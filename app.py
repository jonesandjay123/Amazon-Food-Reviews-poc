import os
import json
import time
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_from_directory

# Load environment variables from .env file
load_dotenv()

# Initialize AI model (optional)
AI_MODEL_TYPE = os.getenv("AI_MODEL_TYPE", "GEMINI").upper()
ai_model = None

try:
    if AI_MODEL_TYPE == "GEMINI":
        from gemini_model import GeminiModel
        ai_model = GeminiModel()
        print("Using Gemini AI model")
    else:
        print(f"Unknown AI_MODEL_TYPE: {AI_MODEL_TYPE}")
except Exception as e:
    print(f"Error initializing AI model: {e}")
    # In a production environment, we might need to terminate the application or provide a fallback

# Initialize Flask app
app = Flask(__name__)

# Import routes
from routes import api
app.register_blueprint(api, url_prefix='/api')

# Set hook before request processing to record request time
@app.before_request
def before_request():
    request.environ['REQUEST_TIME'] = time.time()

@app.route("/", methods=["GET"])
def index():
    """Provide HTML page for chat interface"""
    return render_template("index.html")

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

# Global error handling
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    # Initialize database
    from db import check_database
    check_database()
    
    # Start Flask application
    app.run(debug=True, host="0.0.0.0", port=5000) 