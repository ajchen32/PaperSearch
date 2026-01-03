from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import google.generativeai as genai
import os
import json
import re
import requests
from dotenv import load_dotenv
from functools import lru_cache
import hashlib
from pathlib import Path
import time

# Load environment variables
load_dotenv()

app = FastAPI(title="Research Paper Search Query Decomposer")

# Cache file path
CACHE_FILE = Path(__file__).parent / "cache.json"

# Cache for search results (in-memory cache)
_search_cache: Dict[str, dict] = {}


def load_cache() -> Dict[str, dict]:
    """Load cache from JSON file."""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load cache file: {e}")
            return {}
    return {}


def save_cache(cache: Dict[str, dict]):
    """Save cache to JSON file."""
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Warning: Could not save cache file: {e}")


# Load cache on startup
_search_cache = load_cache()

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development (restrict in production)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Initialize Gemini
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

genai.configure(api_key=gemini_api_key)
# Default to gemini-pro (most widely available)
# Visit http://localhost:8000/list-models to see all available models with your API key
# Then update the model name below if needed (e.g., 'gemini-1.5-pro', 'gemini-1.5-flash')
model = genai.GenerativeModel('gemini-2.5-flash')

# Initialize Semantic Scholar API (no API key required - uses public API)
SEMANTIC_SCHOLAR_BASE_URL = "https://api.semanticscholar.org/graph/v1"
SEMANTIC_SCHOLAR_HEADERS = {}  # No authentication needed for public API


class SearchQueryRequest(BaseModel):
    query: str


class QueryComponent(BaseModel):
    component: str
    description: str
    keywords: List[str]


class QueryDecompositionResponse(BaseModel):
    original_query: str
    components: List[QueryComponent]
    main_concepts: List[str]
    relationships: List[str]


# Semantic Scholar Models
class Paper(BaseModel):
    paperId: str
    title: str
    abstract: Optional[str] = None
    authors: Optional[List[dict]] = None
    year: Optional[int] = None
    citationCount: Optional[int] = None
    referenceCount: Optional[int] = None
    url: Optional[str] = None
    relevance_rating: Optional[str] = None  # "Perfectly Relevant", "Relevant", or "Somewhat Relevant"


class CitationSearchRequest(BaseModel):
    query: str
    forward_limit: int = 3
    backward_limit: int = 3


class CitationResult(BaseModel):
    paper: Paper
    forward_citations: List[Paper]
    backward_citations: List[Paper]


class PaperWithNestedCitations(BaseModel):
    paper: Paper
    nested_forward_citations: List[Paper] = []  # Forward citations of forward citations (one more layer forward)
    nested_backward_citations: List[Paper] = []  # Backward citations of backward citations (one more layer backward)


class RatedCitationSearchResponse(BaseModel):
    query: str
    query_decomposition: QueryDecompositionResponse
    most_relevant_paper: Paper
    forward_citations: List[PaperWithNestedCitations]
    backward_citations: List[PaperWithNestedCitations]
    total_forward: int
    total_backward: int


class CitationSearchResponse(BaseModel):
    query: str
    most_relevant_paper: Paper
    forward_citations: List[PaperWithNestedCitations]  # First layer forward with nested
    backward_citations: List[PaperWithNestedCitations]  # First layer backward with nested
    total_forward: int
    total_backward: int


def decompose_query(query: str) -> QueryDecompositionResponse:
    """
    Uses Gemini to decompose a search query into relevant components.
    """
    prompt = f"""You are a research assistant helping to decompose academic search queries into their component parts.

Given the following search query: "{query}"

Please analyze and break it down into:
1. Individual components/concepts (each major topic or subject)
2. Keywords for each component
3. Main concepts (the core ideas)
4. Relationships between components (how they connect)

Return your response in a structured format:
- For each component, provide:
  - The component name
  - A brief description
  - Relevant keywords (3-5 keywords)
- List the main concepts
- Describe the relationships between components

Format your response as JSON with this structure:
{{
  "components": [
    {{
      "component": "component name",
      "description": "brief description",
      "keywords": ["keyword1", "keyword2", "keyword3"]
    }}
  ],
  "main_concepts": ["concept1", "concept2"],
  "relationships": ["relationship description 1", "relationship description 2"]
}}

Query: {query}
"""

    try:
        response = model.generate_content(prompt)
        
        # Extract JSON from response
        response_text = response.text.strip()
        
        # Try to parse JSON from the response
        # Gemini might wrap JSON in markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            # Handle generic code blocks
            parts = response_text.split("```")
            if len(parts) >= 3:
                response_text = parts[1].strip()
                # Remove language identifier if present
                if response_text.startswith("json"):
                    response_text = response_text[4:].strip()
        
        # Try to extract JSON object if it's embedded in text
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(0)
        
        parsed_response = json.loads(response_text)
        
        # Build the response
        components = [
            QueryComponent(
                component=comp["component"],
                description=comp["description"],
                keywords=comp["keywords"]
            )
            for comp in parsed_response.get("components", [])
        ]
        
        return QueryDecompositionResponse(
            original_query=query,
            components=components,
            main_concepts=parsed_response.get("main_concepts", []),
            relationships=parsed_response.get("relationships", [])
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query with Gemini: {str(e)}"
        )


