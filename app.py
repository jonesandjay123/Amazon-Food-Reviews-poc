import ast
import json
import os
import time

import pandas as pd
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_from_directory
from google import genai  # 新版 SDK 匯入方式
from google.genai import types  # 用於傳入 GenerateContentConfig
from flasgger import Swagger, swag_from
import kagglehub
from kagglehub import KaggleDatasetAdapter
import concurrent.futures

# 載入環境變數
load_dotenv()

app = Flask(__name__)

# 設定 Swagger
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,  # 所有端點
            "model_filter": lambda tag: True,  # 所有模型
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/api/docs/"
}

swagger_template = {
    "info": {
        "title": "電影數據 API",
        "description": "使用電影數據集實現的 RESTful API，支持各種電影查詢功能",
        "version": "1.0.0",
        "contact": {
            "name": "API 支持",
            "email": "support@example.com"
        }
    },
    "tags": [
        {
            "name": "電影列表",
            "description": "獲取電影列表和詳細信息"
        },
        {
            "name": "演員和導演",
            "description": "獲取特定演員或導演的電影"
        },
        {
            "name": "搜索",
            "description": "搜索電影和自然語言查詢"
        },
        {
            "name": "系統",
            "description": "調試和系統信息"
        }
    ]
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)

# 設定 Gemini API 憑證
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 建立 Google GenAI 的 API 客戶端
client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-2.0-flash"

# 定義 Kaggle 數據集信息
KAGGLE_DATASET = "rounakbanik/the-movies-dataset"
MOVIES_FILE = "movies_metadata.csv"
CREDITS_FILE = "credits.csv"
RATINGS_FILE = "ratings_small.csv"

# 數據緩存
cache = {
    "directors_map": None,  # 導演到電影的映射
    "actors_map": None,     # 演員到電影的映射
    "genres_map": None,     # 類型到電影的映射
    "directors_list": None, # 所有導演列表
    "last_load_time": 0     # 上次加載數據的時間戳
}

# 全局數據查詢函數
def get_kaggle_data(file_path, sql_query=None):
    """使用 kagglehub 從 Kaggle 獲取數據"""
    try:
        if sql_query:
            print(f"執行 SQL 查詢: {sql_query}")
            df = kagglehub.load_dataset(
                KaggleDatasetAdapter.PANDAS,
                KAGGLE_DATASET,
                file_path,
                sql_query=sql_query
            )
        else:
            df = kagglehub.load_dataset(
                KaggleDatasetAdapter.PANDAS,
                KAGGLE_DATASET,
                file_path
            )
        return df
    except Exception as e:
        print(f"獲取 Kaggle 數據時發生錯誤: {e}")
        return pd.DataFrame()

def parse_json_field(json_str, key=None):
    """解析 JSON 格式的字段"""
    try:
        if isinstance(json_str, str):
            data = ast.literal_eval(json_str)
            if key and isinstance(data, list):
                return [item[key] for item in data if key in item]
            return data
        return json_str
    except (ValueError, SyntaxError, TypeError) as e:
        # 記錄錯誤但回傳空列表以避免中斷處理
        print(f"解析 JSON 字段時出錯: {e}")
        return []

