import pandas as pd
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.utils import embedding_functions

MODEL_NAME = "all-MiniLM-L12-v2"

# all-MiniLM-L12-v2 truncates input at 128 tokens (~450-500 chars). Anything
# longer is silently cut off before embedding, so we split each policy into
# chunks that fit. ~450 chars keeps us safely under the limit; 75-char overlap
# preserves sentences that straddle a chunk boundary.
CHUNK_SIZE = 450
CHUNK_OVERLAP = 75


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split text into overlapping chunks, preferring sentence boundaries.

    Whitespace is normalized first. Short text returns a single chunk. For
    longer text we take a window of chunk_size chars, then back up to the last
    sentence end ('. ') in the window so chunks don't cut mid-sentence.
    """
    text = " ".join(text.split())
    if len(text) <= chunk_size:
        return [text] if text else []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        window = text[start:end]
        if end < len(text):
            boundary = window.rfind(". ")
            if boundary > chunk_size * 0.5:  # only if it's not too early
                end = start + boundary + 1
                window = text[start:end]
        chunk = window.strip()
        if chunk:
            chunks.append(chunk)
        # end is always >= start + chunk_size*0.5, so this makes forward progress.
        start = end - overlap
    return chunks


# Load a sentence transformer model
model = SentenceTransformer(MODEL_NAME)
model.save("./model")  # save into a subfolder, not the project root

# Chroma's built-in embedding function wraps the same model so that the
# vector store can embed documents/queries on its own.
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=MODEL_NAME
)

# Example embeddings
sentences = ["This is an example sentence", "Each sentence is converted"]
embeddings = model.encode(sentences)
print(f"Embedded {len(sentences)} sentences -> shape {embeddings.shape}")

# Create a persistent Chroma collection that uses this model for embedding.
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(
    name="documents",
    embedding_function=embedding_fn,
    metadata={"hnsw:space": "cosine"},
)
print(f"Chroma collection '{collection.name}' ready ({collection.count()} docs).")



# Load the Country Data Protection Policies dataset (CSV is in the project root).
data_protection = pd.read_csv("country_plus_policies.csv")
print("Sample Data:\n", data_protection.head())

# Chunk each policy's Body so the full text gets embedded (not just the first
# 128 tokens). Each chunk becomes its own entry, carrying the row's metadata
# plus its position so we can trace a result back to its source row.
documents = []
metadatas = []
ids = []
for row_idx, row in data_protection.iterrows():
    chunks = chunk_text(str(row["Body"]))
    for chunk_idx, chunk in enumerate(chunks):
        documents.append(chunk)
        metadatas.append(
            {
                "Subject": row["Subject"],
                "Date": row["Date"],
                "Source": row["Source"],
                "filepath": row["filepath"],
                "row": int(row_idx),
                "chunk": chunk_idx,
            }
        )
        ids.append(f"row{row_idx}_chunk{chunk_idx}")

print(f"Chunked {len(data_protection)} policies into {len(documents)} chunks.")

# Add to the collection. The collection's embedding_function (set above) embeds
# each chunk automatically. upsert avoids "duplicate id" errors on re-runs.
collection.upsert(documents=documents, metadatas=metadatas, ids=ids)

# PersistentClient writes to ./chroma_db automatically — no .persist() call needed.
print(f"Stored {collection.count()} chunks in collection '{collection.name}'.")

# Querying the Regulatory Database. query() returns documents, metadatas and
# distances together — there is no separate similarity_search call in chromadb.
query = "What are the data protection policies in Iceland?"
results = collection.query(
    query_texts=[query],
    n_results=3,
    include=["documents", "metadatas", "distances"],
)

print("Query Results (higher similarity = more relevant):")
for doc, meta, dist in zip(
    results["documents"][0],
    results["metadatas"][0],
    results["distances"][0],
):
    # With cosine space, chromadb returns cosine distance (1 - similarity).
    similarity = 1 - dist
    print(f"- [{similarity:.4f}] {meta['Subject']} ({meta['Date']}): {doc[:100]}...")
