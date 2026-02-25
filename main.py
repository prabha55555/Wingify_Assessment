from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
import os
import uuid
from typing import Optional
from sqlalchemy.orm import Session

from crewai import Crew, Process
from agents import financial_analyst, verifier, investment_advisor, risk_assessor
from task import verification, analyze_financial_document, investment_analysis, risk_assessment

# Import Celery app and tasks
from celery_app import celery_app
from worker import analyze_document_task

# Import database
from database import get_db, check_db_connection
from models import DocumentStatus
import crud

# Validate required environment variables
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError(
        "OPENAI_API_KEY environment variable is not set. "
        "Please create a .env file with your OpenAI API key. "
        "See .env.example for reference."
    )

app = FastAPI(
    title="Financial Document Analyzer",
    description="AI-powered financial document analysis system using CrewAI multi-agent framework",
    version="1.0.0"
)

def run_crew(query: str, file_path: str = "data/sample.pdf"):
    """To run the whole crew with all agents and tasks"""
    financial_crew = Crew(
        agents=[verifier, financial_analyst, investment_advisor, risk_assessor],
        tasks=[verification, analyze_financial_document, investment_analysis, risk_assessment],
        process=Process.sequential,
        verbose=True,
    )
    
    result = financial_crew.kickoff({'query': query})
    return result

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Financial Document Analyzer API is running",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/upload-document/ (POST) - Submit document for async analysis",
            "status": "/task-status/{task_id} (GET) - Check task status",
            "result": "/task-result/{task_id} (GET) - Get analysis result",
            "sync": "/analyze-sync/ (POST) - Synchronous analysis (blocks until complete)"
        }
    }


@app.post("/upload-document/")
async def upload_document(
    file: UploadFile = File(...),
    query: str = Form(default="Analyze this financial document for investment insights"),
    user_id: Optional[str] = Form(default=None),
    db: Session = Depends(get_db)
):
    """
    Upload a financial document for asynchronous analysis.
    Returns a task ID that can be used to check status and retrieve results.
    
    This endpoint uses Celery queue for concurrent processing and saves metadata to database.
    """
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Validate file size (max 50MB)
    file_content = await file.read()
    max_size = int(os.getenv("MAX_FILE_SIZE_MB", "50")) * 1024 * 1024
    if len(file_content) > max_size:
        raise HTTPException(
            status_code=400, 
            detail=f"File size exceeds {max_size // (1024*1024)}MB limit"
        )
    
    file_id = str(uuid.uuid4())
    file_path = f"data/financial_document_{file_id}.pdf"
    
    try:
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        # Save uploaded file
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Validate query
        if query == "" or query is None:
            query = "Analyze this financial document for investment insights"
        
        # Get or create user in database
        user_db = None
        if user_id:
            user_db = crud.get_or_create_user(db, user_id)
        
        # Create document record in database
        document = crud.create_document(
            db=db,
            filename=f"financial_document_{file_id}.pdf",
            original_filename=file.filename,
            file_path=file_path,
            user_id=user_db.id if user_db else None,
            file_size=len(file_content),
            query=query,
            task_id=None  # Will be updated after task creation
        )
        
        # Create analysis record
        analysis = crud.create_analysis(
            db=db,
            document_id=document.id,
            status="pending"
        )
        
        # Submit task to Celery queue
        task = analyze_document_task.apply_async(
            args=[query.strip(), file_path, user_id, document.id]
        )
        
        # Update document with task ID
        crud.update_document_task_id(db, document.id, task.id)
        
        # Update analysis with task ID
        if analysis:
            analysis.task_id = task.id
            db.commit()
        
        return {
            "status": "queued",
            "message": "Document uploaded successfully and queued for analysis",
            "task_id": task.id,
            "document_id": str(document.document_id),
            "file_id": file_id,
            "filename": file.filename,
            "query": query,
            "check_status": f"/task-status/{task.id}",
            "get_result": f"/task-result/{task.id}"
        }
        
    except Exception as e:
        # Clean up file if task submission fails
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass
        raise HTTPException(
            status_code=500, 
            detail=f"Error submitting analysis task: {str(e)}"
        )


