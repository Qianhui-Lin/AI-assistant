import chromadb
from chromadb.config import Settings
from openai import OpenAI
import os

client = OpenAI()

# Local DB directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
CHROMA_DIR = os.path.join(BASE_DIR, "data/chroma_db")

# Create or load persistent Chroma DB
# chroma_client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet",
#                                         persist_directory=CHROMA_DIR))

chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)

collection = chroma_client.get_or_create_collection(
    name="handbook",
    metadata={"hnsw:space": "cosine"}  # similarity metric
)


# --------------------------------
# 1. Chunk text
# --------------------------------
def chunk_text(text, chunk_size=2000, overlap=300):
    chunks = []
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
def build_rag_from_text(text):
    chunks = chunk_text(text)
    embeddings = embed_text(chunks)

    ids = [f"chunk_{i}" for i in range(len(chunks))]

    collection.upsert(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
    )

    print(f"Inserted {len(chunks)} chunks into ChromaDB")
    # chroma_client.persist()
    return chunks


# --------------------------------
# 4. Query DB
# --------------------------------
def search_similar_chunks(query, top_k=5):
    query_embed = embed_text([query])[0]

    results = collection.query(
        query_embeddings=[query_embed],
        n_results=top_k
    )

    return results["documents"][0]  # list of chunk strings
