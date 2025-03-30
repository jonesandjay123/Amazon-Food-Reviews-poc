import os
import json
import time
import sqlite3
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_from_directory
from flasgger import Swagger, swag_from

# initialize model
from gemini_model import GeminiModel
# optional model for future use
# from chatgpt_model import ChatGPTModel

# Import LangChain agent (optional, controlled by environment variable)
USE_LANGCHAIN = os.getenv("USE_LANGCHAIN", "False").lower() == "true"
langchain_agent = None
if USE_LANGCHAIN:
    try:
        from langchain_agent import LangChainAgent
        langchain_agent = LangChainAgent()
        print("LangChain Agent initialized successfully")
    except Exception as e:
        print(f"Error initializing LangChain Agent: {e}")
        print("Falling back to standard RAG approach")
        USE_LANGCHAIN = False

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure Swagger
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,  # All endpoints
            "model_filter": lambda tag: True,  # All models
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/api/docs/"
}

swagger_template = {
    "info": {
        "title": "Amazon Fine Food Reviews API",
        "description": "RESTful API implemented using Amazon Fine Food Reviews data, supporting various food review query functions",
        "version": "1.0.0",
        "contact": {
            "name": "API Support",
            "email": "support@example.com"
        }
    },
    "tags": [
        {
            "name": "Review List",
            "description": "Get review lists and detailed information"
        },
        {
            "name": "Products and Users",
            "description": "Get reviews for specific products or users"
        },
        {
            "name": "Search",
            "description": "Search reviews and natural language queries"
        },
        {
            "name": "System",
            "description": "Debug and system information"
        }
    ]
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)

# initialize model
# can be controlled by environment variable
AI_MODEL_TYPE = os.getenv("AI_MODEL_TYPE", "GEMINI").upper()
ai_model = None

try:
    if AI_MODEL_TYPE == "GEMINI":
        ai_model = GeminiModel()
        print("Using Gemini AI model")
    elif AI_MODEL_TYPE == "CHATGPT":
        # Uncomment when ChatGPT model is ready
        # ai_model = ChatGPTModel()
        # print("Using ChatGPT AI model")
        print("ChatGPT model not implemented yet, falling back to Gemini")
        ai_model = GeminiModel()
    else:
        print(f"Unknown AI_MODEL_TYPE: {AI_MODEL_TYPE}, falling back to Gemini")
        ai_model = GeminiModel()
except Exception as e:
    print(f"Error initializing AI model: {e}")
    # in real application, it may need to terminate the application or provide a backup plan

# Set database path
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DATA_DIR, "database.sqlite")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Query result cache
cache = {
    "query_cache": {},  # Query result cache
    "last_load_time": 0  # Timestamp of last data load
}

# Connect to SQLite database
def get_db_connection():
    """Create and return a SQLite database connection"""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database file not found: {DB_PATH}. Please run download_data.sh to download the data first.")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return results as dictionaries
    return conn

def execute_query(query, params=None, cache_key=None):
    """Execute SQLite query, support caching results"""
    # If cache key is provided and query result is cached, return cached result
    if cache_key and cache_key in cache["query_cache"]:
        print(f"Using cached result: {cache_key}")
        return cache["query_cache"][cache_key]
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
            
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Cache result (if cache key is provided)
        if cache_key:
            cache["query_cache"][cache_key] = results
            
        return results
    except Exception as e:
        print(f"Error executing query: {e}")
        if conn:
            conn.close()
        raise e

