from flask import Flask, request, jsonify, render_template
import os
import requests
import json
from dotenv import load_dotenv
from google import genai  # 新版 SDK 匯入方式
from google.genai import types  # 用來傳入 GenerateContentConfig

load_dotenv()

app = Flask(__name__)

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 建立 Google GenAI 的 API 客戶端
client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_NAME = 'gemini-2.0-flash'

latest_query = ""
latest_places_data = []

def get_place_details(place_id):
    """取得地點詳細資訊"""
    url = f"https://places.googleapis.com/v1/places/{place_id}?fields=displayName,formattedAddress,rating,websiteUri,regularOpeningHours&key={GOOGLE_PLACES_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None

@app.route('/', methods=['GET'])
def index():
    """提供聊天界面的 HTML 頁面"""
    return render_template('index.html')

@app.route('/query', methods=['POST'])
def query():
    global latest_query, latest_places_data
    try:
        data = request.get_json()
        user_query = data.get('query', '')
        if not user_query:
            return jsonify({"error": "查詢內容不能為空"}), 400
        latest_query = user_query

        # 呼叫 Gemini API 生成結構化查詢，強制回傳 JSON 格式
        prompt = f"""
        根據以下自然語言查詢，提取關鍵信息以便進行 Google Places API 查詢。
        請僅回傳 JSON，且僅包含以下鍵：
            location（地點）,
            keyword（關鍵字）,
            radius（半徑，以米為單位）,
            limit（結果數量限制）。
        不要額外輸出其他文字。
        查詢: {user_query}
        """
        gemini_response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        print("=== Gemini API raw output ===")
        print(gemini_response.text)
        try:
            structured_query = json.loads(gemini_response.text)
        except Exception as e:
            print("Error parsing Gemini response as JSON:", e)
            return jsonify({"error": "Gemini API 回傳資料格式錯誤"}), 500

        # 如果 Gemini 回傳的 limit 為 null，則預設為 5
        limit = structured_query.get('limit') if structured_query.get('limit') is not None else 5
        keyword = structured_query.get('keyword', '')
        location_str = structured_query.get('location', '')
        
        # 建立 Places API 的文字查詢字串
        if location_str:
            text_query = f"{keyword} in {location_str}"
        else:
            text_query = keyword

        print("=== Debug Gemini parsed data ===")
        print("text_query:", text_query)
        print("radius:", structured_query.get('radius'))
        print("limit:", limit)

        # 根據新版文件，Places API 只需要傳入 textQuery
        payload = {
            "textQuery": text_query
        }
        print("=== Debug Places API payload ===")
        print(json.dumps(payload, indent=2))

        # HTTP 標頭中傳入 API 金鑰與欄位遮罩
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.websiteUri,places.regularOpeningHours"
        }
        print("=== Debug Places API headers ===")
        print(headers)

        places_url = "https://places.googleapis.com/v1/places:searchText"
        places_response = requests.post(places_url, headers=headers, json=payload)

        print("=== Places API raw response ===")
        print("Status code:", places_response.status_code)
        print("Response text:", places_response.text)

        if places_response.status_code == 200:
            try:
                places_data = places_response.json()
                # 儲存結果到全局變數，確保有 'places' 欄位
                if 'places' in places_data:
                    latest_places_data = places_data['places'][:limit]
                    print(f"成功儲存 {len(latest_places_data)} 筆地點資料")
                else:
                    latest_places_data = []
                    print("Places API 回傳成功但無 'places' 欄位")
            except Exception as e:
                print("Error parsing Places API response as JSON:", e)
                return jsonify({"error": "Places API 回傳資料格式錯誤"}), 500
            
            return jsonify({
                "query": user_query,
                "status": "success",
                "message": "查詢成功，請使用 /results 端點查看整理後的結果"
            })
        else:
            return jsonify({"error": f"Places API 請求失敗：{places_response.status_code}"}), 500
    except Exception as e:
        print("Overall error in /query:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/results', methods=['GET'])
def results():
    global latest_query, latest_places_data
    try:
        if not latest_places_data:
            return jsonify({"error": "尚未有查詢結果，請先使用 /query 端點進行查詢"}), 400
        
        formatted_results = []
        for place in latest_places_data:
            # 直接從 place 數據中提取信息，不再調用 get_place_details
            name = place.get('displayName', {}).get('text', 'N/A')
            address = place.get('formattedAddress', 'N/A')
            rating = place.get('rating', 'N/A')
            website = place.get('websiteUri', 'N/A')
            
            # 處理營業時間
            opening_hours = 'N/A'
            if 'regularOpeningHours' in place and 'weekdayDescriptions' in place['regularOpeningHours']:
                opening_hours = ', '.join(place['regularOpeningHours']['weekdayDescriptions'])
            
            formatted_results.append({
                "name": name,
                "address": address,
                "rating": rating,
                "website": website,
                "opening_hours": opening_hours
            })
        
        return jsonify({
            "query": latest_query,
            "results": formatted_results
        })
    except Exception as e:
        print("Overall error in /results:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/debug', methods=['GET'])
def debug():
    """調試端點，用於檢視當前存儲的資料"""
    global latest_query, latest_places_data
    return jsonify({
        "latest_query": latest_query,
        "latest_places_data": latest_places_data,
        "data_type": str(type(latest_places_data)),
        "data_length": len(latest_places_data) if isinstance(latest_places_data, list) else 0
    })

if __name__ == '__main__':
    if not GOOGLE_PLACES_API_KEY:
        print("錯誤：未設置 GOOGLE_PLACES_API_KEY 環境變數")
        exit(1)
    if not GEMINI_API_KEY:
        print("錯誤：未設置 GEMINI_API_KEY 環境變數")
        exit(1)
    app.run(debug=True)
