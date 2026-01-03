# Research Paper Search Query Decomposer - Setup Guide

This FastAPI application uses Google's Gemini AI to decompose research paper search queries into their relevant components and performs forward/backward citation searches using the Semantic Scholar API.

## Overview

This system:
- Decomposes research queries using Google's Gemini 2.5 Flash model
- Searches for the most relevant paper using Semantic Scholar API
- Performs forward and backward citation searches (with nested layers)
- Rates papers for relevance against the original query criteria
- Provides a React frontend for visualization

## Step 1: Get Your Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey) (or visit https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key" or "Get API Key"
4. Copy the API key that's generated (it will look something like: `AIzaSy...`)

**Note:** Keep this key secret! Don't share it publicly or commit it to version control.

## Step 2: Create Your .env File

**Note:** Semantic Scholar API works without an API key (using direct API links), so you only need the Gemini API key.

1. In the `backend` folder (same folder as `LLMcall.py`), create a new file named `.env` (note the dot at the beginning)
2. Open the `.env` file in a text editor
3. Add the following line, replacing `your_gemini_api_key_here` with your actual API key:

```
GEMINI_API_KEY=AIzaSyYourActualKeyHere
```

**Important:** 
- No spaces around the `=` sign
- No quotes around the API key value
- Make sure the file is named exactly `.env` (not `env.txt` or anything else)

## Step 3: Install Dependencies

```bash
# Navigate to the backend folder
cd backend

# Install dependencies
pip install -r requirements.txt
```

## Step 4: Run the Application

Start the FastAPI server:
```bash
cd backend
uvicorn LLMcall:app --reload
```

The API will be available at `http://localhost:8000`

The server should start without errors. If you see an error about the API key not being set, double-check that:
- Your `.env` file exists in the `backend` folder
- The file is named exactly `.env` (not `.env.txt`)
- The API key is correctly formatted: `GEMINI_API_KEY=your_key_here`

## API Endpoints

### POST `/decompose-query`
Decomposes a search query into its components.

**Request Body:**
```json
{
  "query": "llms and their use in neural networks"
}
```

**Response:**
```json
{
  "original_query": "llms and their use in neural networks",
  "components": [
    {
      "component": "LLMs",
      "description": "Large Language Models",
      "keywords": ["large language models", "transformer", "GPT", "BERT"]
    },
    {
      "component": "Neural Networks",
      "description": "Artificial neural network architectures",
      "keywords": ["neural networks", "deep learning", "artificial intelligence"]
    }
  ],
  "main_concepts": ["LLMs", "Neural Networks", "Integration"],
  "relationships": ["LLMs are built using neural network architectures", "LLMs utilize transformer-based neural networks"]
}
```

### POST `/citation-search-rated`
Performs forward and backward citation search with relevance ratings.

**Request Body:**
```json
{
  "query": "transformer architecture",
  "forward_limit": 3,
  "backward_limit": 3
}
```

**Response:**
```json
{
  "query": "transformer architecture",
  "query_decomposition": { ... },
  "most_relevant_paper": { ... },
  "forward_citations": [ ... ],
  "backward_citations": [ ... ],
  "total_forward": 3,
  "total_backward": 3
}
```

### GET `/`
Returns API information and available endpoints.

### GET `/health`
Health check endpoint.

### GET `/list-models`
Lists available Gemini models.

### GET `/cache/clear`
Clears the search cache.

### GET `/cache/stats`
Gets cache statistics.

## Example Usage

### Using Python requests:

```python
import requests

# Decompose a query
response = requests.post(
    "http://localhost:8000/decompose-query",
    json={"query": "llms and their use in neural networks"}
)
print(response.json())

# Perform citation search with ratings
response = requests.post(
    "http://localhost:8000/citation-search-rated",
    json={
        "query": "transformer architecture",
        "forward_limit": 3,
        "backward_limit": 3
    }
)
print(response.json())
```

### Using example scripts:

Run the example scripts from the `examples` folder:
```bash
cd backend/examples
python example_usage.py
python citation_search_example.py
```

## Troubleshooting

**Error: "GEMINI_API_KEY environment variable is not set"**
- Make sure the `.env` file is in the same folder as `LLMcall.py`
- Check that the file is named exactly `.env` (some systems hide files starting with a dot)
- Verify the format: `GEMINI_API_KEY=your_key` (no spaces, no quotes)

**Semantic Scholar API:**
- The API works without an API key using direct API links
- No additional setup needed for Semantic Scholar
- The system includes retry logic (10 attempts with 1 second delay) for failed API calls

**Error: "Invalid API key"**
- Make sure you copied the entire API key
- Check that there are no extra spaces or characters
- Try generating a new API key from Google AI Studio

**Error: "404 models/gemini-2.5-flash is not found"**
- Visit `http://localhost:8000/list-models` to see available models
- Update the model name in `LLMcall.py` if needed

## Features

- **Query Decomposition**: Uses Gemini LLM to break down queries into components, keywords, concepts, and relationships
- **Intelligent Search**: If initial query finds no results, automatically tries searching individual components
- **Forward/Backward Citation Search**: Finds papers that cite the most relevant paper and papers it cites
- **Nested Search**: Extends search one layer deeper for each citation (forward and backward)
- **Relevance Rating**: Rates all papers as "Perfectly Relevant", "Relevant", or "Somewhat Relevant"
- **Caching**: In-memory and persistent file-based caching for faster repeated searches
- **Retry Logic**: Automatic retries for Semantic Scholar API calls (10 attempts with 1 second delay)