def rate_paper_relevance(paper: Paper, query_decomposition: QueryDecompositionResponse) -> str:
    """
    Uses Gemini to rate a paper's relevance against the decomposed query criteria.
    Returns: "Perfectly Relevant", "Relevant", or "Somewhat Relevant"
    """
    # Build the relevance criteria from decomposition
    components_text = "\n".join([
        f"- {comp.component}: {comp.description} (Keywords: {', '.join(comp.keywords)})"
        for comp in query_decomposition.components
    ])
    
    main_concepts_text = ", ".join(query_decomposition.main_concepts)
    relationships_text = "\n".join([f"- {rel}" for rel in query_decomposition.relationships])
    
    paper_info = f"Title: {paper.title}"
    if paper.abstract:
        paper_info += f"\nAbstract: {paper.abstract[:500]}"  # Limit abstract length
    
    prompt = f"""You are a research paper relevance evaluator. Rate how relevant a paper is to a given search query based on the decomposed criteria.

ORIGINAL QUERY: {query_decomposition.original_query}

RELEVANCE CRITERIA (from query decomposition):
Main Concepts: {main_concepts_text}

Components:
{components_text}

Relationships:
{relationships_text}

PAPER TO EVALUATE:
{paper_info}

Rate this paper's relevance to the original query and criteria. Choose ONE of these ratings:
1. "Perfectly Relevant" - The paper directly addresses all or most of the main concepts and components, with strong alignment to the relationships described.
2. "Relevant" - The paper addresses some of the main concepts and components, with moderate alignment to the query.
3. "Somewhat Relevant" - The paper has some connection to the query but only addresses a few concepts or has weak alignment.

Respond with ONLY the rating: "Perfectly Relevant", "Relevant", or "Somewhat Relevant" (no other text).
"""

    try:
        response = model.generate_content(prompt)
        rating = response.text.strip()
        
        # Clean up the response to ensure it matches one of the valid ratings
        rating = rating.replace('"', '').replace("'", "").strip()
        if "Perfectly Relevant" in rating:
            return "Perfectly Relevant"
        elif "Relevant" in rating and "Somewhat" not in rating:
            return "Relevant"
        elif "Somewhat Relevant" in rating:
            return "Somewhat Relevant"
        else:
            # Default fallback
            return "Somewhat Relevant"
    except Exception as e:
        # Default to "Somewhat Relevant" if rating fails
        return "Somewhat Relevant"


def collect_all_papers(most_relevant: Paper, forward_citations: List[PaperWithNestedCitations], 
                       backward_citations: List[PaperWithNestedCitations]) -> List[Paper]:
    """
    Collects all papers from the citation search (including nested ones).
    """
    all_papers = [most_relevant]
    
    for paper_with_nested in forward_citations:
        all_papers.append(paper_with_nested.paper)
        all_papers.extend(paper_with_nested.nested_forward_citations)
    
    for paper_with_nested in backward_citations:
        all_papers.append(paper_with_nested.paper)
        all_papers.extend(paper_with_nested.nested_backward_citations)
    
    return all_papers


# Semantic Scholar API Functions
def search_most_relevant_paper(query: str) -> Optional[Paper]:
    """
    Search for the most relevant paper using Semantic Scholar API.
    Returns the top result.
    Retries up to 10 times with 1 second delay between attempts.
    """
    url = f"{SEMANTIC_SCHOLAR_BASE_URL}/paper/search"
    params = {
        'query': query,
        'limit': 1,
        'fields': 'paperId,title,abstract,authors,year,citationCount,referenceCount,url'
    }
    
    max_retries = 10
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=SEMANTIC_SCHOLAR_HEADERS, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('data') and len(data['data']) > 0:
                paper_data = data['data'][0]
                return Paper(**paper_data)
            return None
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)  # Wait 1 second before retrying
                continue
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error searching Semantic Scholar after {max_retries} attempts: {str(e)}"
                )