def load_data():
    """載入並預處理電影數據，建立查詢優化的緩存"""
    global cache
    # 檢查是否需要刷新數據緩存（每小時刷新一次）
    current_time = time.time()
    if cache["last_load_time"] > 0 and (current_time - cache["last_load_time"]) < 3600:
        return
    print("開始加載數據並建立緩存...")
    try:
        # 使用並行處理加速數據加載
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # 獲取導演數據
            future_directors = executor.submit(
                get_kaggle_data,
                CREDITS_FILE,
                "SELECT id, crew FROM credits"
            )
            # 獲取電影元數據
            future_movies = executor.submit(
                get_kaggle_data,
                MOVIES_FILE,
                "SELECT id, title, release_date, genres, vote_average, overview, revenue, budget, runtime FROM movies_metadata"
            )
            # 獲取演員數據
            future_cast = executor.submit(
                get_kaggle_data,
                CREDITS_FILE,
                "SELECT id, cast FROM credits"
            )
            # 等待所有數據獲取完成
            credits_df_crew = future_directors.result()
            movies_df = future_movies.result()
            credits_df_cast = future_cast.result()
        # 數據預處理
        if not movies_df.empty:
            # 轉換 ID 為整數以便匹配
            movies_df["id"] = pd.to_numeric(movies_df["id"], errors="coerce")
            # 解析 genres 欄位
            movies_df["genres"] = movies_df["genres"].apply(
                lambda x: parse_json_field(x, "name") if pd.notnull(x) else []
            )
        if not credits_df_crew.empty:
            # 轉換 movie_id 為整數以便匹配
            credits_df_crew["id"] = pd.to_numeric(credits_df_crew["id"], errors="coerce")
            # 解析 crew 欄位
            credits_df_crew["crew"] = credits_df_crew["crew"].apply(
                lambda x: parse_json_field(x) if pd.notnull(x) else []
            )
            # 從 crew 中提取導演信息
            credits_df_crew["directors"] = credits_df_crew["crew"].apply(
                lambda crew: [
                    member["name"] for member in crew if isinstance(crew, list) and member.get("job") == "Director"
                ]
            )
        if not credits_df_cast.empty:
            # 轉換 movie_id 為整數以便匹配
            credits_df_cast["id"] = pd.to_numeric(credits_df_cast["id"], errors="coerce")
            # 解析 cast 欄位
            credits_df_cast["cast"] = credits_df_cast["cast"].apply(
                lambda x: parse_json_field(x) if pd.notnull(x) else []
            )
        # 建立優化查詢的緩存映射
        # 1. 導演到電影的映射
        directors_map = {}
        for _, row in credits_df_crew.iterrows():
            movie_id = row["id"]
            directors = row["directors"]
            if pd.isna(movie_id) or not isinstance(directors, list):
                continue
            movie = movies_df[movies_df["id"] == movie_id]
            if movie.empty:
                continue
            movie_data = movie.iloc[0]
            movie_info = {
                "id": int(movie_id) if pd.notnull(movie_id) else None,
                "title": movie_data["title"],
                "release_date": movie_data["release_date"],
                "genres": movie_data["genres"],
                "vote_average": movie_data["vote_average"],
                "revenue": movie_data["revenue"],
            }
            for director in directors:
                if director not in directors_map:
                    directors_map[director] = []
                directors_map[director].append(movie_info)
        # 2. 演員到電影的映射
        actors_map = {}
        for _, row in credits_df_cast.iterrows():
            movie_id = row["id"]
            cast = row["cast"]
            if pd.isna(movie_id) or not isinstance(cast, list):
                continue
            movie = movies_df[movies_df["id"] == movie_id]
            if movie.empty:
                continue
            movie_data = movie.iloc[0]
            for actor in cast[:10]:  # 只取前10個演員
                if not isinstance(actor, dict) or "name" not in actor:
                    continue
                actor_name = actor["name"]
                character = actor.get("character", "Unknown")
                movie_info = {
                    "id": int(movie_id) if pd.notnull(movie_id) else None,
                    "title": movie_data["title"],
                    "release_date": movie_data["release_date"],
                    "character": character,
                    "popularity": movie_data.get("popularity", None),
                }
                if actor_name not in actors_map:
                    actors_map[actor_name] = []
                actors_map[actor_name].append(movie_info)
        # 3. 類型到電影的映射
        genres_map = {}
        for _, movie in movies_df.iterrows():
            genres = movie["genres"]
            if not isinstance(genres, list):
                continue
            for genre in genres:
                if genre not in genres_map:
                    genres_map[genre] = []
                genres_map[genre].append({
                    "id": int(movie["id"]) if pd.notnull(movie["id"]) else None,
                    "title": movie["title"],
                    "release_date": movie["release_date"],
                    "vote_average": movie["vote_average"],
                    "genres": genres,
                })
        # 4. 所有導演列表
        directors_list = sorted(list(directors_map.keys()))
        # 更新緩存
        cache["directors_map"] = directors_map
        cache["actors_map"] = actors_map
        cache["genres_map"] = genres_map
        cache["directors_list"] = directors_list
        cache["last_load_time"] = current_time
        print("數據加載和緩存建立完成")
    except Exception as e:
        print(f"數據緩存建立錯誤: {e}")

