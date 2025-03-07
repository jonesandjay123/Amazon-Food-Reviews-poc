from flask import Flask, request, jsonify
import os
import requests
import json
from dotenv import load_dotenv
from google import genai  # 新版 SDK 匯入方式
from google.genai import types  # 如有需要傳入額外設定，可使用

load_dotenv()

app = Flask(__name__)

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 建立 Google GenAI 的 API 客戶端，注意新版 SDK 會從 GOOGLE_API_KEY 環境變數自動抓取，但這裡我們顯性傳入
client = genai.Client(api_key=GEMINI_API_KEY)
# 指定要使用的模型，可根據需求調整，例如 'gemini-2.0-flash'
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
        prompt = f"""
        根據以下自然語言查詢，提取關鍵信息以便進行 Google Places API 查詢。
        僅返回 JSON 格式，包含這些鍵：location（地點）, keyword（關鍵字）, radius（半徑，以米為單位）, limit（結果數量限制）。
        查詢: {user_query}
        """
        # 使用新版 SDK 調用 Gemini API 生成結構化查詢
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        structured_query = json.loads(response.text)
        params = {
            'key': GOOGLE_PLACES_API_KEY,
            'query': structured_query.get('keyword', ''),
            'locationBias': {
                "circle": {
                    "center": {
                        "latitude": 0.0,
                        "longitude": 0.0
                    },
                    "radius": structured_query.get('radius', 5000.0)
                }
            },
            'includedTypes': [],
            'languageCode': 'zh-TW',
            'regionCode': 'TW'
        }
        # 如果有指定地點，則利用地理編碼 API 取得座標
        if 'location' in structured_query and structured_query['location']:
            geocode_params = {
                'key': GOOGLE_PLACES_API_KEY,
                'address': structured_query['location']
            }
            geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
            geocode_response = requests.get(geocode_url, params=geocode_params)
            geocode_data = geocode_response.json()
            if geocode_data['status'] == 'OK':
                location = geocode_data['results'][0]['geometry']['location']
                params['locationBias']['circle']['center']['latitude'] = location['lat']
                params['locationBias']['circle']['center']['longitude'] = location['lng']

        headers = {
            'Content-Type': 'application/json'
        }
        places_url = "https://places.googleapis.com/v1/places:searchText"
        places_response = requests.post(places_url, headers=headers, json=params)

        if places_response.status_code == 200:
            places_data = places_response.json()
            latest_places_data = places_data.get('places', [])
            limit = structured_query.get('limit', 5)
            latest_places_data = latest_places_data[:limit]
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
