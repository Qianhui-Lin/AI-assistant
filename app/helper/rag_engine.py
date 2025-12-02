import chromadb
from chromadb.config import Settings
from openai import OpenAI
import os
from typing import List

client = OpenAI()

# Local DB directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
CHROMA_DIR = os.path.join(BASE_DIR, "data/chroma_db")

# Create or load persistent Chroma DB
# chroma_client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet",
#                                         persist_directory=CHROMA_DIR))

chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)


def normalise_level(level: str) -> str:
    """
    Normalise level strings so the API can accept things like:
    'ug', 'UG', 'Undergraduate' and map them to 'ug'.

    You can expand this mapping if needed.
    """
    if not level:
        raise ValueError("Level cannot be empty")

    l = level.strip().lower()

    mapping = {
        "ug": "ug",
        "undergraduate": "ug",
        "pgt": "pgt",
        "postgraduate_taught": "pgt",
        "pg_taught": "pgt",
        "pgr": "pgr",
        "postgraduate_research": "pgr",
        "pg_research": "pgr",
    }

    return mapping.get(l, l)  

def get_collection_name(level: str) -> str:
    """
    Return the Chroma collection name for a given level.
    Example: level='UG' -> 'handbook_ug'
    """
    norm = normalise_level(level)
    return f"handbook_{norm}"


def get_or_create_collection_for_level(level: str):
    """
    Convenience wrapper: directly get/create the collection for a level.
    """
    name = get_collection_name(level)
    return chroma_client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},  # cosine similarity
    )


def get_or_create_collection(collection_name: str):
    """
    Generic getter if you already know the collection name.
    """
    return chroma_client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

# --------------------------------
# 1. Chunk text
# --------------------------------
def chunk_text(text, chunk_size=2000, overlap=300):
    chunks:List[str] = []
    start = 0

    while start < len(text):
        chunk = text[start:start + chunk_size]
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


# --------------------------------
# 2. Compute embeddings
# --------------------------------
def embed_text(texts):
    resp = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )
    return [e.embedding for e in resp.data]


# --------------------------------
# 3. Build DB from text
# --------------------------------
def build_rag_from_text(text: str, collection_name: str)-> List[str]:
    chunks = chunk_text(text)
    embeddings = embed_text(chunks)

    ids = [f"chunk_{i}" for i in range(len(chunks))]


    col = get_or_create_collection(collection_name)
    col.upsert(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
    )

    print(f"Inserted {len(chunks)} chunks into ChromaDB collection '{collection_name}'")
    return chunks


# --------------------------------
# 4. Query DB
# --------------------------------
def search_similar_chunks(query: str, collection_name: str, top_k=5)-> List[str]:
    query_embed = embed_text([query])[0]
    col = get_or_create_collection(collection_name)

    results = col.query(
        query_embeddings=[query_embed],
        n_results=top_k,
    )

    return results["documents"][0]  # list of chunk strings
