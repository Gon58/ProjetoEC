from src.db.vectorial import search_documents

def search_vector_db(query: str, n_results: int = 2) -> str:
    """
    Searches the vector database for Steam user reviews about CS skins, market, and prices.
    Use this tool when the user asks for opinions, sentiment, or qualitative data about items.
    """
    result = search_documents(
        query=query,
        collection_name="steam_reviews",
        n_results=n_results
    )
    
    if result["status"] != "success" or result["total_results"] == 0:
        return "No relevant reviews found."
        
    # Format the retrieved documents into a single string for the LLM
    texts = [match["text"] for match in result["results"]]
    return "\n---\n".join(texts)