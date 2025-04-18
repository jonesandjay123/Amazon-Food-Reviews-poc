from flask import Blueprint, jsonify, request
from db import execute_query

# Create blueprint
api = Blueprint('api', __name__)

@api.route("/news", methods=["GET"])
def get_news():
    """Get news list, supporting pagination and category filtering"""
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))
    category = request.args.get("category")
    keyword = request.args.get("keyword")
    
    # Calculate pagination offset
    offset = (page - 1) * limit
    
    # Construct query
    sql_query = "SELECT * FROM news WHERE 1=1"
    params = []
    
    # Add category filter
    if category:
        sql_query += " AND category = ?"
        params.append(category)
    
    # Add keyword filter
    if keyword:
        sql_query += " AND (title LIKE ? OR text LIKE ?)"
        keyword_param = f"%{keyword}%"
        params.append(keyword_param)
        params.append(keyword_param)
    
    # Calculate total record count
    count_query = sql_query.replace("SELECT *", "SELECT COUNT(*) as count")
    count_result = execute_query(count_query, tuple(params) if params else None)
    total_count = count_result[0]["count"] if count_result else 0
    
    # Add pagination limits
    sql_query += " LIMIT ? OFFSET ?"
    params.append(limit)
    params.append(offset)
    
    # Execute query
    results = execute_query(sql_query, tuple(params) if params else None)
    
    # Calculate total pages
    total_pages = (total_count + limit - 1) // limit
    
    return jsonify({
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "total_count": total_count,
        "data": results
    })

@api.route("/news/<int:news_id>", methods=["GET"])
def get_news_detail(news_id):
    """Get news details by ID"""
    result = execute_query("SELECT * FROM news WHERE id = ?", (news_id,))
    
    if result:
        return jsonify(result[0])
    else:
        return jsonify({"error": "News not found"}), 404

@api.route("/search", methods=["GET"])
def search_news():
    """Search news (basic text search)"""
    q = request.args.get("q")
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))
    
    if not q:
        return jsonify({"error": "Search keyword cannot be empty"}), 400
    
    offset = (page - 1) * limit
    
    # Construct query (search in title and content)
    sql_query = "SELECT * FROM news WHERE title LIKE ? OR text LIKE ?"
    params = (f"%{q}%", f"%{q}%")
    
    # Calculate total record count
    count_query = sql_query.replace("SELECT *", "SELECT COUNT(*) as count")
    count_result = execute_query(count_query, params)
    total_count = count_result[0]["count"] if count_result else 0
    
    # Add pagination limits
    sql_query += " LIMIT ? OFFSET ?"
    params = params + (limit, offset)
    
    # Execute query
    results = execute_query(sql_query, params)
    
    # Calculate total pages
    total_pages = (total_count + limit - 1) // limit
    
    return jsonify({
        "query": q,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "total_count": total_count,
        "data": results
    })

@api.route("/query", methods=["POST"])
def query_news():
    """Natural language query for news (using Gemini API)"""
    data = request.get_json()
    
    if not data or "query" not in data:
        return jsonify({"error": "Query cannot be empty"}), 400
    
    user_query = data["query"]
    
    # Can connect to Gemini API to parse query here
    # Simplified version: directly parse common categories and keywords
    
    # Simple parsing logic
    parsed_data = parse_natural_language_query(user_query)
    
    # Construct query
    sql_query = "SELECT * FROM news WHERE 1=1"
    params = []
    
    if parsed_data.get("category"):
        sql_query += " AND category = ?"
        params.append(parsed_data["category"])
    
    if parsed_data.get("keyword"):
        sql_query += " AND (title LIKE ? OR text LIKE ?)"
        keyword_param = f"%{parsed_data['keyword']}%"
        params.append(keyword_param)
        params.append(keyword_param)
    
    # Add limit
    sql_query += " LIMIT 10"
    
    # Execute query
    results = execute_query(sql_query, tuple(params) if params else None)
    
    return jsonify({
        "query": user_query,
        "parsed": parsed_data,
        "results": results
    })

@api.route("/system_status", methods=["GET"])
def system_status():
    """Get system status"""
    from db import check_database
    
    db_status = check_database()
    
    return jsonify({
        "status": "ok" if db_status else "error",
        "database": "connected" if db_status else "error",
        "timestamp": request.environ.get('REQUEST_TIME', 0)
    })

@api.route("/debug", methods=["GET"])
def debug():
    """Debug information"""
    from db import cache
    
    return jsonify({
        "cache_size": len(cache["query_cache"]),
        "last_load_time": cache["last_load_time"],
        "timestamp": request.environ.get('REQUEST_TIME', 0)
    })

def parse_natural_language_query(query):
    """Parse natural language query, extract category and keywords"""
    result = {"keyword": None, "category": None}
    
    # Convert to lowercase for matching
    query_lower = query.lower()
    
    # Check category (5 categories: business, entertainment, politics, sport, tech)
    categories = ["business", "entertainment", "politics", "sport", "tech"]
    for category in categories:
        if category in query_lower:
            result["category"] = category
            break
    
    # Extract keywords (simplified version)
    # Can extract based on common keyword patterns
    keywords = ["about", "related to", "concerning", "on"]
    for keyword in keywords:
        if keyword in query_lower:
            parts = query_lower.split(keyword, 1)
            if len(parts) > 1 and parts[1].strip():
                # Take text after the last keyword as search term
                result["keyword"] = parts[1].strip()
                # Remove any trailing punctuation
                result["keyword"] = result["keyword"].rstrip(".,;:?!")
                break
    
    # If above methods do not find keywords, use some heuristic rules
    if not result["keyword"]:
        # Remove category words and common verbs, take the longest word as keyword
        exclude_words = categories + ["list", "show", "find", "get", "latest", "news"]
        words = [w for w in query_lower.split() if w not in exclude_words and len(w) > 3]
        if words:
            result["keyword"] = max(words, key=len)
    
    return result 