@app.route("/", methods=["GET"])
def index():
    """提供聊天界面的 HTML 頁面"""
    return render_template("index.html")

@app.route("/api", methods=["GET"])
def api_home():
    """提供 API 文檔和測試界面的入口頁面"""
    return render_template("api.html")

@app.route("/api/movies", methods=["GET"])
@swag_from({
    "tags": ["電影列表"],
    "summary": "獲取電影列表",
    "description": "獲取電影列表，支持多種過濾條件",
    "parameters": [
        {
            "name": "page",
            "in": "query",
            "type": "integer",
            "default": 1,
            "description": "頁碼"
        },
        {
            "name": "limit",
            "in": "query",
            "type": "integer",
            "default": 20,
            "description": "每頁結果數量"
        },
        {
            "name": "year",
            "in": "query",
            "type": "integer",
            "description": "發行年份"
        },
        {
            "name": "genre",
            "in": "query",
            "type": "string",
            "description": "電影類型"
        },
        {
            "name": "min_rating",
            "in": "query",
            "type": "number",
            "format": "float",
            "description": "最低評分"
        },
        {
            "name": "min_revenue",
            "in": "query",
            "type": "number",
            "format": "float",
            "description": "最低票房"
        }
    ],
    "responses": {
        "200": {
            "description": "成功獲取電影列表"
        }
    }
})
def get_movies():
    """獲取電影列表，支持多種過濾條件"""
    load_data()

    # 獲取查詢參數
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 20, type=int)
    year = request.args.get("year", type=int)
    genre = request.args.get("genre")
    min_rating = request.args.get("min_rating", type=float)
    min_revenue = request.args.get("min_revenue", type=float)

    # 構建 SQL 查詢
    sql_query = "SELECT id, title, release_date, genres, vote_average, revenue, runtime FROM movies_metadata WHERE 1=1"
    if year:
        sql_query += f" AND release_date LIKE '%{year}%'"
    if min_revenue:
        sql_query += f" AND CAST(revenue AS FLOAT) >= {min_revenue}"
    if min_rating:
        sql_query += f" AND CAST(vote_average AS FLOAT) >= {min_rating}"
    # 添加排序和分頁
    sql_query += " ORDER BY popularity DESC"
    sql_query += f" LIMIT {limit} OFFSET {(page - 1) * limit}"
    # 執行查詢
    movies_df = get_kaggle_data(MOVIES_FILE, sql_query)
    # 針對 genre 進行進一步過濾（這個需要在 Python 中處理，因為 genres 是 JSON 結構）
    if genre and not movies_df.empty:
        # 解析 genres 欄位
        movies_df["genres"] = movies_df["genres"].apply(
            lambda x: parse_json_field(x, "name") if pd.notnull(x) else []
        )
        # 過濾包含特定類型的電影
        movies_df = movies_df[
            movies_df["genres"].apply(
                lambda x: genre in x if isinstance(x, list) else False
            )
        ]
    # 格式化結果
    movies_list = []
    for _, movie in movies_df.iterrows():
        movie_data = {
            "id": int(movie["id"]) if pd.notnull(movie["id"]) else None,
            "title": movie["title"],
            "release_date": movie["release_date"],
            "genres": movie["genres"] if "genres" in movie and isinstance(movie["genres"], list) else [],
            "vote_average": movie["vote_average"],
            "revenue": movie["revenue"],
            "runtime": movie["runtime"],
        }
        movies_list.append(movie_data)

    total = len(movies_list)  # 注意：這不是總記錄數，只是當前頁的記錄數

    return jsonify(
        {
            "page": page,
            "total_results": total,
            "total_pages": (total + limit - 1) // limit if total > 0 else 1,
            "results": movies_list,
        }
    )

