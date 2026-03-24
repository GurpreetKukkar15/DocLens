import os
import uuid
import pymupdf
import pytesseract
from PIL import Image
from io import BytesIO
from qdrant_client.models import Distance, VectorParams, PointStruct, PayloadSchemaType

from app.config import (
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    EMBEDDING_DIMENSIONS,
    CHUNK_SIZE,
    CHUNK_OVERLAP
)
from app.core.clients import gemini_client, qdrant_client

def ensure_collection():
    existing = [c.name for c in qdrant_client.get_collections().collections]
    if COLLECTION_NAME not in existing:
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIMENSIONS, distance=Distance.COSINE)
        )
        qdrant_client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="filename",
            field_schema=PayloadSchemaType.KEYWORD
        )


def extract_text_from_pdf(file_bytes: bytes, filename: str) -> list[dict]:
    pages = []
    doc = pymupdf.open(stream=file_bytes, filetype="pdf")

    for page_num, page in enumerate(doc, start=1):
        text = page.get_text().strip()

        if not text:
            pix = page.get_pixmap()
            img = Image.open(BytesIO(pix.tobytes("png")))
            text = pytesseract.image_to_string(img).strip()

        if text:
            pages.append({
                "page": page_num,
                "text": text,
                "filename": filename
            })

    return pages


def chunk_text(text: str, page: int, filename: str) -> list[dict]:
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + CHUNK_SIZE
        chunk_words = words[start:end]
        chunk_content = " ".join(chunk_words)

        chunks.append({
            "text": chunk_content,
            "page": page,
            "filename": filename,
            "chunk_index": len(chunks)
        })

        start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks


def embed_text(text: str) -> list[float]:
    import time
    max_retries = 5
    for attempt in range(max_retries):
        try:
            result = gemini_client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=text
            )
            return result.embeddings[0].values
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait_time = 30 * (attempt + 1)
                print(f"Rate limited. Waiting {wait_time}s before retry {attempt+1}/{max_retries}")
                time.sleep(wait_time)
            else:
                raise e
    raise Exception("Max retries exceeded for embedding")

def ingest_document(file_bytes: bytes, filename: str) -> dict:
    ensure_collection()

    pages = extract_text_from_pdf(file_bytes, filename)

    if not pages:
        return {"status": "error", "message": "No text could be extracted"}

    all_chunks = []
    for page_data in pages:
        chunks = chunk_text(page_data["text"], page_data["page"], filename)
        all_chunks.extend(chunks)

    points = []
    for i, chunk in enumerate(all_chunks):
        print(f"Embedding chunk {i+1}/{len(all_chunks)} from {filename}")
        vector = embed_text(chunk["text"])
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "text": chunk["text"],
                "filename": filename,
                "page": chunk["page"],
                "chunk_index": chunk["chunk_index"]
            }
        )
        points.append(point)

    qdrant_client.upsert(collection_name=COLLECTION_NAME, points=points)

    return {
        "status": "success",
        "filename": filename,
        "pages": len(pages),
        "chunks": len(all_chunks)
    }
