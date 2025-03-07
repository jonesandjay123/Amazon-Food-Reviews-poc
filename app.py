from flask import Flask, request, jsonify
import os
import requests
import json
from dotenv import load_dotenv
from google import genai  # 新版 SDK 匯入方式
from google.genai import types  # 如有需要額外設定，可使用

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

@app.route('/query', methods=['POST'])
def query():
    global latest_query, latest_places_data
    try:
        data = request.get_json()
        user_query = data.get('query', '')
        if not user_query:
            return jsonify({"error": "查詢內容不能為空"}), 400
        latest_query = user_query

        # 呼叫 Gemini API 生成結構化查詢
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
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        print("=== Gemini API raw output ===")
        print(response.text)
        structured_query = json.loads(response.text)
        
        # 若 Gemini 回傳的 limit 為 null，則預設為 5
        limit = structured_query.get('limit') if structured_query.get('limit') is not None else 5
        keyword = structured_query.get('keyword', '')
        location_str = structured_query.get('location', '')
        
        # 建立 Places API 的文字查詢字串
        # 若有 location，則組合 "keyword in location"，否則僅使用 keyword
        if location_str:
            text_query = f"{keyword} in {location_str}"
        else:
            text_query = keyword

        # 建立 Places API 的請求主體，依據新版文件只需要 textQuery
        payload = {
            "textQuery": text_query
        }
        # 依文件要求，使用 HTTP 標頭傳入 API 金鑰與欄位遮罩（欄位中間不得有空格）
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.websiteUri,places.regularOpeningHours"
        }
        places_url = "https://places.googleapis.com/v1/places:searchText"
        places_response = requests.post(places_url, headers=headers, json=payload)
        
        # 如果 Places API 回傳失敗，除錯印出相關訊息
        if places_response.status_code != 200:
            print("=== Places API Response ===")
            print(places_response.status_code)
            print(places_response.text)
        
        if places_response.status_code == 200:
            places_data = places_response.json()
            latest_places_data = places_data.get('places', [])[:limit]
            return jsonify({
                "query": user_query,
                "status": "success",
                "message": "查詢成功，請使用 /results 端點查看整理後的結果"
            })
        else:
            return jsonify({"error": f"Places API 請求失敗：{places_response.status_code}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/results', methods=['GET'])
def results():
    global latest_query, latest_places_data
    try:
        if not latest_places_data:
            return jsonify({"error": "尚未有查詢結果，請先使用 /query 端點進行查詢"}), 400
        formatted_results = []
        for place in latest_places_data:
            place_details = get_place_details(place['id'])
            if place_details:
                name = place_details.get('displayName', {}).get('text', 'N/A')
                address = place_details.get('formattedAddress', 'N/A')
                rating = place_details.get('rating', 'N/A')
                website = place_details.get('websiteUri', 'N/A')
                opening_hours = place_details.get('regularOpeningHours', {}).get('text', 'N/A')
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
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    if not GOOGLE_PLACES_API_KEY:
        print("錯誤：未設置 GOOGLE_PLACES_API_KEY 環境變數")
        exit(1)
    if not GEMINI_API_KEY:
        print("錯誤：未設置 GEMINI_API_KEY 環境變數")
        exit(1)
    app.run(debug=True)