@app.route("/api/movies/<int:movie_id>", methods=["GET"])
@swag_from({
    "tags": ["電影列表"],
    "summary": "獲取特定電影的詳細信息",
    "description": "根據電影 ID 獲取詳細信息",
    "parameters": [
        {
            "name": "movie_id",
            "in": "path",
            "type": "integer",
            "required": True,
            "description": "電影 ID"
        }
    ],
    "responses": {
        "200": {
            "description": "成功獲取電影詳情"
        },
        "404": {
            "description": "找不到該電影"
        }
    }
})
def get_movie_details(movie_id):
    """獲取特定電影的詳細信息"""
    # 直接用 SQL 查詢獲取電影詳情
    sql_query = f"SELECT * FROM movies_metadata WHERE id = {movie_id}"
    movie_df = get_kaggle_data(MOVIES_FILE, sql_query)
    if movie_df.empty:
        return jsonify({"error": "找不到該電影"}), 404
    movie = movie_df.iloc[0]
    # 解析 genres 欄位
    genres = parse_json_field(movie["genres"], "name") if pd.notnull(movie["genres"]) else []
    # 獲取演員和導演信息
    cast_sql = f"SELECT cast, crew FROM credits WHERE id = {movie_id}"
    cast_crew_df = get_kaggle_data(CREDITS_FILE, cast_sql)
    cast = []
    directors = []
    if not cast_crew_df.empty:
        cast_row = cast_crew_df.iloc[0]
        # 解析 cast 資料
        cast_data = parse_json_field(cast_row["cast"]) if pd.notnull(cast_row["cast"]) else []
        if isinstance(cast_data, list):
            cast = [
                {
                    "id": actor.get("id"),
                    "name": actor.get("name"),
                    "character": actor.get("character"),
                }
                for actor in cast_data[:10] if isinstance(actor, dict)
            ]
        # 解析 crew 資料並提取導演
        crew_data = parse_json_field(cast_row["crew"]) if pd.notnull(cast_row["crew"]) else []
        if isinstance(crew_data, list):
            directors = [
                member.get("name") for member in crew_data
                if isinstance(member, dict) and member.get("job") == "Director"
            ]
    # 獲取評分數據
    rating_sql = f"SELECT rating FROM ratings_small WHERE movieId = {movie_id}"
    ratings_df = get_kaggle_data(RATINGS_FILE, rating_sql)
    rating_info = None
    if not ratings_df.empty:
        rating_info = {
            "average_rating": ratings_df["rating"].mean(),
            "number_of_ratings": len(ratings_df),
        }
    # 構建完整回應
    movie_details = {
        "id": int(movie["id"]) if pd.notnull(movie["id"]) else None,
        "title": movie["title"],
        "original_title": movie["original_title"] if "original_title" in movie else movie["title"],
        "release_date": movie["release_date"],
        "genres": genres,
        "overview": movie["overview"],
        "vote_average": movie["vote_average"],
        "vote_count": movie["vote_count"] if "vote_count" in movie else None,
        "revenue": movie["revenue"],
        "budget": movie["budget"] if "budget" in movie else None,
        "runtime": movie["runtime"],
        "cast": cast,
        "directors": directors,
        "rating_info": rating_info,
    }
    return jsonify(movie_details)