def check_database():
    """Check database structure and display basic information"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("Database table structure:")
        for table in tables:
            table_name = table['name']
            print(f"- {table_name}")
            
            # Get column information for the table
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  - {col['name']} ({col['type']})")
                
            # Get record count
            cursor.execute(f"SELECT COUNT(*) as count FROM {table_name};")
            count = cursor.fetchone()['count']
            print(f"  - Record count: {count}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"Error checking database: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return False

@app.route("/", methods=["GET"])
def index():
    """Provide HTML page for chat interface"""
    # Pass LangChain status to template
    return render_template("index.html", use_langchain=USE_LANGCHAIN)

@app.route("/api", methods=["GET"])
def api_home():
    """Provide entry page for API documentation and testing interface"""
    return render_template("api.html")

@app.route("/api/reviews", methods=["GET"])
@swag_from({
    "tags": ["Review List"],
    "summary": "Get review list",
    "description": "Get Amazon Fine Food review list, supporting various filters",
    "parameters": [
        {
            "name": "page",
            "in": "query",
            "type": "integer",
            "default": 1,
            "description": "Page number"
        },
        {
            "name": "limit",
            "in": "query",
            "type": "integer",
            "default": 20,
            "description": "Number of results per page"
        },
        {
            "name": "min_score",
            "in": "query",
            "type": "integer",
            "description": "Minimum rating (1-5)"
        },
        {
            "name": "max_score",
            "in": "query",
            "type": "integer",
            "description": "Maximum rating (1-5)"
        }
    ],
    "responses": {
        "200": {
            "description": "Successfully retrieved review list"
        }
    }
})
def get_reviews():
    """Get review list, supports pagination and rating filters"""
    # Get query parameters
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 20, type=int)
    min_score = request.args.get("min_score", type=int)
    max_score = request.args.get("max_score", type=int)

    # Build query and parameters
    query = "SELECT * FROM Reviews WHERE 1=1"
    params = []
    
    if min_score:
        query += " AND Score >= ?"
        params.append(min_score)
    
    if max_score:
        query += " AND Score <= ?"
        params.append(max_score)
    
    # Add pagination
    offset = (page - 1) * limit
    query += f" ORDER BY Time DESC LIMIT {limit} OFFSET {offset}"
    
    # Cache key
    cache_key = f"reviews:{page}:{limit}:{min_score}:{max_score}"
    
    # Execute query
    try:
        results = execute_query(query, tuple(params) if params else None, cache_key)
        
        # Get total record count (for pagination)
        count_query = "SELECT COUNT(*) as total FROM Reviews WHERE 1=1"
        if min_score:
            count_query += " AND Score >= ?"
        if max_score:
            count_query += " AND Score <= ?"
        
        count_results = execute_query(count_query, tuple(params) if params else None)
        total = count_results[0]['total'] if count_results else 0
        
        return jsonify({
            "page": page,
            "limit": limit,
            "total_results": total,
            "total_pages": (total + limit - 1) // limit if total > 0 else 1,
            "results": results
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/reviews/<string:review_id>", methods=["GET"])
@swag_from({
    "tags": ["Review List"],
    "summary": "Get review details",
    "description": "Get detailed information by review ID",
    "parameters": [
        {
            "name": "review_id",
            "in": "path",
            "type": "string",
            "required": True,
            "description": "Review ID"
        }
    ],
    "responses": {
        "200": {
            "description": "Successfully retrieved review details"
        },
        "404": {
            "description": "Review not found"
        }
    }
})
def get_review_details(review_id):
    """Get detailed information for a single review"""
    try:
        query = "SELECT * FROM Reviews WHERE Id = ?"
        results = execute_query(query, (review_id,))
        
        if not results:
            return jsonify({"error": "Review not found"}), 404
        
        review = results[0]
        
        # Get related product information
        product_query = """
        SELECT ProductId, COUNT(*) as review_count, AVG(Score) as avg_score 
        FROM Reviews 
        WHERE ProductId = ? 
        GROUP BY ProductId
        """
        product_info = execute_query(product_query, (review['ProductId'],))
        
        # Build complete response
        response = {
            **review,
            "product_info": product_info[0] if product_info else None
        }
        
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/product/<string:product_id>", methods=["GET"])
@swag_from({
    "tags": ["Products and Users"],
    "summary": "Get product reviews",
    "description": "Get all reviews for a specific product",
    "parameters": [
        {
            "name": "product_id",
            "in": "path",
            "type": "string",
            "required": True,
            "description": "Product ID"
        },
        {
            "name": "page",
            "in": "query",
            "type": "integer",
            "default": 1,
            "description": "Page number"
        },
        {
            "name": "limit",
            "in": "query",
            "type": "integer",
            "default": 20,
            "description": "Number of results per page"
        }
    ],
    "responses": {
        "200": {
            "description": "Successfully retrieved product reviews"
        }
    }
})
def get_product_reviews(product_id):
    """Get all reviews for a specific product"""
    # Get query parameters
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 20, type=int)
    offset = (page - 1) * limit
    
    try:
        # Get product reviews
        query = """
        SELECT * FROM Reviews 
        WHERE ProductId = ? 
        ORDER BY Time DESC 
        LIMIT ? OFFSET ?
        """
        reviews = execute_query(query, (product_id, limit, offset))
        
        # Get product review statistics
        stats_query = """
        SELECT 
            ProductId, 
            COUNT(*) as review_count, 
            AVG(Score) as avg_score,
            SUM(CASE WHEN Score = 5 THEN 1 ELSE 0 END) as five_star,
            SUM(CASE WHEN Score = 4 THEN 1 ELSE 0 END) as four_star,
            SUM(CASE WHEN Score = 3 THEN 1 ELSE 0 END) as three_star,
            SUM(CASE WHEN Score = 2 THEN 1 ELSE 0 END) as two_star,
            SUM(CASE WHEN Score = 1 THEN 1 ELSE 0 END) as one_star
        FROM Reviews 
        WHERE ProductId = ?
        GROUP BY ProductId
        """
        stats = execute_query(stats_query, (product_id,))
        
        # Get total record count (for pagination)
        count_query = "SELECT COUNT(*) as total FROM Reviews WHERE ProductId = ?"
        count_results = execute_query(count_query, (product_id,))
        total = count_results[0]['total'] if count_results else 0
        
        return jsonify({
            "product_id": product_id,
            "statistics": stats[0] if stats else None,
            "page": page,
            "limit": limit,
            "total_reviews": total,
            "total_pages": (total + limit - 1) // limit if total > 0 else 1,
            "reviews": reviews
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/user/<string:user_id>", methods=["GET"])
@swag_from({
    "tags": ["Products and Users"],
    "summary": "Get user reviews",
    "description": "Get all reviews by a specific user",
    "parameters": [
        {
            "name": "user_id",
            "in": "path",
            "type": "string",
            "required": True,
            "description": "User ID"
        },
        {
            "name": "page",
            "in": "query",
            "type": "integer",
            "default": 1,
            "description": "Page number"
        },
        {
            "name": "limit",
            "in": "query",
            "type": "integer",
            "default": 20,
            "description": "Number of results per page"
        }
    ],
    "responses": {
        "200": {
            "description": "Successfully retrieved user reviews"
        }
    }
})
def get_user_reviews(user_id):
    """Get all reviews by a specific user"""
    # Get query parameters
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 20, type=int)
    offset = (page - 1) * limit
    
    try:
        # Get user reviews
        query = """
        SELECT * FROM Reviews 
        WHERE UserId = ? 
        ORDER BY Time DESC 
        LIMIT ? OFFSET ?
        """
        reviews = execute_query(query, (user_id, limit, offset))
        
        # Get user review statistics
        stats_query = """
        SELECT 
            UserId, 
            ProfileName,
            COUNT(*) as review_count, 
            AVG(Score) as avg_score
        FROM Reviews 
        WHERE UserId = ?
        GROUP BY UserId, ProfileName
        """
        stats = execute_query(stats_query, (user_id,))
        
        # Get total record count (for pagination)
        count_query = "SELECT COUNT(*) as total FROM Reviews WHERE UserId = ?"
        count_results = execute_query(count_query, (user_id,))
        total = count_results[0]['total'] if count_results else 0
        
        return jsonify({
            "user_id": user_id,
            "user_profile": stats[0] if stats else None,
            "page": page,
            "limit": limit,
            "total_reviews": total,
            "total_pages": (total + limit - 1) // limit if total > 0 else 1,
            "reviews": reviews
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/search", methods=["GET"])
@swag_from({
    "tags": ["Search"],
    "summary": "Search reviews",
    "description": "Search reviews using keywords",
    "parameters": [
        {
            "name": "q",
            "in": "query",
            "type": "string",
            "required": True,
            "description": "Search keyword"
        },
        {
            "name": "page",
            "in": "query",
            "type": "integer",
            "default": 1,
            "description": "Page number"
        },
        {
            "name": "limit",
            "in": "query",
            "type": "integer",
            "default": 20,
            "description": "Number of results per page"
        }
    ],
    "responses": {
        "200": {
            "description": "Successfully retrieved search results"
        },
        "400": {
            "description": "Search query cannot be empty"
        }
    }
})
def search_reviews():
    """Search reviews using keywords"""
    query_text = request.args.get("q", "")
    if not query_text:
        return jsonify({"error": "Search keyword must be provided"}), 400
    
    # Get query parameters
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 20, type=int)
    offset = (page - 1) * limit
    
    # Build search query
    search_query = """
    SELECT * FROM Reviews 
    WHERE Text LIKE ? OR Summary LIKE ? 
    ORDER BY Time DESC 
    LIMIT ? OFFSET ?
    """
    search_params = (f"%{query_text}%", f"%{query_text}%", limit, offset)
    
    try:
        # Execute query
        results = execute_query(search_query, search_params)
        
        # Get total record count (for pagination)
        count_query = "SELECT COUNT(*) as total FROM Reviews WHERE Text LIKE ? OR Summary LIKE ?"
        count_params = (f"%{query_text}%", f"%{query_text}%")
        count_results = execute_query(count_query, count_params)
        total = count_results[0]['total'] if count_results else 0
        
        return jsonify({
            "query": query_text,
            "page": page,
            "limit": limit,
            "total_results": total,
            "total_pages": (total + limit - 1) // limit if total > 0 else 1,
            "results": results
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/query", methods=["POST"])
@swag_from({
    "tags": ["Search"],
    "summary": "Natural language query for reviews",
    "description": "Query reviews using natural language, processed by AI API with optional LangChain enhancement",
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
                        "description": "Natural language query"
                    },
                    "force_langchain": {
                        "type": "boolean",
                        "description": "Force use of LangChain for this query (override environment setting)"
                    },
                    "force_standard": {
                        "type": "boolean",
                        "description": "Force use of standard RAG for this query (override environment setting)"
                    }
                },
                "required": ["query"]
            }
        }
    ],
    "responses": {
        "200": {
            "description": "Successfully retrieved query results"
        },
        "400": {
            "description": "Query cannot be empty"
        },
        "500": {
            "description": "Error occurred while processing query"
        }
    }
})
def query_reviews():
    """Query reviews using natural language (using AI API)"""
    data = request.get_json()
    if not data or "query" not in data:
        return jsonify({"error": "Natural language query must be provided"}), 400

    user_query = data["query"]
    
    # Check if we should use LangChain for this specific query
    use_langchain_for_query = USE_LANGCHAIN
    if "force_langchain" in data and data["force_langchain"] is True:
        use_langchain_for_query = True
    elif "force_standard" in data and data["force_standard"] is True:
        use_langchain_for_query = False
    
    # Add information about which approach is being used
    query_metadata = {
        "query_method": "langchain" if use_langchain_for_query else "standard_rag",
        "ai_model": AI_MODEL_TYPE,
        "timestamp": time.time()
    }

    try:
        # Use LangChain Agent if enabled
        if use_langchain_for_query and langchain_agent:
            print(f"Using LangChain Agent for query: {user_query}")
            response = langchain_agent.process_query(user_query)
            response["query_metadata"] = query_metadata
            return jsonify(response)
            
        # Otherwise use standard RAG approach
        print(f"Using standard RAG approach for query: {user_query}")
        
        # Use AI model to parse query
        structured_query = ai_model.parse_natural_language_query(user_query)

        # Search reviews based on structured query
        sql_query = "SELECT * FROM Reviews WHERE 1=1"
        params = []
        
        # Handle rating range
        if "min_score" in structured_query and structured_query["min_score"]:
            sql_query += " AND Score >= ?"
            params.append(structured_query["min_score"])
        
        if "max_score" in structured_query and structured_query["max_score"]:
            sql_query += " AND Score <= ?"
            params.append(structured_query["max_score"])
        
        # Handle keywords
        if "keyword" in structured_query and structured_query["keyword"]:
            keyword = structured_query["keyword"]
            sql_query += " AND (Text LIKE ? OR Summary LIKE ?)"
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        
        # Handle specific product
        if "product" in structured_query and structured_query["product"]:
            product = structured_query["product"]
            # Try to match product ID directly or search in text
            sql_query += " AND (ProductId = ? OR Text LIKE ? OR Summary LIKE ?)"
            params.extend([product, f"%{product}%", f"%{product}%"])
        
        # Handle specific user
        if "user" in structured_query and structured_query["user"]:
            user = structured_query["user"]
            # Try to match user ID or name
            sql_query += " AND (UserId = ? OR ProfileName LIKE ?)"
            params.extend([user, f"%{user}%"])
            
        # Sort and limit results
        sql_query += " ORDER BY Time DESC LIMIT 10"
        
        # Execute query
        results = execute_query(sql_query, tuple(params) if params else None)
            
        return jsonify({
            "query": user_query,
            "interpreted_as": structured_query,
            "results_count": len(results),
            "results": results,
            "query_metadata": query_metadata
        })
        
    except Exception as e:
        print(f"Query processing error: {e}")
        return jsonify({
            "error": str(e),
            "query_metadata": query_metadata
        }), 500

@app.route("/api/toggle_langchain", methods=["POST"])
@swag_from({
    "tags": ["System"],
    "summary": "Toggle LangChain mode",
    "description": "Toggle between standard RAG and LangChain Agent for natural language queries",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "enable_langchain": {
                        "type": "boolean",
                        "description": "Whether to enable LangChain Agent"
                    }
                },
                "required": ["enable_langchain"]
            }
        }
    ],
    "responses": {
        "200": {
            "description": "Successfully updated LangChain mode"
        },
        "400": {
            "description": "Invalid request"
        },
        "500": {
            "description": "Error updating LangChain mode"
        }
    }
})
def toggle_langchain():
    """Toggle LangChain mode for natural language queries"""
    global USE_LANGCHAIN, langchain_agent
    
    data = request.get_json()
    if not data or "enable_langchain" not in data:
        return jsonify({"error": "enable_langchain parameter must be provided"}), 400
    
    try:
        enable_langchain = data["enable_langchain"]
        
        # If enabling LangChain and it's not already initialized
        if enable_langchain and not langchain_agent:
            from langchain_agent import LangChainAgent
            langchain_agent = LangChainAgent()
        
        USE_LANGCHAIN = enable_langchain
        mode = "enabled" if USE_LANGCHAIN else "disabled"
        
        print(f"LangChain Agent {mode}")
        return jsonify({
            "success": True,
            "message": f"LangChain Agent {mode}",
            "langchain_enabled": USE_LANGCHAIN
        })
    except Exception as e:
        print(f"Error toggling LangChain mode: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/system_status", methods=["GET"])
@swag_from({
    "tags": ["System"],
    "summary": "System status",
    "description": "Get system status including LangChain availability",
    "responses": {
        "200": {
            "description": "Successfully retrieved system status"
        }
    }
})
def system_status():
    """Get system status including LangChain availability"""
    try:
        # Check database connection
        db_ok = check_database()
        
        return jsonify({
            "status": "ok" if db_ok and ai_model else "error",
            "database": {
                "connected": db_ok,
                "path": DB_PATH,
                "exists": os.path.exists(DB_PATH)
            },
            "ai_model": {
                "type": AI_MODEL_TYPE,
                "initialized": ai_model is not None
            },
            "langchain": {
                "available": langchain_agent is not None,
                "enabled": USE_LANGCHAIN
            },
            "cache": {
                "size": len(cache["query_cache"]) if "query_cache" in cache else 0
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/debug", methods=["GET"])
@swag_from({
    "tags": ["System"],
    "summary": "Debug system status",
    "description": "Get system data loading status information",
    "responses": {
        "200": {
            "description": "Successfully retrieved system status"
        }
    }
})
def debug():
    """Debug endpoint for viewing database status"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [dict(row) for row in cursor.fetchall()]
        
        # Get record count for each table
        table_counts = {}
        for table in tables:
            table_name = table['name']
            cursor.execute(f"SELECT COUNT(*) as count FROM {table_name};")
            count = cursor.fetchone()['count']
            table_counts[table_name] = count
        
        conn.close()
        
        return jsonify({
            "database_path": DB_PATH,
            "database_exists": os.path.exists(DB_PATH),
            "tables": tables,
            "record_counts": table_counts,
            "cache_status": {
                "query_cache_size": len(cache["query_cache"]),
                "last_load_time": cache["last_load_time"]
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/favicon.ico')
def favicon():
    """Provide website icon"""
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == "__main__":
    # check if database and AI model are initialized correctly
    if not ai_model:
        print("Error: AI model initialization failed")
        exit(1)

    print("Initializing Amazon Fine Food Reviews system...")
    print(f"LangChain Agent: {'Enabled' if USE_LANGCHAIN else 'Disabled'}")
    
    if not os.path.exists(DB_PATH):
        print(f"Warning: Database file not found: {DB_PATH}")
        print("Please run download_data.sh to download the data first")
    else:
        print(f"Database file exists: {DB_PATH}")
        check_database()
    
    # Use environment variable to control debug mode, default is False (safe mode)
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    
    app.run(debug=debug_mode) 