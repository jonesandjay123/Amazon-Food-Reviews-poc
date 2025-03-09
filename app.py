import ast
import json
import os

import pandas as pd
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from google import genai  # 新版 SDK 匯入方式
from google.genai import types  # 用來傳入 GenerateContentConfig
from flasgger import Swagger, swag_from

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

# 定義數據檔案路徑
DATA_PATH = "./data"
MOVIES_FILE = os.path.join(DATA_PATH, "movies_metadata.csv")
CREDITS_FILE = os.path.join(DATA_PATH, "credits.csv")
RATINGS_FILE = os.path.join(DATA_PATH, "ratings_small.csv")

# 全局數據存儲
movies_df = None
credits_df = None
ratings_df = None
movies_processed = False


def load_data():
    """載入並處理電影數據"""
    global movies_df, credits_df, ratings_df, movies_processed

    if movies_processed:
        return

    try:
        # 確保數據目錄存在
        if not os.path.exists(DATA_PATH):
            os.makedirs(DATA_PATH)

        # 載入數據文件
        if os.path.exists(MOVIES_FILE):
            movies_df = pd.read_csv(MOVIES_FILE, low_memory=False)
        else:
            print(f"警告：找不到電影元數據文件: {MOVIES_FILE}")
            movies_df = pd.DataFrame()

        if os.path.exists(CREDITS_FILE):
            credits_df = pd.read_csv(CREDITS_FILE)
        else:
            print(f"警告：找不到演員和製作人員文件: {CREDITS_FILE}")
            credits_df = pd.DataFrame()

        if os.path.exists(RATINGS_FILE):
            ratings_df = pd.read_csv(RATINGS_FILE)
        else:
            print(f"警告：找不到評分文件: {RATINGS_FILE}")
            ratings_df = pd.DataFrame()

        # 數據預處理
        if not movies_df.empty:
            # 轉換 ID 為整數以便匹配
            movies_df["id"] = pd.to_numeric(movies_df["id"], errors="coerce")

            # 解析 genres 欄位
            movies_df["genres"] = movies_df["genres"].apply(
                lambda x: parse_json_field(x, "name") if pd.notnull(x) else []
            )

        if not credits_df.empty:
            # 轉換 movie_id 為整數以便匹配
            credits_df["id"] = pd.to_numeric(credits_df["id"], errors="coerce")

            # 解析 cast 和 crew 欄位
            credits_df["cast"] = credits_df["cast"].apply(
                lambda x: parse_json_field(x) if pd.notnull(x) else []
            )
            credits_df["crew"] = credits_df["crew"].apply(
                lambda x: parse_json_field(x) if pd.notnull(x) else []
            )

            # 從 crew 中提取導演信息
            credits_df["directors"] = credits_df["crew"].apply(
                lambda crew: [
                    member["name"] for member in crew if member.get("job") == "Director"
                ]
            )

        if not ratings_df.empty:
            # 確保 ID 欄位為整數
            ratings_df["movieId"] = ratings_df["movieId"].astype(int)

        movies_processed = True
        print("電影數據載入和預處理完成")

    except Exception as e:
        print(f"數據載入錯誤: {e}")


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

    # 篩選電影
    filtered_movies = movies_df.copy()

    if year:
        filtered_movies = filtered_movies[
            filtered_movies["release_date"].str.contains(str(year), na=False)
        ]

    if genre:
        filtered_movies = filtered_movies[
            filtered_movies["genres"].apply(
                lambda x: genre in x if isinstance(x, list) else False
            )
        ]

    if min_revenue:
        filtered_movies = filtered_movies[
            pd.to_numeric(filtered_movies["revenue"], errors="coerce") >= min_revenue
        ]

    if min_rating and not ratings_df.empty:
        # 計算每部電影的平均評分
        avg_ratings = ratings_df.groupby("movieId")["rating"].mean().reset_index()
        avg_ratings.rename(columns={"movieId": "id"}, inplace=True)

        # 合併評分數據
        filtered_movies = filtered_movies.merge(avg_ratings, on="id", how="left")
        filtered_movies = filtered_movies[filtered_movies["rating"] >= min_rating]

    # 分頁
    total = len(filtered_movies)
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit

    paginated_movies = filtered_movies.iloc[start_idx:end_idx]

    # 格式化結果
    movies_list = []
    for _, movie in paginated_movies.iterrows():
        movie_data = {
            "id": int(movie["id"]) if pd.notnull(movie["id"]) else None,
            "title": movie["title"],
            "release_date": movie["release_date"],
            "genres": movie["genres"],
            "overview": movie["overview"],
            "vote_average": movie["vote_average"],
            "revenue": movie["revenue"],
            "runtime": movie["runtime"],
        }
        movies_list.append(movie_data)

    return jsonify(
        {
            "page": page,
            "total_results": total,
            "total_pages": (total + limit - 1) // limit,
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
    load_data()

    # 查找電影
    movie = movies_df[movies_df["id"] == movie_id]
    if movie.empty:
        return jsonify({"error": "找不到該電影"}), 404

    movie = movie.iloc[0]

    # 獲取演員和導演信息
    cast_crew = credits_df[credits_df["id"] == movie_id]
    cast = []
    directors = []

    if not cast_crew.empty:
        cast_data = cast_crew.iloc[0]["cast"]
        if isinstance(cast_data, list):
            cast = [
                {
                    "id": actor.get("id"),
                    "name": actor.get("name"),
                    "character": actor.get("character"),
                }
                for actor in cast_data[:10]
            ]  # 只取前10個演員

        directors_data = cast_crew.iloc[0]["directors"]
        if isinstance(directors_data, list):
            directors = directors_data

    # 獲取評分信息
    rating_info = None
    if not ratings_df.empty:
        movie_ratings = ratings_df[ratings_df["movieId"] == movie_id]
        if not movie_ratings.empty:
            rating_info = {
                "average_rating": movie_ratings["rating"].mean(),
                "number_of_ratings": len(movie_ratings),
            }

    # 構建完整回應
    movie_details = {
        "id": int(movie["id"]) if pd.notnull(movie["id"]) else None,
        "title": movie["title"],
        "original_title": movie["original_title"],
        "release_date": movie["release_date"],
        "genres": movie["genres"],
        "overview": movie["overview"],
        "vote_average": movie["vote_average"],
        "vote_count": movie["vote_count"],
        "revenue": movie["revenue"],
        "budget": movie["budget"],
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

    if credits_df.empty:
        return jsonify({"error": "演員數據不可用"}), 500

    # 查找演員參演的電影
    actor_name_lower = actor_name.lower()
    actor_movies = []

    for _, row in credits_df.iterrows():
        cast = row["cast"]
        if isinstance(cast, list):
            for actor in cast:
                if (
                    isinstance(actor, dict)
                    and "name" in actor
                    and actor["name"].lower() == actor_name_lower
                ):
                    movie_id = row["id"]
                    movie = movies_df[movies_df["id"] == movie_id]
                    if not movie.empty:
                        movie_data = movie.iloc[0]
                        actor_movies.append(
                            {
                                "id": int(movie_id) if pd.notnull(movie_id) else None,
                                "title": movie_data["title"],
                                "release_date": movie_data["release_date"],
                                "character": actor.get("character", "Unknown"),
                                "popularity": (
                                    movie_data["popularity"]
                                    if "popularity" in movie_data
                                    else None
                                ),
                            }
                        )

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

    if credits_df.empty:
        return jsonify({"error": "導演數據不可用"}), 500

    # 查找導演的電影
    director_name_lower = director_name.lower()
    director_movies = []

    for _, row in credits_df.iterrows():
        directors = row["directors"]
        if isinstance(directors, list):
            for director in directors:
                if (
                    isinstance(director, str)
                    and director.lower() == director_name_lower
                ):
                    movie_id = row["id"]
                    movie = movies_df[movies_df["id"] == movie_id]
                    if not movie.empty:
                        movie_data = movie.iloc[0]
                        director_movies.append(
                            {
                                "id": int(movie_id) if pd.notnull(movie_id) else None,
                                "title": movie_data["title"],
                                "release_date": movie_data["release_date"],
                                "genres": movie_data["genres"],
                                "vote_average": movie_data["vote_average"],
                                "revenue": movie_data["revenue"],
                            }
                        )

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
    load_data()

    query = request.args.get("q", "")
    if not query:
        return jsonify({"error": "必須提供搜索查詢"}), 400

    # 在標題和概述中搜索
    matched_movies = movies_df[
        movies_df["title"].str.contains(query, case=False, na=False)
        | movies_df["overview"].str.contains(query, case=False, na=False)
    ]

    # 格式化結果
    results = []
    for _, movie in matched_movies.head(20).iterrows():
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
    - actor: 演員名稱
    - director: 導演名稱
    - year: 發行年份
    - genre: 電影類型
    - min_rating: 最低評分
    - keyword: 標題或概述中的關鍵字

    查詢: {user_query}
    """

    try:
        gemini_response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )

        # 解析 Gemini 回應
        structured_query = json.loads(gemini_response.text)

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
            director_response = get_director_movies(structured_query["director"])
            director_data = json.loads(director_response.data)
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
            "movies_loaded": not movies_df.empty if movies_df is not None else False,
            "credits_loaded": not credits_df.empty if credits_df is not None else False,
            "ratings_loaded": not ratings_df.empty if ratings_df is not None else False,
            "movies_count": len(movies_df) if movies_df is not None else 0,
            "credits_count": len(credits_df) if credits_df is not None else 0,
            "ratings_count": len(ratings_df) if ratings_df is not None else 0,
            "data_path": DATA_PATH,
            "files_exist": {
                "movies": os.path.exists(MOVIES_FILE),
                "credits": os.path.exists(CREDITS_FILE),
                "ratings": os.path.exists(RATINGS_FILE),
            },
        }
    )


if __name__ == "__main__":
    if not GEMINI_API_KEY:
        print("錯誤：未設置 GEMINI_API_KEY 環境變數")
        exit(1)

    # 使用環境變數來控制 debug 模式，預設為 False（安全模式）
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    app.run(debug=debug_mode)
