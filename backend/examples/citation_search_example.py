"""
Example script demonstrating forward/backward citation search using Semantic Scholar API.
Make sure the FastAPI server is running before executing this script.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def citation_search_example():
    """Example of the full citation search workflow."""
    query = "transformer architecture attention mechanism"
    
    print(f"Searching for papers related to: {query}\n")
    print("=" * 70)
    
    # Perform citation search
    response = requests.post(
        f"{BASE_URL}/citation-search",
        json={
            "query": query,
            "forward_limit": 3,
            "backward_limit": 3
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        
        print(f"\nMost Relevant Paper:")
        print(f"  Title: {result['most_relevant_paper']['title']}")
        print(f"  Paper ID: {result['most_relevant_paper']['paperId']}")
        if result['most_relevant_paper'].get('year'):
            print(f"  Year: {result['most_relevant_paper']['year']}")
        if result['most_relevant_paper'].get('citationCount'):
            print(f"  Citations: {result['most_relevant_paper']['citationCount']}")
        
        print(f"\n\nForward Citations (Papers citing this paper): {result['total_forward']}")
        for i, paper_data in enumerate(result['forward_citations'], 1):
            paper = paper_data['paper']
            print(f"\n  {i}. {paper['title']}")
            if paper.get('year'):
                print(f"     Year: {paper['year']}")
            if paper.get('citationCount'):
                print(f"     Citations: {paper['citationCount']}")
            
            # Show nested forward citations (papers that cite this forward citation - one more layer forward)
            nested_forward = paper_data.get('nested_forward_citations', [])
            if nested_forward:
                print(f"     └─ Nested Forward Citations ({len(nested_forward)}):")
                for j, nested_paper in enumerate(nested_forward, 1):
                    print(f"        {j}. {nested_paper['title']}")
                    if nested_paper.get('year'):
                        print(f"           Year: {nested_paper['year']}")
        
        print(f"\n\nBackward Citations (Papers cited by this paper): {result['total_backward']}")
        for i, paper_data in enumerate(result['backward_citations'], 1):
            paper = paper_data['paper']
            print(f"\n  {i}. {paper['title']}")
            if paper.get('year'):
                print(f"     Year: {paper['year']}")
            if paper.get('citationCount'):
                print(f"     Citations: {paper['citationCount']}")
            
            # Show nested backward citations (papers that this backward citation cites - one more layer backward)
            nested_backward = paper_data.get('nested_backward_citations', [])
            if nested_backward:
                print(f"     └─ Nested Backward Citations ({len(nested_backward)}):")
                for j, nested_paper in enumerate(nested_backward, 1):
                    print(f"        {j}. {nested_paper['title']}")
                    if nested_paper.get('year'):
                        print(f"           Year: {nested_paper['year']}")
        
        return result
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None


def search_paper_example():
    """Example of searching for a single paper."""
    query = "BERT language model"
    
    print(f"\n\nSearching for paper: {query}")
    print("=" * 70)
    
    response = requests.get(
        f"{BASE_URL}/search-paper",
        params={"query": query}
    )
    
    if response.status_code == 200:
        paper = response.json()
        print(f"\nTitle: {paper['title']}")
        print(f"Paper ID: {paper['paperId']}")
        if paper.get('abstract'):
            print(f"Abstract: {paper['abstract'][:200]}...")
        return paper
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None


def citation_search_rated_example():
    """Example of citation search with relevance ratings."""
    query = "transformer architecture attention mechanism"
    
    print(f"\n\nSearching for papers with relevance ratings: {query}")
    print("=" * 70)
    
    # Perform rated citation search
    response = requests.post(
        f"{BASE_URL}/citation-search-rated",
        json={
            "query": query,
            "forward_limit": 3,
            "backward_limit": 3
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        
        print(f"\nQuery Decomposition:")
        print(f"  Main Concepts: {', '.join(result['query_decomposition']['main_concepts'])}")
        print(f"  Components: {len(result['query_decomposition']['components'])}")
        
        print(f"\n\nMost Relevant Paper:")
        paper = result['most_relevant_paper']
        print(f"  Title: {paper['title']}")
        print(f"  Relevance Rating: {paper.get('relevance_rating', 'Not rated')}")
        if paper.get('year'):
            print(f"  Year: {paper['year']}")
        
        print(f"\n\nForward Citations (Papers citing this paper): {result['total_forward']}")
        for i, paper_data in enumerate(result['forward_citations'], 1):
            paper = paper_data['paper']
            print(f"\n  {i}. {paper['title']}")
            print(f"     Relevance Rating: {paper.get('relevance_rating', 'Not rated')}")
            if paper.get('year'):
                print(f"     Year: {paper['year']}")
            
            # Show nested forward citations with ratings
            nested_forward = paper_data.get('nested_forward_citations', [])
            if nested_forward:
                print(f"     └─ Nested Forward Citations ({len(nested_forward)}):")
                for j, nested_paper in enumerate(nested_forward, 1):
                    print(f"        {j}. {nested_paper['title']}")
                    print(f"           Relevance Rating: {nested_paper.get('relevance_rating', 'Not rated')}")
                    if nested_paper.get('year'):
                        print(f"           Year: {nested_paper['year']}")
        
        print(f"\n\nBackward Citations (Papers cited by this paper): {result['total_backward']}")
        for i, paper_data in enumerate(result['backward_citations'], 1):
            paper = paper_data['paper']
            print(f"\n  {i}. {paper['title']}")
            print(f"     Relevance Rating: {paper.get('relevance_rating', 'Not rated')}")
            if paper.get('year'):
                print(f"     Year: {paper['year']}")
            
            # Show nested backward citations with ratings
            nested_backward = paper_data.get('nested_backward_citations', [])
            if nested_backward:
                print(f"     └─ Nested Backward Citations ({len(nested_backward)}):")
                for j, nested_paper in enumerate(nested_backward, 1):
                    print(f"        {j}. {nested_paper['title']}")
                    print(f"           Relevance Rating: {nested_paper.get('relevance_rating', 'Not rated')}")
                    if nested_paper.get('year'):
                        print(f"           Year: {nested_paper['year']}")
        
        return result
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None


if __name__ == "__main__":
    print("Citation Search Example")
    print("=" * 70)
    print("Make sure the FastAPI server is running at http://localhost:8000\n")
    
    # Full citation search with ratings
    citation_search_rated_example()
    
    # Regular citation search (without ratings)
    # citation_search_example()
    
    # Single paper search
    # search_paper_example()

