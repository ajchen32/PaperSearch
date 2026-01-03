# Research Paper Search Query Decomposer

This FastAPI application uses Google's Gemini AI to decompose research paper search queries into their relevant components.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your Gemini API key:
   - Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a `.env` file in the `backend` folder (same folder as `LLMcall.py`)
   - Add: `GEMINI_API_KEY=your_api_key_here`
   - You can use `examples/env_template.txt` as a template (copy it to `.env` in the backend folder)

## Running the Application

Start the FastAPI server:
```bash
cd backend
uvicorn LLMcall:app --reload
```

The API will be available at `http://localhost:8000`

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

### GET `/`
Returns API information and available endpoints.

### GET `/health`
Health check endpoint.

## Example Usage

```python
import requests

response = requests.post(
    "http://localhost:8000/decompose-query",
    json={"query": "llms and their use in neural networks"}
)
print(response.json())
```

Or run the example scripts from the `examples` folder:
```bash
python examples/example_usage.py
python examples/citation_search_example.py
```

## Next Steps

This is the first step in building a forward/backward search system for research papers. The decomposed components can be used to:
- Search for papers by individual components
- Find related papers through forward citations
- Trace back through backward citations
- Build a comprehensive research graph