def get_forward_citations(paper_id: str, limit: int = 3) -> List[Paper]:
    """
    Get papers that cite the given paper (forward citations).
    Retries up to 10 times with 1 second delay between attempts.
    """
    url = f"{SEMANTIC_SCHOLAR_BASE_URL}/paper/{paper_id}/citations"
    params = {
        'limit': limit,
        'fields': 'paperId,title,abstract,authors,year,citationCount,referenceCount,url'
    }
    
    max_retries = 10
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=SEMANTIC_SCHOLAR_HEADERS, params=params)
            response.raise_for_status()
            data = response.json()
            
            papers = []
            if data.get('data'):
                for item in data['data']:
                    if 'citingPaper' in item:
                        papers.append(Paper(**item['citingPaper']))
            return papers[:limit]
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)  # Wait 1 second before retrying
                continue
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error fetching forward citations after {max_retries} attempts: {str(e)}"
                )


def get_backward_citations(paper_id: str, limit: int = 3) -> List[Paper]:
    """
    Get papers that the given paper cites (backward citations/references).
    Retries up to 10 times with 1 second delay between attempts.
    """
    url = f"{SEMANTIC_SCHOLAR_BASE_URL}/paper/{paper_id}/references"
    params = {
        'limit': limit,
        'fields': 'paperId,title,abstract,authors,year,citationCount,referenceCount,url'
    }
    
    max_retries = 10
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=SEMANTIC_SCHOLAR_HEADERS, params=params)
            response.raise_for_status()
            data = response.json()
            
            papers = []
            if data.get('data'):
                for item in data['data']:
                    if 'citedPaper' in item:
                        papers.append(Paper(**item['citedPaper']))
            return papers[:limit]
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)  # Wait 1 second before retrying
                continue
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error fetching backward citations after {max_retries} attempts: {str(e)}"
                )


@app.post("/decompose-query", response_model=QueryDecompositionResponse)
async def decompose_search_query(request: SearchQueryRequest):
    """
    Decomposes a search query into its relevant components using Gemini.
    
    Example:
    - Input: "llms and their use in neural networks"
    - Output: Components like "LLMs", "Neural Networks", with keywords and relationships
    """
    return decompose_query(request.query)


@app.post("/citation-search", response_model=CitationSearchResponse)
async def citation_search(request: CitationSearchRequest):
    """
    Performs forward and backward citation search with one additional layer:
    1. Finds the most relevant paper for the query
    2. Gets forward citations (papers citing it) - limited to 3
    3. Gets backward citations (papers it cites) - limited to 3
    4. For each forward citation, gets its forward citations (nested forward) - limited to 3
    5. For each backward citation, gets its backward citations (nested backward) - limited to 3
    """
    # Step 1: Find most relevant paper
    most_relevant = search_most_relevant_paper(request.query)
    
    if not most_relevant:
        raise HTTPException(
            status_code=404,
            detail=f"No papers found for query: {request.query}"
        )
    
    # Step 2: Get forward citations (papers that cite the most relevant paper)
    forward_citations_level1 = get_forward_citations(most_relevant.paperId, request.forward_limit)
    
    # Step 3: Get backward citations (papers that the most relevant paper cites)
    backward_citations_level1 = get_backward_citations(most_relevant.paperId, request.backward_limit)
    
    # Step 4: For each forward citation, get its forward citations (nested layer - going further forward)
    forward_with_nested = []
    for paper in forward_citations_level1:
        nested_forward = get_forward_citations(paper.paperId, request.forward_limit)
        forward_with_nested.append(PaperWithNestedCitations(
            paper=paper,
            nested_forward_citations=nested_forward,
            nested_backward_citations=[]
        ))
    
    # Step 5: For each backward citation, get its backward citations (nested layer - going further backward)
    backward_with_nested = []
    for paper in backward_citations_level1:
        nested_backward = get_backward_citations(paper.paperId, request.backward_limit)
        backward_with_nested.append(PaperWithNestedCitations(
            paper=paper,
            nested_forward_citations=[],
            nested_backward_citations=nested_backward
        ))
    
    return CitationSearchResponse(
        query=request.query,
        most_relevant_paper=most_relevant,
        forward_citations=forward_with_nested,
        backward_citations=backward_with_nested,
        total_forward=len(forward_with_nested),
        total_backward=len(backward_with_nested)
    )


def get_cache_key(query: str, forward_limit: int, backward_limit: int) -> str:
    """Generate a cache key from query and parameters."""
    cache_string = f"{query.lower().strip()}:{forward_limit}:{backward_limit}"
    return hashlib.md5(cache_string.encode()).hexdigest()


