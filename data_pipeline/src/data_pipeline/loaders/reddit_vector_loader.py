import os
from pymongo import MongoClient
import chromadb
import requests

def index_reddit_posts_to_chroma():
    # Connect Mongo
    mongo_client = MongoClient(host=os.getenv("MONGO_HOST", "localhost"), port=int(os.getenv("MONGO_PORT", 27017)))
    db = mongo_client[os.getenv("MONGO_DB", "ec_project")]
    reddit_coll = db[os.getenv("REDDIT_COLLECTION", "reddit_posts")]
    
    # Connect Chroma
    chroma_client = chromadb.HttpClient(host=os.getenv("CHROMA_HOST", "localhost"), port=int(os.getenv("CHROMA_PORT", 8000)))
    collection = chroma_client.get_or_create_collection(name="reddit_posts")
    
    # Fetch + embed
    posts = list(reddit_coll.find({}))
    print(f"Indexing {len(posts)} Reddit posts to Chroma...")
    
    for i, post in enumerate(posts):
        doc_text = f"{post.get('title', '')} {post.get('selftext', '')}"
        
        # Embed via Ollama
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        resp = requests.post(f"{ollama_url}/api/embed", json={"model": "embeddinggemma:latest", "input": doc_text})
        embedding = resp.json()["embeddings"][0] if resp.status_code == 200 else None
        
        if embedding:
            collection.upsert(ids=[post["post_id"]], metadatas=[{"subreddit": post.get("subreddit"), "url": post.get("url")}], embeddings=[embedding], documents=[doc_text])
        
        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(posts)} indexed")
    
    print(f"Done! {len(posts)} posts indexed in Chroma collection 'reddit_posts'")
    mongo_client.close()

if __name__ == "__main__":
    index_reddit_posts_to_chroma()