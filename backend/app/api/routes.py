from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from app.models.schemas import QueryRequest
from app.services.ingestion import ingest_document
from app.services.query import process_query, get_all_documents

router = APIRouter()


@router.get("/health")
async def health_check():
    """Check if the API is running"""
    return {"status": "ok", "message": "DocLens API is running"}


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Receive a PDF and ingest it into Qdrant"""
    try:
        # Validate file type
        if not file.filename.endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )

        # Read file bytes
        file_bytes = await file.read()

        # Run ingestion pipeline
        result = ingest_document(file_bytes, file.filename)

        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])

        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query")
async def query_documents(request: QueryRequest):
    """Process a user query against all uploaded documents"""
    try:
        if not request.query.strip():
            raise HTTPException(
                status_code=400,
                detail="Query cannot be empty"
            )

        result = process_query(request.query)

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents")
async def list_documents():
    """Return list of all uploaded documents"""
    try:
        filenames = get_all_documents()
        return JSONResponse(content={
            "documents": filenames,
            "count": len(filenames)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))