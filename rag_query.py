"""Natural-language query interface (RAG) over the data-protection policy DB.

Pipeline:  question -> retrieve top chunks from Chroma -> build a grounded
prompt -> Groq LLM -> answer with source attribution.

Run Embedding_Setup.py first so ./chroma_db is populated.
"""

import os

from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions
from groq import Groq

# --- Config -----------------------------------------------------------------
MODEL_NAME = "all-MiniLM-L12-v2"          # must match Embedding_Setup.py
LLM_MODEL = "llama-3.3-70b-versatile"     # Groq-hosted model
N_RESULTS = 5                             # how many chunks to retrieve (per country when filtered)
MIN_SIMILARITY = 0.15                     # drop chunks weaker than this (cosine)

# --- Setup ------------------------------------------------------------------
load_dotenv()
groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])

embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=MODEL_NAME
)
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_collection(
    name="documents",
    embedding_function=embedding_fn,
)

# Distinct country names actually present in the collection, derived at startup
# so detection stays accurate if the corpus changes. Aliases map common ways a
# user might name a country to the exact Subject value stored in the metadata.
KNOWN_COUNTRIES = sorted(
    {m["Subject"] for m in collection.get(include=["metadatas"])["metadatas"] if m.get("Subject")}
)
COUNTRY_ALIASES = {
    "united states of america": ["united states", "u.s.", "u.s.a", "usa", "america"],
}


def detect_countries(question):
    """Return the known countries explicitly named in the question."""
    q = question.lower()
    found = []
    for country in KNOWN_COUNTRIES:
        names = [country.lower()] + COUNTRY_ALIASES.get(country.lower(), [])
        if any(name in q for name in names):
            found.append(country)
    return found


def _rows_to_chunks(results):
    """Turn a chromadb query result into similarity-filtered chunk dicts."""
    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        similarity = 1 - dist  # cosine space: distance = 1 - similarity
        if similarity >= MIN_SIMILARITY:
            chunks.append({"text": doc, "meta": meta, "similarity": similarity})
    return chunks


def retrieve(question, n_results=N_RESULTS):
    """Return the most relevant chunks as a list of dicts, best first.

    If the question names one or more known countries, retrieval is restricted
    to those jurisdictions (a metadata filter on `Subject`). For comparative
    questions naming several countries, each country is queried separately so
    every named jurisdiction is guaranteed representation instead of competing
    for the same slots. Chunks below MIN_SIMILARITY are dropped so weak matches
    aren't fed to the model as evidence.
    """
    countries = detect_countries(question)

    if countries:
        chunks = []
        for country in countries:
            results = collection.query(
                query_texts=[question],
                n_results=n_results,
                where={"Subject": country},
                include=["documents", "metadatas", "distances"],
            )
            chunks.extend(_rows_to_chunks(results))
        chunks.sort(key=lambda c: c["similarity"], reverse=True)
        return chunks

    results = collection.query(
        query_texts=[question],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )
    return _rows_to_chunks(results)


def build_context(chunks):
    """Format retrieved chunks into a numbered, citable context block."""
    blocks = []
    for i, c in enumerate(chunks, start=1):
        m = c["meta"]
        blocks.append(
            f"[{i}] Country: {m['Subject']} | Source: {m['Source']} | "
            f"URL: {m['filepath']}\n{c['text']}"
        )
    return "\n\n".join(blocks)


SYSTEM_PROMPT = (
    "You are a regulatory-compliance assistant. Answer the user's question "
    "USING ONLY the numbered context passages provided. Do not use outside "
    "knowledge. If the context does not contain the answer, reply exactly: "
    "\"I don't have enough information in the provided documents to answer that.\" "
    "Cite the passages you used with their country name and bracket number, "
    "e.g. (Iceland [1]). Be concise and factual."
)


def answer(question):
    """Run the full RAG pipeline for one question and return the LLM answer."""
    chunks = retrieve(question)
    if not chunks:
        return (
            "I don't have enough information in the provided documents to answer that.",
            [],
        )

    context = build_context(chunks)
    user_prompt = (
        f"Context passages:\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer using only the passages above, and cite your sources."
    )

    response = groq_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,  # low temperature keeps answers grounded
    )
    return response.choices[0].message.content, chunks


def ask(question):
    """End-to-end entry point for UIs.

    Returns a dict: {"answer": str, "sources": [str, ...]} where each source
    is a human-readable citation line for display.
    """
    reply, chunks = answer(question)
    sources = [
        f"[{i}] {c['meta']['Subject']} (similarity {c['similarity']:.2f}) — "
        f"{c['meta']['filepath']}"
        for i, c in enumerate(chunks, start=1)
    ]
    return {"answer": reply, "sources": sources}


if __name__ == "__main__":
    question = "What is Iceland's Data Privacy Policy?"
    print(f"Q: {question}\n")

    result = ask(question)
    print("A:", result["answer"])

    print("\nRetrieved sources:")
    for line in result["sources"]:
        print(f"  {line}")
