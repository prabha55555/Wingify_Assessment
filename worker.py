"""
Celery Worker Tasks for Financial Document Analysis

This module contains Celery tasks that run the CrewAI analysis asynchronously.
Workers process documents in the background, allowing the API to handle multiple requests concurrently.
"""

import os
import traceback
from datetime import datetime
from celery import Task
from celery_app import celery_app
from crewai import Crew, Process

# Import agents and tasks
from agents import financial_analyst, verifier, investment_advisor, risk_assessor
from task import verification, analyze_financial_document, investment_analysis, risk_assessment

# Import database
from database import SessionLocal
from models import DocumentStatus
import crud


class CallbackTask(Task):
    """Custom Task class that provides task lifecycle hooks"""
    
    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds"""
        print(f"Task {task_id} completed successfully")
        return super().on_success(retval, task_id, args, kwargs)
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails"""
        print(f"Task {task_id} failed: {exc}")
        return super().on_failure(exc, task_id, args, kwargs, einfo)


@celery_app.task(
    base=CallbackTask,
    bind=True,
    name="worker.analyze_document_task",
    max_retries=3,
    default_retry_delay=60
)
def analyze_document_task(self, query: str, file_path: str, user_id: str = None, document_id: int = None):
    """
    Asynchronous task to analyze a financial document using CrewAI agents.
    
    Args:
        self: Celery task instance (bound)
        query (str): User's analysis query
        file_path (str): Path to the uploaded PDF file
        user_id (str, optional): User identifier for tracking
        document_id (int, optional): Database document ID
    
    Returns:
        dict: Analysis results including status, findings, and metadata
    """
    
    task_id = self.request.id
    start_time = datetime.utcnow()
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Update document status to PROCESSING
        if document_id:
            crud.update_document_status(db, document_id, DocumentStatus.PROCESSING)
        
        # Update task state to show progress
        self.update_state(
            state="PROCESSING",
            meta={
                "status": "Initializing agents...",
                "progress": 10,
                "current_step": "setup"
            }
        )
        
        # Verify file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Document not found at {file_path}")
        
        # Update state
        self.update_state(
            state="PROCESSING",
            meta={
                "status": "Running verification...",
                "progress": 20,
                "current_step": "verification"
            }
        )
        
        # Create and configure the crew
        financial_crew = Crew(
            agents=[verifier, financial_analyst, investment_advisor, risk_assessor],
            tasks=[verification, analyze_financial_document, investment_analysis, risk_assessment],
            process=Process.sequential,
            verbose=True,
        )
        
        # Update state
        self.update_state(
            state="PROCESSING",
            meta={
                "status": "Analyzing financial document...",
                "progress": 40,
                "current_step": "analysis"
            }
        )
        
        # Run the crew analysis
        result = financial_crew.kickoff({"query": query})
        
        # Update state
        self.update_state(
            state="PROCESSING",
            meta={
                "status": "Generating recommendations...",
                "progress": 80,
                "current_step": "recommendations"
            }
        )
        
        # Calculate processing time
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        # Prepare result
        analysis_result = {
            "status": "success",
            "task_id": task_id,
            "query": query,
            "analysis": str(result),
            "user_id": user_id,
            "processing_time_seconds": processing_time,
            "completed_at": end_time.isoformat(),
            "file_path": file_path,
            "document_id": document_id
        }
        
        # Save to database
        if document_id:
            # Update document status
            crud.update_document_status(
                db, document_id, DocumentStatus.COMPLETED, processed_at=end_time
            )
            
            # Get or create analysis record
            analysis = crud.get_analysis_by_task_id(db, task_id)
            if analysis:
                crud.update_analysis_result(
                    db=db,
                    analysis_id=analysis.id,
                    analysis_result=analysis_result,
                    raw_output=str(result),
                    processing_time_seconds=processing_time,
                    status="completed"
                )
            else:
                # Create new analysis record
                crud.create_analysis(
                    db=db,
                    document_id=document_id,
                    task_id=task_id,
                    analysis_result=analysis_result,
                    raw_output=str(result),
                    processing_time_seconds=processing_time,
                    status="completed"
                )
        
        return analysis_result
        
    except FileNotFoundError as e:
        error_msg = f"File not found: {str(e)}"
        print(f"Task {task_id} failed: {error_msg}")
        
        # Update database
        if document_id:
            crud.update_document_status(db, document_id, DocumentStatus.FAILED)
            analysis = crud.get_analysis_by_task_id(db, task_id)
            if analysis:
                crud.update_analysis_error(db, analysis.id, error_msg)
        
        return {
            "status": "error",
            "task_id": task_id,
            "error": error_msg,
            "error_type": "FileNotFoundError",
            "document_id": document_id
        }
        
    except Exception as e:
        error_msg = str(e)
        error_traceback = traceback.format_exc()
        print(f"Task {task_id} encountered error: {error_msg}")
        print(f"Traceback: {error_traceback}")
        
        # Update database
        if document_id:
            crud.update_document_status(db, document_id, DocumentStatus.FAILED)
            analysis = crud.get_analysis_by_task_id(db, task_id)
            if analysis:
                crud.update_analysis_error(db, analysis.id, error_msg)
        
        # Retry on certain types of errors
        if "rate limit" in error_msg.lower() or "timeout" in error_msg.lower():
            try:
                # Exponential backoff: 60s, 120s, 240s
                raise self.retry(countdown=60 * (2 ** self.request.retries), exc=e)
            except self.MaxRetriesExceededError:
                pass  # Fall through to return error
        
        return {
            "status": "error",
            "task_id": task_id,
            "error": error_msg,
            "error_type": type(e).__name__,
            "traceback": error_traceback,
            "document_id": document_id
        }
    
    finally:
        # Close database session
        db.close()


@celery_app.task(name="worker.cleanup_old_files")
def cleanup_old_files(max_age_hours: int = 24):
    """
    Periodic task to clean up old uploaded files.
    
    Args:
        max_age_hours (int): Delete files older than this many hours
    
    Returns:
        dict: Cleanup statistics
    """
    import time
    
    data_dir = "data"
    if not os.path.exists(data_dir):
        return {"status": "no_directory", "files_deleted": 0}
    
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    deleted_count = 0
    
    try:
        for filename in os.listdir(data_dir):
            if filename.startswith("financial_document_"):
                file_path = os.path.join(data_dir, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        os.remove(file_path)
                        deleted_count += 1
                        print(f"Deleted old file: {filename}")
        
        return {
            "status": "success",
            "files_deleted": deleted_count,
            "max_age_hours": max_age_hours
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "files_deleted": deleted_count
        }


# Configure periodic tasks (optional - requires celery beat)
celery_app.conf.beat_schedule = {
    "cleanup-old-files-daily": {
        "task": "worker.cleanup_old_files",
        "schedule": 86400.0,  # Run every 24 hours
        "args": (24,)  # Delete files older than 24 hours
    },
}
