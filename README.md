# Amazon Fine Food Reviews API

A RESTful API based on the Kaggle Amazon Fine Food Reviews dataset, supporting food review queries and natural language queries using the Gemini API.

## Key Features

- 🍕 Access Amazon food review data using SQLite database
- 🔍 Efficient query caching mechanism for improved query speed
- 💬 Google Gemini API integration for natural language processing
- 📚 Complete Swagger API documentation
- 🧠 Intelligent review search and analysis

## Environment Setup

### Prerequisites

- Python 3.9+
- Kaggle account and API key
- Google Gemini API key

### Installation Steps

1. **Clone this repository**:

   ```bash
   git clone <repository-url>
   cd food-reviews-api
   ```

2. **Create and activate virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file and add the following:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

### Kaggle API Setup

1. **Get Kaggle API key**:
   - Kaggle API keys are typically stored in the `~/.kaggle/kaggle.json` file
   - If not yet set up, log in to [Kaggle](https://www.kaggle.com/), click on your profile picture in the top right > Account > API > Create New API Token

### Download Data

#### Option 1: Using the provided script (recommended)
Run the following commands to download and extract the Amazon Fine Food Reviews dataset:

```bash
chmod +x download_data.sh
./download_data.sh
```

This will download the database file and extract it to the `data` directory.

#### Option 2: Manual download
1. Manually download the dataset from Kaggle: [Amazon Fine Food Reviews](https://www.kaggle.com/datasets/snap/amazon-fine-food-reviews)
2. Extract the `database.sqlite` file
3. Create a `data` directory in your project root if it doesn't exist
4. Place the `database.sqlite` file in the `data` directory

## Running the Application

Start the Flask application:

```bash
python app.py
```

The application will run at http://localhost:5000.

## Using Gemini API Natural Language Queries

This system integrates Google Gemini API to query food review data using natural language. These features can be accessed through the chat interface (http://localhost:5000/) or the API endpoint.

### Sample Natural Language Queries:

1. **Keyword-based searches**:
   - "Find reviews about chocolate"
   - "Show reviews containing 'delicious'"

2. **Rating-based filtering**:
   - "Find 5-star chocolate reviews"
   - "Show food reviews with ratings higher than 3 stars"

3. **Specific product queries**:
   - "Find all reviews for product ID B001E4KFG0"
   - "What positive reviews did this product B000LQOCH0 receive?"

4. **User review analysis**:
   - "Show all reviews by user A1RSDE90N6RSZF"
   - "Which users gave the most 5-star ratings?"

5. **Sentiment analysis**:
   - "Find the most positive reviews for chocolate"
   - "What negative reviews are there for this product B005IGVBPK?"

6. **Combined queries**:
   - "Find 5-star chocolate reviews from 2010"
   - "Show 1-star reviews that contain 'disappointed'"

### How Gemini API Works:

The system sends your natural language query to the Gemini API, which parses the query and extracts key parameters:
- Keywords (keyword)
- Rating range (min_score, max_score)
- Product identifiers (product)
- User identifiers (user)
- Sentiment orientation (sentiment)

Then, the system uses these parameters to construct SQL queries to retrieve relevant reviews from the database.

## Testing the API

You can test the API in several ways:

### Using a Browser

1. Access the API documentation: http://localhost:5000/api/docs/
2. Use the chat interface: http://localhost:5000/

### Using curl

1. **Test natural language queries**:

   ```bash
   curl -X POST http://localhost:5000/api/query \
     -H "Content-Type: application/json" \
     -d '{"query":"Find 5-star reviews for chocolate"}'
   ```

2. **Get review list**:

   ```bash
   curl http://localhost:5000/api/reviews?limit=10&min_score=5
   ```

3. **Get reviews for a specific product**:

   ```bash
   curl http://localhost:5000/api/product/B001E4KFG0
   ```

4. **Search reviews**:

   ```bash
   curl http://localhost:5000/api/search?q=delicious
   ```

5. **Check system status**:
   ```bash
   curl http://localhost:5000/api/debug
   ```

## Dataset Information

This project uses the "Amazon Fine Food Reviews" dataset from Kaggle, containing approximately 568,454 food reviews from Amazon:
https://www.kaggle.com/datasets/snap/amazon-fine-food-reviews

The database file (`database.sqlite`) contains the following information:
- Product review text and rating (1-5 stars)
- Product information
- User information
- Review time and summary

## Troubleshooting

1. **Kaggle API authentication error**:
   - Verify that the `~/.kaggle/kaggle.json` file exists and has the correct permissions

2. **Database file not found**:
   - Run `./download_data.sh` to download the database file
   - Verify that the `data/database.sqlite` file exists

3. **Gemini API errors**:
   - Confirm that the `GEMINI_API_KEY` is correctly set in the `.env` file
   - Check if the API key is valid and whether usage limits have been reached

## API Endpoint List

### Review Queries

- `GET /api/reviews` - Get review list (supports pagination and rating filtering)
- `GET /api/reviews/{review_id}` - Get specific review details

### Products and Users

- `GET /api/product/{product_id}` - Get reviews for a specific product
- `GET /api/user/{user_id}` - Get reviews by a specific user

### Search

- `GET /api/search?q={query}` - Basic review search
- `POST /api/query` - Natural language query (using Gemini API)

### System

- `GET /api/debug` - Check system status
- `GET /api/system_status` - Get detailed system status including LangChain availability
- `POST /api/toggle_langchain` - Toggle LangChain mode

## LangChain Enhanced Features

This project now includes advanced capabilities through LangChain integration, enabling more sophisticated natural language processing and multi-step reasoning. LangChain uses a chain of tools to break down complex queries into sequences of steps.

### Enabling LangChain

There are three ways to enable LangChain:

1. **Environment variable**: Set `USE_LANGCHAIN=true` in your environment or `.env` file.
2. **Toggle in UI**: Use the toggle switch in the top right corner of the chat interface.
3. **API parameter**: Add `"force_langchain": true` to your API requests.

```bash
# Example of toggling LangChain via API
curl -X POST http://localhost:5000/api/toggle_langchain \
  -H "Content-Type: application/json" \
  -d '{"enable_langchain": true}'
```

### Comparing Standard RAG vs. LangChain

The table below shows the key differences between the standard RAG approach and LangChain enhanced queries:

| Feature | Standard RAG | LangChain Enhanced |
|---------|-------------|-------------------|
| Query complexity | Single-step, direct mapping to SQL | Multi-step reasoning, dynamic query construction |
| Self-correction | No | Yes, can adjust queries based on intermediate results |
| Analysis depth | Basic | In-depth with data aggregation capabilities |
| Interactive | No | Can suggest related queries |
| Data insights | Limited to direct results | Provides broader context and patterns |

### Sample Complex Queries for LangChain

LangChain excels with complex queries that require multiple steps or deeper analysis. Try these examples to see the difference:

1. **Multi-step aggregation queries**:
   - "What are the top 5 products with the most reviews in the last 3 years?"
   - "Show me which products have higher than average ratings but with at least 10 reviews"

2. **Trend analysis**:
   - "Has the average rating for chocolate products improved over time?"
   - "Are people writing longer reviews for highly rated products?"

3. **Complex filtering with analytics**:
   - "Find users who gave both 5-star and 1-star ratings and compare their review styles"
   - "Which products have polarizing reviews (many 5-star and many 1-star ratings)?"

4. **Comparative analysis**:
   - "Compare reviews for products B001E4KFG0 and B000LQOCH0 in terms of sentiment and common keywords"
   - "What are the most common complaints in negative reviews for highly rated products?"

### Testing the Difference

To experience the full power of LangChain, try running the same complex query with and without LangChain enabled:

1. Toggle LangChain OFF and ask: "What products have the most helpful reviews for chocolate with at least a 4-star rating?"
2. Toggle LangChain ON and ask the same question.

Notice how the LangChain version provides:
- More comprehensive results
- Step-by-step reasoning
- Additional insights
- Better structured data

### Viewing LangChain's Reasoning

When using the UI with LangChain enabled, you'll see a "Show reasoning steps" dropdown that reveals how LangChain broke down your query and the intermediate steps it took to arrive at the answer. This transparency helps understand the system's reasoning process.

## Future Plans

We plan to enhance the LangChain integration by:
1. Adding more specialized tools for deeper analysis
2. Implementing conversation memory for follow-up questions
3. Supporting more complex data visualization capabilities
4. Adding automatic insight generation for all queries 