@app.route("/api/actor/<string:actor_name>", methods=["GET"])
@swag_from({
    "tags": ["演員和導演"],
    "summary": "獲取特定演員參演的所有電影",
    "description": "根據演員名稱獲取其參演的所有電影",
    "parameters": [
        {
            "name": "actor_name",
            "in": "path",
            "type": "string",
            "required": True,
            "description": "演員名稱"
        }
    ],
    "responses": {
        "200": {
            "description": "成功獲取演員電影列表"
        },
        "500": {
            "description": "演員數據不可用"
        }
    }
})
def get_actor_movies(actor_name):
    """獲取特定演員參演的所有電影"""
    load_data()
    if not cache["actors_map"]:
        return jsonify({"error": "演員數據不可用"}), 500
    # 查找演員的電影（不區分大小寫）
    actor_name_lower = actor_name.lower()
    # 嘗試精確匹配
    exact_matches = [name for name in cache["actors_map"].keys()
                     if name.lower() == actor_name_lower]
    if exact_matches:
        actor_movies = cache["actors_map"][exact_matches[0]]
    else:
        # 嘗試模糊匹配
        potential_matches = [name for name in cache["actors_map"].keys()
                            if actor_name_lower in name.lower()]
        if not potential_matches:
            return jsonify({"actor": actor_name, "movie_count": 0, "movies": []}), 200
        actor_movies = cache["actors_map"][potential_matches[0]]
    # 按受歡迎程度排序
    actor_movies.sort(
        key=lambda x: x.get("popularity", 0) if x.get("popularity") is not None else 0,
        reverse=True,
    )
    return jsonify(
        {"actor": actor_name, "movie_count": len(actor_movies), "movies": actor_movies}
    )

@app.route("/api/director/<string:director_name>", methods=["GET"])
@swag_from({
    "tags": ["演員和導演"],
    "summary": "獲取特定導演執導的所有電影",
    "description": "根據導演名稱獲取其執導的所有電影",
    "parameters": [
        {
            "name": "director_name",
            "in": "path",
            "type": "string",
            "required": True,
            "description": "導演名稱"
        }
    ],
    "responses": {
        "200": {
            "description": "成功獲取導演電影列表"
        },
        "500": {
            "description": "導演數據不可用"
        }
    }
})
def get_director_movies(director_name):
    """獲取特定導演執導的所有電影"""
    load_data()
    if not cache["directors_map"]:
        return jsonify({"error": "導演數據不可用"}), 500
    # 查找導演的電影（不區分大小寫）
    director_name_lower = director_name.lower()
    # 嘗試精確匹配
    exact_matches = [name for name in cache["directors_map"].keys()
                     if name.lower() == director_name_lower]
    if exact_matches:
        director_movies = cache["directors_map"][exact_matches[0]]
    else:
        # 嘗試模糊匹配
        potential_matches = [name for name in cache["directors_map"].keys()
                            if director_name_lower in name.lower()]
        if not potential_matches:
            return jsonify({"director": director_name, "movie_count": 0, "movies": []}), 200
        director_movies = cache["directors_map"][potential_matches[0]]
    # 按發行日期排序
    director_movies.sort(key=lambda x: x.get("release_date", ""), reverse=True)
    return jsonify(
        {
            "director": director_name,
            "movie_count": len(director_movies),
            "movies": director_movies,
        }
    )

@app.route("/api/search", methods=["GET"])
@swag_from({
    "tags": ["搜索"],
    "summary": "搜索電影",
    "description": "使用關鍵字搜索電影",
    "parameters": [
        {
            "name": "q",
            "in": "query",
            "type": "string",
            "required": True,
            "description": "搜索查詢"
        }
    ],
    "responses": {
        "200": {
            "description": "成功獲取搜索結果"
        },
        "400": {
            "description": "搜索查詢不能為空"
        }
    }
})
def search_movies():
    """搜索電影（基本文本搜索）"""
    query = request.args.get("q", "")
    if not query:
        return jsonify({"error": "必須提供搜索查詢"}), 400

    # 使用SQL查詢進行搜索
    sql_query = f"""
    SELECT id, title, release_date, genres, overview
    FROM movies_metadata
    WHERE title LIKE '%{query}%' OR overview LIKE '%{query}%'
    LIMIT 20
    """
    matched_movies = get_kaggle_data(MOVIES_FILE, sql_query)
    # 解析genres列
    matched_movies["genres"] = matched_movies["genres"].apply(
        lambda x: parse_json_field(x, "name") if pd.notnull(x) else []
    )

    # 格式化結果
    results = []
    for _, movie in matched_movies.iterrows():
        results.append(
            {
                "id": int(movie["id"]) if pd.notnull(movie["id"]) else None,
                "title": movie["title"],
                "release_date": movie["release_date"],
                "overview": movie["overview"],
                "genres": movie["genres"],
            }
        )

    return jsonify({"query": query, "results_count": len(results), "results": results})

