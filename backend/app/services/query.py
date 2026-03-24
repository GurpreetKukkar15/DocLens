from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.config import (
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    CHAT_MODEL
)
from app.core.clients import gemini_client, groq_client, qdrant_client


def embed_query(text: str) -> list[float]:
    result = gemini_client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text
    )
    return result.embeddings[0].values

def get_all_documents() -> list[str]:
    results = qdrant_client.scroll(
        collection_name=COLLECTION_NAME,
        limit=1000,
        with_payload=True,
        with_vectors=False
    )
    filenames = list(set(
        point.payload["filename"] for point in results[0]
    ))
    return filenames


def search_per_document(query_vector: list[float], filename: str) -> list[dict]:
    results = qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=3,
        query_filter=Filter(
            must=[
                FieldCondition(
                    key="filename",
                    match=MatchValue(value=filename)
                )
            ]
        ),
        with_payload=True
    )
    return [
        {
            "text": r.payload["text"],
            "page": r.payload["page"],
            "chunk_index": r.payload["chunk_index"],
            "score": r.score
        }
        for r in results.points
    ]


def answer_per_document(query: str, chunks: list[dict], filename: str) -> dict:
    if not chunks:
        return {
            "filename": filename,
            "answer": "No relevant content found",
            "citation": "N/A"
        }

    context = "\n\n".join([
        f"[Page {c['page']}]: {c['text']}" for c in chunks
    ])

    prompt = f"""You are analyzing a single document called "{filename}".

Using ONLY the following excerpts from this document, answer the question.
If the document doesn't contain relevant information, say "Not found in this document."

Document excerpts:
{context}

Question: {query}

Format your response exactly like this:
ANSWER: <your answer here>
CITATION: Page <number>"""

    response = groq_client.chat.completions.create(
    model=CHAT_MODEL,
    messages=[{"role": "user", "content": prompt}],
    max_tokens=300
)
    text = response.choices[0].message.content.strip()

    answer = "Could not parse answer"
    citation = "N/A"

    for line in text.split("\n"):
        if line.startswith("ANSWER:"):
            answer = line.replace("ANSWER:", "").strip()
        elif line.startswith("CITATION:"):
            citation = line.replace("CITATION:", "").strip()

    return {
        "filename": filename,
        "answer": answer,
        "citation": citation
    }


def identify_themes(query: str, doc_answers: list[dict]) -> str:
    answers_text = "\n\n".join([
        f"Document: {d['filename']}\nAnswer: {d['answer']}\nCitation: {d['citation']}"
        for d in doc_answers
        if d['answer'] not in ["No relevant content found", "Not found in this document."]
    ])

    if not answers_text:
        return "No common themes found — the documents do not contain relevant information for this query."

    prompt = f"""You are a research analyst. Below are answers extracted from multiple documents.

Query: {query}

Document Answers:
{answers_text}

Identify 2-4 common themes. Format exactly like this:
THEME 1 - <Theme Title>:
<2-3 sentence synthesis>
Supporting documents: DOC1, DOC2

THEME 2 - <Theme Title>:
<2-3 sentence synthesis>
Supporting documents: DOC3, DOC4"""

    response = groq_client.chat.completions.create(
    model=CHAT_MODEL,
    messages=[{"role": "user", "content": prompt}],
    max_tokens=1000
    )
    return response.choices[0].message.content.strip()


def process_query(query: str) -> dict:
    query_vector = embed_query(query)
    filenames = get_all_documents()

    if not filenames:
        return {"error": "No documents uploaded yet"}

    doc_answers = []
    for filename in filenames:
        chunks = search_per_document(query_vector, filename)
        answer = answer_per_document(query, chunks, filename)
        doc_answers.append(answer)

    themes = identify_themes(query, doc_answers)

    return {
        "query": query,
        "doc_answers": doc_answers,
        "themes": themes
    }