@app.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """
    Check the status of an analysis task.
    
    Returns:
        - PENDING: Task is waiting in queue
        - PROCESSING: Task is being processed
        - SUCCESS: Task completed successfully
        - FAILURE: Task failed
    """
    
    task_result = celery_app.AsyncResult(task_id)
    
    if task_result.state == "PENDING":
        response = {
            "task_id": task_id,
            "status": "pending",
            "message": "Task is waiting in queue"
        }
    elif task_result.state == "PROCESSING":
        response = {
            "task_id": task_id,
            "status": "processing",
            "message": "Task is being processed",
            "meta": task_result.info
        }
    elif task_result.state == "SUCCESS":
        response = {
            "task_id": task_id,
            "status": "completed",
            "message": "Analysis completed successfully",
            "result_available": True,
            "get_result": f"/task-result/{task_id}"
        }
    elif task_result.state == "FAILURE":
        response = {
            "task_id": task_id,
            "status": "failed",
            "message": "Task failed",
            "error": str(task_result.info)
        }
    else:
        response = {
            "task_id": task_id,
            "status": task_result.state.lower(),
            "message": f"Task state: {task_result.state}"
        }
    
    return response


@app.get("/task-result/{task_id}")
async def get_task_result(task_id: str):
    """
    Retrieve the result of a completed analysis task.
    Returns 404 if task is not complete or doesn't exist.
    """
    
    task_result = celery_app.AsyncResult(task_id)
    
    if task_result.state == "PENDING":
        raise HTTPException(
            status_code=404,
            detail="Task not found or still pending. Check /task-status/{task_id} first."
        )
    elif task_result.state == "PROCESSING":
        raise HTTPException(
            status_code=202,
            detail="Task is still being processed. Please check back later."
        )
    elif task_result.state == "SUCCESS":
        result = task_result.result
        
        # Clean up the file after successful retrieval
        if "file_path" in result and os.path.exists(result["file_path"]):
            try:
                os.remove(result["file_path"])
                print(f"Cleaned up file: {result['file_path']}")
            except OSError as e:
                print(f"Warning: Could not delete file {result['file_path']}: {str(e)}")
        
        return result
    elif task_result.state == "FAILURE":
        raise HTTPException(
            status_code=500,
            detail=f"Task failed: {str(task_result.info)}"
        )
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected task state: {task_result.state}"
        )


@app.post("/analyze-sync/")
async def analyze_document_endpoint(
    file: UploadFile = File(...),
    query: str = Form(default="Analyze this financial document for investment insights")
):
    """
    Synchronous analysis endpoint - blocks until analysis is complete.
    Use /upload-document/ for async processing with queue system.
    
    This endpoint processes the document immediately and returns the full analysis.
    For production with high load, prefer the async /upload-document/ endpoint.
    """
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Validate file size (max 50MB)
    file_content = await file.read()
    if len(file_content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 50MB limit")
    
    file_id = str(uuid.uuid4())
    file_path = f"data/financial_document_{file_id}.pdf"
    
    try:
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        # Save uploaded file
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Validate query
        if query == "" or query is None:
            query = "Analyze this financial document for investment insights"
            
        # Process the financial document with all analysts
        response = run_crew(query=query.strip(), file_path=file_path)
        
        return {
            "status": "success",
            "query": query,
            "analysis": str(response),
            "file_processed": file.filename
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing financial document: {str(e)}")
    
    finally:
        # Clean up uploaded file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError as e:
                print(f"Warning: Could not delete temporary file {file_path}: {str(e)}")


@app.get("/user/{user_id}/documents")
async def get_user_documents(user_id: str, limit: int = 10, db: Session = Depends(get_db)):
    """
    Get all documents uploaded by a specific user.
    Returns document metadata and analysis status.
    """
    user = crud.get_user_by_user_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    documents = crud.get_documents_by_user(db, user.id, limit=limit)
    
    return {
        "user_id": user_id,
        "total_documents": len(documents),
        "documents": [
            {
                "document_id": str(doc.document_id),
                "filename": doc.original_filename,
                "status": doc.status.value,
                "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                "processed_at": doc.processed_at.isoformat() if doc.processed_at else None,
                "query": doc.query,
                "task_id": doc.task_id
            }
            for doc in documents
        ]
    }


@app.get("/stats")
async def get_statistics(db: Session = Depends(get_db)):
    """Get system statistics"""
    return {
        "total_documents": crud.get_total_documents(db),
        "total_analyses": crud.get_total_analyses(db),
        "system_status": "operational"
    }


if __name__ == "__main__":
    import uvicorn
    
    # Check database connection on startup
    print("Checking database connection...")
    if check_db_connection():
        print("✅ Database connected successfully")
    else:
        print("⚠️  Warning: Database connection failed. Some features may not work.")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)