@app.post("/citation-search-rated", response_model=RatedCitationSearchResponse)
async def citation_search_with_ratings(request: CitationSearchRequest):
    """
    Performs forward and backward citation search with relevance ratings:
    1. Decomposes the query using LLM
    2. Finds the most relevant paper
    3. Gets forward and backward citations with nested layers
    4. Rates all papers against the decomposed query criteria
    
    Results are cached based on query and limits.
    """
    # Check cache first
    cache_key = get_cache_key(request.query, request.forward_limit, request.backward_limit)
    if cache_key in _search_cache:
        cached_result = _search_cache[cache_key]
        # Reconstruct the response from cached data
        return RatedCitationSearchResponse(**cached_result)
    
    # Step 1: Decompose the query to get relevance criteria
    query_decomposition = decompose_query(request.query)
    
    # Step 2: Find most relevant paper - try full query first, then individual components
    most_relevant = search_most_relevant_paper(request.query)
    
    # If no results with full query, try searching individual components
    if not most_relevant:
        # Try main concepts first
        for concept in query_decomposition.main_concepts:
            most_relevant = search_most_relevant_paper(concept)
            if most_relevant:
                break
        
        # If still no results, try each component's description
        if not most_relevant:
            for component in query_decomposition.components:
                most_relevant = search_most_relevant_paper(component.description)
                if most_relevant:
                    break
        
        # If still no results, try component keywords
        if not most_relevant:
            for component in query_decomposition.components:
                for keyword in component.keywords:
                    most_relevant = search_most_relevant_paper(keyword)
                    if most_relevant:
                        break
                if most_relevant:
                    break
        
        # If still nothing found after trying all components
        if not most_relevant:
            raise HTTPException(
                status_code=404,
                detail=f"No papers found for query: {request.query} or any of its components"
            )
    
    # Step 3: Get forward citations (papers that cite the most relevant paper)
    forward_citations_level1 = get_forward_citations(most_relevant.paperId, request.forward_limit)
    
    # Step 4: Get backward citations (papers that the most relevant paper cites)
    backward_citations_level1 = get_backward_citations(most_relevant.paperId, request.backward_limit)
    
    # Step 5: For each forward citation, get its forward citations AND backward citations (nested layer - going both directions)
    forward_with_nested = []
    for paper in forward_citations_level1:
        nested_forward = get_forward_citations(paper.paperId, request.forward_limit)
        nested_backward = get_backward_citations(paper.paperId, request.backward_limit)
        forward_with_nested.append(PaperWithNestedCitations(
            paper=paper,
            nested_forward_citations=nested_forward,
            nested_backward_citations=nested_backward
        ))
    
    # Step 6: For each backward citation, get its backward citations AND forward citations (nested layer - going both directions)
    backward_with_nested = []
    for paper in backward_citations_level1:
        nested_backward = get_backward_citations(paper.paperId, request.backward_limit)
        nested_forward = get_forward_citations(paper.paperId, request.forward_limit)
        backward_with_nested.append(PaperWithNestedCitations(
            paper=paper,
            nested_forward_citations=nested_forward,
            nested_backward_citations=nested_backward
        ))
    
    # Step 7: Rate all papers
    # Rate the most relevant paper
    most_relevant_rating = rate_paper_relevance(most_relevant, query_decomposition)
    most_relevant = most_relevant.model_copy(update={"relevance_rating": most_relevant_rating})
    
    # Rate forward citations and their nested citations
    rated_forward_with_nested = []
    for paper_with_nested in forward_with_nested:
        paper_rating = rate_paper_relevance(paper_with_nested.paper, query_decomposition)
        rated_paper = paper_with_nested.paper.model_copy(update={"relevance_rating": paper_rating})
        
        rated_nested_forward = []
        for nested_paper in paper_with_nested.nested_forward_citations:
            nested_rating = rate_paper_relevance(nested_paper, query_decomposition)
            rated_nested_forward.append(nested_paper.model_copy(update={"relevance_rating": nested_rating}))
        
        rated_nested_backward = []
        for nested_paper in paper_with_nested.nested_backward_citations:
            nested_rating = rate_paper_relevance(nested_paper, query_decomposition)
            rated_nested_backward.append(nested_paper.model_copy(update={"relevance_rating": nested_rating}))
        
        rated_forward_with_nested.append(PaperWithNestedCitations(
            paper=rated_paper,
            nested_forward_citations=rated_nested_forward,
            nested_backward_citations=rated_nested_backward
        ))
    
    # Rate backward citations and their nested citations
    rated_backward_with_nested = []
    for paper_with_nested in backward_with_nested:
        paper_rating = rate_paper_relevance(paper_with_nested.paper, query_decomposition)
        rated_paper = paper_with_nested.paper.model_copy(update={"relevance_rating": paper_rating})
        
        rated_nested_backward = []
        for nested_paper in paper_with_nested.nested_backward_citations:
            nested_rating = rate_paper_relevance(nested_paper, query_decomposition)
            rated_nested_backward.append(nested_paper.model_copy(update={"relevance_rating": nested_rating}))
        
        rated_nested_forward = []
        for nested_paper in paper_with_nested.nested_forward_citations:
            nested_rating = rate_paper_relevance(nested_paper, query_decomposition)
            rated_nested_forward.append(nested_paper.model_copy(update={"relevance_rating": nested_rating}))
        
        rated_backward_with_nested.append(PaperWithNestedCitations(
            paper=rated_paper,
            nested_forward_citations=rated_nested_forward,
            nested_backward_citations=rated_nested_backward
        ))
    
    result = RatedCitationSearchResponse(
        query=request.query,
        query_decomposition=query_decomposition,
        most_relevant_paper=most_relevant,
        forward_citations=rated_forward_with_nested,
        backward_citations=rated_backward_with_nested,
        total_forward=len(rated_forward_with_nested),
        total_backward=len(rated_backward_with_nested)
    )
    
    # Cache the result (convert to dict for caching)
    _search_cache[cache_key] = result.model_dump()
    
    # Save cache to file
    save_cache(_search_cache)
    
    return result