@app.route("/api/query", methods=["POST"])
@swag_from({
    "tags": ["搜索"],
    "summary": "自然語言查詢電影",
    "description": "使用自然語言查詢電影，由 Gemini API 解析",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "自然語言查詢"
                    }
                },
                "required": ["query"]
            }
        }
    ],
    "responses": {
        "200": {
            "description": "成功獲取查詢結果"
        },
        "400": {
            "description": "查詢不能為空"
        },
        "500": {
            "description": "處理查詢時發生錯誤"
        }
    }
})
def query_movies():
    """使用自然語言查詢電影（使用 Gemini API）"""
    load_data()

    data = request.get_json()
    if not data or "query" not in data:
        return jsonify({"error": "必須提供自然語言查詢"}), 400

    user_query = data["query"]

    # 使用 Gemini API 解析查詢
    prompt = f"""
    根據以下自然語言查詢，提取有關電影的搜索關鍵信息。
    請以JSON格式回傳以下欄位（如果有相關信息）：
    - actor: 演員名稱（如有中文名，請同時提供英文名）
    - director: 導演名稱（如有中文名，請同時提供英文名）
    - year: 發行年份
    - genre: 電影類型
    - min_rating: 最低評分
    - keyword: 標題或概述中的關鍵字

    例如：如果查詢是"找克里斯多夫·諾蘭執導的電影"，應返回：{{"director": "Christopher Nolan"}}

    查詢: {user_query}
    """

    try:
        print(f"正在處理查詢: {user_query}")
        gemini_response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        print(f"Gemini API 原始回應: {gemini_response.text}")
        # 解析 Gemini 回應
        try:
            structured_query = json.loads(gemini_response.text)
            print(f"結構化查詢內容: {structured_query}")
        except json.JSONDecodeError as json_err:
            print(f"JSON解析錯誤: {json_err}. 原始回應: {gemini_response.text}")
            return jsonify({"error": f"無法解析模型回應為JSON: {str(json_err)}"}), 500

        # 根據結構化查詢搜索電影
        results = []

        # 如果查詢指定了演員
        if "actor" in structured_query and structured_query["actor"]:
            actor_response = get_actor_movies(structured_query["actor"])
            actor_data = json.loads(actor_response.data)
            if "movies" in actor_data:
                # 標記結果來源
                for movie in actor_data["movies"]:
                    movie["result_type"] = "actor_search"
                results.extend(actor_data["movies"])

        # 如果查詢指定了導演
        if "director" in structured_query and structured_query["director"]:
            print(f"嘗試搜索導演: {structured_query['director']}")
            director_response = get_director_movies(structured_query["director"])
            director_data = json.loads(director_response.data)
            print(f"導演搜索結果: {director_data}")
            if "movies" in director_data:
                # 標記結果來源
                for movie in director_data["movies"]:
                    movie["result_type"] = "director_search"
                results.extend(director_data["movies"])

        # 如果查詢包含其他條件，搜索電影
        if (
            ("year" in structured_query and structured_query["year"])
            or ("genre" in structured_query and structured_query["genre"])
            or ("min_rating" in structured_query and structured_query["min_rating"])
            or ("keyword" in structured_query and structured_query["keyword"])
        ):
            # 構建 API 參數
            params = {}
            if "year" in structured_query and structured_query["year"]:
                params["year"] = structured_query["year"]
            if "genre" in structured_query and structured_query["genre"]:
                params["genre"] = structured_query["genre"]
            if "min_rating" in structured_query and structured_query["min_rating"]:
                params["min_rating"] = structured_query["min_rating"]

            # 如果有關鍵字，使用搜索 API
            if "keyword" in structured_query and structured_query["keyword"]:
                search_response = search_movies()
                search_data = json.loads(search_response.data)
                if "results" in search_data:
                    # 標記結果來源
                    for movie in search_data["results"]:
                        movie["result_type"] = "keyword_search"
                    results.extend(search_data["results"])
            else:
                # 使用電影 API 進行過濾
                movies_response = get_movies()
                movies_data = json.loads(movies_response.data)
                if "results" in movies_data:
                    # 標記結果來源
                    for movie in movies_data["results"]:
                        movie["result_type"] = "filter_search"
                    results.extend(movies_data["results"])

        # 去除重複結果
        unique_movies = {}
        for movie in results:
            if "id" in movie and movie["id"] not in unique_movies:
                unique_movies[movie["id"]] = movie

        unique_results = list(unique_movies.values())

        return jsonify(
            {
                "query": user_query,
                "interpreted_as": structured_query,
                "results_count": len(unique_results),
                "results": unique_results,
            }
        )

    except Exception as e:
        print(f"查詢處理錯誤: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/debug", methods=["GET"])
