# BBC News Mini Corpus API

A RESTful API based on the BBC News Dataset, supporting various category news queries and natural language query processing.

## Key Features

- 📰 Access BBC News article data using SQLite database
- 🔍 Efficient query caching mechanism to improve query speed
- 💬 Support for natural language query processing (using Gemini AI model)
- 🗄️ Concise, modular code structure
- 🚀 Lightweight design, easy to extend
- 🌐 Provides web interface for intuitive querying

## Dataset Information

This project uses the BBC News Dataset, which includes news articles in five main categories:
- **business**: Business news
- **entertainment**: Entertainment news
- **politics**: Political news
- **sport**: Sports news
- **tech**: Technology news

Data source: `https://huggingface.co/datasets/hf-internal/bbc-text/resolve/main/bbc-text.csv`

## Project Structure Diagram

```
bbc-news-api/
├── app.py              # Flask main application entry point
├── routes.py           # API route handling logic
├── db.py               # Database connection and query module
├── chatgpt_model.py    # ChatGPT AI model integration
├── gemini_model.py     # Gemini AI model integration
├── requirements.txt    # Dependency package list
├── .env                # Environment variable configuration file
├── template.env        # Environment variable template
├── README.md           # English documentation
├── README_ZH.md        # Chinese documentation
│
├── scripts/            # Helper scripts
│   └── csv_to_sqlite.py    # Convert CSV to SQLite
│
├── static/             # Static resources
│   ├── css/
│   │   └── style.css       # Stylesheet
│   └── js/
│       └── script.js       # Frontend interaction script
│
├── templates/          # HTML templates
│   ├── index.html          # Main page/chat interface
│   └── api.html            # API documentation page
│
└── data/               # Data folder (auto-created)
    ├── bbc-news.csv        # Original CSV data
    └── bbc_news.sqlite     # SQLite database
```

## System Flow Diagram

```
User Request → Flask Application (app.py)
    ↓
Route Handling (routes.py) → Database Query (db.py) → SQLite Database
    ↓                           ↑
Natural Language Parsing ← Gemini AI Model (gemini_model.py)
    ↓
JSON Response → Frontend Display
```

## Environment Setup

### Prerequisites

- Python 3.8+
- Internet connection (for downloading the dataset)
- Gemini API Key (optional, for natural language query functionality)

### Installation Steps

1. **Clone this repository**:

   ```bash
   git clone <repository-url>
   cd bbc-news-api
   ```

2. **Create and activate a virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install --upgrade pip setuptools wheel
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:

   Copy `template.env` to `.env` and set your Gemini API Key (if you need natural language query functionality):

   ```bash
   cp template.env .env
   # Then edit the .env file to add your API key
   ```

5. **Prepare data**:

   ```bash
   # Step 5: Prepare data
   1. Download CSV: https://huggingface.co/datasets/hf-internal/bbc-text/resolve/main/bbc-text.csv
   2. Rename the file to bbc-news.csv and place it in the data/ folder
   3. Convert to SQLite
      python scripts/csv_to_sqlite.py
   ```

## Running the Application

Start the Flask application:

```bash
python app.py
```

The application will run at http://localhost:5000.

## Using Natural Language Queries

This system supports using natural language to query BBC news articles. These features can be accessed through the chat interface (http://localhost:5000/) or API endpoints.

### Available Natural Language Query Examples:

1. **Category-based queries**:
   - "Find business news"
   - "Show the latest political reports"

2. **Keyword-based queries**:
   - "Find tech news about Apple"
   - "Find sports news that mention football"

3. **Combined queries**:
   - "Find business news discussing markets"
   - "What entertainment news is there about movies?"

## Testing the API

You can test the API in the following ways:

### Using a Browser

Visit the chat interface: http://localhost:5000/

### Using curl

1. **Test natural language queries**:

   ```bash
   curl -X POST http://localhost:5000/api/query \
     -H "Content-Type: application/json" \
     -d '{"query":"Find tech news about Apple"}'
   ```

2. **Get news list**:

   ```bash
   curl http://localhost:5000/api/news?category=tech&limit=10
   ```

3. **Get specific news details**:

   ```bash
   curl http://localhost:5000/api/news/1
   ```

4. **Search news**:

   ```bash
   curl http://localhost:5000/api/search?q=market
   ```

5. **Check system status**:
   ```bash
   curl http://localhost:5000/api/system_status
   ```

## API Endpoint List

### News Queries

- `GET /api/news` - Get news list (supports pagination and category filtering)
  - Parameters: `page`, `limit`, `category`, `keyword`
- `GET /api/news/{news_id}` - Get specific news details

### Search

- `GET /api/search?q={query}` - Basic text search
  - Parameters: `q`, `page`, `limit`
- `POST /api/query` - Natural language query
  - Request body: `{"query": "natural language query text"}`

### System

- `GET /api/debug` - Debug information
- `GET /api/system_status` - Get system status

## Main Module Functions

- **app.py**: Flask application entry point, initializes services and routes
- **routes.py**: Handles all API routes and request logic
- **db.py**: Database connection and query processing, includes caching mechanism
- **gemini_model.py**: Integration with Gemini AI model, processes natural language query parsing

## Extension Suggestions

1. Add more NLP features, such as article summaries or sentiment analysis
2. Implement more advanced search features, such as similarity search
3. Add user authentication and authorization
4. Add support for more news sources
5. Add periodic data update mechanism

## Troubleshooting

1. **Database file does not exist**:
   - Make sure you've downloaded the CSV file and placed it in the data/ folder
   - Run `python scripts/csv_to_sqlite.py` to convert the CSV to SQLite
   - Confirm that the `data/bbc_news.sqlite` file exists

2. **Natural language query functionality is unavailable**:
   - Confirm that the `.env` file exists and contains a valid `GEMINI_API_KEY`
   - Check API key limitations and network connectivity

3. **Application startup error**:
   - Check that all dependencies are correctly installed
   - View logs for detailed error information
   
4. **Query returns empty results**:
   - Confirm that the database has been correctly created and contains data
   - Use the `api/system_status` endpoint to check system status