@app.get("/paper/{paper_id}/citations")
async def get_paper_forward_citations(paper_id: str, limit: int = 3):
    """
    Get forward citations for a specific paper (papers that cite it).
    """
    citations = get_forward_citations(paper_id, limit)
    return {
        "paper_id": paper_id,
        "forward_citations": citations,
        "count": len(citations)
    }


@app.get("/paper/{paper_id}/references")
async def get_paper_backward_citations(paper_id: str, limit: int = 3):
    """
    Get backward citations for a specific paper (papers it cites).
    """
    citations = get_backward_citations(paper_id, limit)
    return {
        "paper_id": paper_id,
        "backward_citations": citations,
        "count": len(citations)
    }


@app.get("/search-paper")
async def search_paper(query: str):
    """
    Search for the most relevant paper for a given query.
    """
    paper = search_most_relevant_paper(query)
    if not paper:
        raise HTTPException(
            status_code=404,
            detail=f"No papers found for query: {query}"
        )
    return paper


@app.get("/cache/clear")
async def clear_cache():
    """Clear the search cache (both in-memory and file)."""
    global _search_cache
    cache_size = len(_search_cache)
    _search_cache.clear()
    
    # Also clear the cache file
    if CACHE_FILE.exists():
        try:
            CACHE_FILE.unlink()
        except IOError as e:
            print(f"Warning: Could not delete cache file: {e}")
    
    return {
        "message": "Cache cleared",
        "items_cleared": cache_size
    }


@app.get("/cache/stats")
async def cache_stats():
    """Get cache statistics."""
    return {
        "cache_size": len(_search_cache),
        "cached_queries": list(_search_cache.keys())[:10]  # Show first 10 keys
    }


@app.get("/")
async def root():
    return {
        "message": "Research Paper Search Query Decomposer API",
        "endpoints": {
            "/decompose-query": "POST - Decompose a search query into components",
            "/citation-search": "POST - Find most relevant paper and get forward/backward citations",
            "/citation-search-rated": "POST - Citation search with relevance ratings (cached)",
            "/search-paper": "GET - Search for most relevant paper",
            "/paper/{paper_id}/citations": "GET - Get forward citations for a paper",
            "/paper/{paper_id}/references": "GET - Get backward citations for a paper",
            "/cache/clear": "GET - Clear the search cache",
            "/cache/stats": "GET - Get cache statistics"
        }
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/list-models")
async def list_models():
    """
    Lists all available Gemini models that support generateContent.
    Use this to find the correct model name if you get a 404 error.
    """
    try:
        models = genai.list_models()
        available_models = [
            {
                "name": m.name,
                "display_name": m.display_name,
                "supported_methods": list(m.supported_generation_methods)
            }
            for m in models if 'generateContent' in m.supported_generation_methods
        ]
        return {
            "available_models": available_models,
            "count": len(available_models)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing models: {str(e)}"
        )