@swag_from({
    "tags": ["系統"],
    "summary": "調試系統狀態",
    "description": "獲取系統數據加載狀態信息",
    "responses": {
        "200": {
            "description": "成功獲取系統狀態"
        }
    }
})
def debug():
    """調試端點，用於檢視數據加載狀態"""
    load_data()

    return jsonify(
        {
            "data_loaded": cache["last_load_time"] > 0,
            "cache_status": {
                "directors_map": bool(cache["directors_map"]),
                "actors_map": bool(cache["actors_map"]),
                "genres_map": bool(cache["genres_map"]),
                "directors_list": bool(cache["directors_list"]),
                "last_updated": cache["last_load_time"],
            },
            "kaggle_dataset": KAGGLE_DATASET,
            "files": {
                "movies": MOVIES_FILE,
                "credits": CREDITS_FILE,
                "ratings": RATINGS_FILE,
            },
        }
    )

@app.route("/api/debug/directors", methods=["GET"])
@swag_from({
    "tags": ["系統"],
    "summary": "獲取所有導演列表",
    "description": "用於調試：列出數據集中的所有導演名稱",
    "parameters": [
        {
            "name": "limit",
            "in": "query",
            "type": "integer",
            "default": 100,
            "description": "要返回的導演數量限制"
        },
        {
            "name": "search",
            "in": "query",
            "type": "string",
            "description": "按名稱搜索導演（不區分大小寫）"
        }
    ],
    "responses": {
        "200": {
            "description": "成功獲取導演列表"
        }
    }
})
def list_directors():
    """調試端點，列出所有導演"""
    load_data()
    if not cache["directors_list"]:
        return jsonify({"error": "導演數據不可用"}), 500
    directors_list = cache["directors_list"]
    # 應用搜索過濾
    search_term = request.args.get("search", "").lower()
    if search_term:
        directors_list = [d for d in directors_list if search_term in d.lower()]
    # 應用限制
    limit = request.args.get("limit", 100, type=int)
    directors_list = directors_list[:limit]
    # 返回結果
    return jsonify({
        "total_directors": len(cache["directors_list"]),
        "returned_count": len(directors_list),
        "search_term": search_term if search_term else None,
        "directors": directors_list
    })

@app.route('/favicon.ico')
def favicon():
    """提供網站圖標"""
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == "__main__":
    if not GEMINI_API_KEY:
        print("錯誤：未設置 GEMINI_API_KEY 環境變數")
        exit(1)

    # 使用環境變數來控制 debug 模式，預設為 False（安全模式）
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    app.run(debug=debug_mode)
