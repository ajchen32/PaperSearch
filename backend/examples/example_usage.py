"""
Example script to demonstrate how to use the query decomposition API.
Make sure the FastAPI server is running before executing this script.
"""

import requests
import json

# API endpoint
BASE_URL = "http://localhost:8000"

def decompose_query(query: str):
    """Send a query to the decomposition API and print the results."""
    response = requests.post(
        f"{BASE_URL}/decompose-query",
        json={"query": query}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n{'='*60}")
        print(f"Original Query: {result['original_query']}")
        print(f"{'='*60}\n")
        
        print("Components:")
        for i, component in enumerate(result['components'], 1):
            print(f"\n  {i}. {component['component']}")
            print(f"     Description: {component['description']}")
            print(f"     Keywords: {', '.join(component['keywords'])}")
        
        print(f"\n\nMain Concepts: {', '.join(result['main_concepts'])}")
        
        print(f"\nRelationships:")
        for i, rel in enumerate(result['relationships'], 1):
            print(f"  {i}. {rel}")
        
        return result
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

if __name__ == "__main__":
    # Example queries
    queries = [
        "llms and their use in neural networks",
        "transformer architecture in natural language processing",
        "reinforcement learning for game playing"
    ]
    
    print("Testing Query Decomposition API\n")
    print("Make sure the FastAPI server is running at http://localhost:8000\n")
    
    for query in queries:
        decompose_query(query)
        print("\n" + "-"*60 + "\n")

