"""
CRUD Operations for Database Models

Provides functions for creating, reading, updating, and deleting database records.
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from datetime import datetime
import uuid

from models import User, Document, Analysis, APILog, DocumentStatus


# ===== User Operations =====

def create_user(db: Session, user_id: str, email: Optional[str] = None, 
                api_key: Optional[str] = None) -> User:
    """
    Create a new user.
    
    Args:
        db: Database session
        user_id: Unique user identifier
        email: User email (optional)
        api_key: API key for authentication (optional)
    
    Returns:
        User: Created user object
    """
    user = User(
        user_id=user_id,
        email=email,
        api_key=api_key
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        # User might already exist, return existing
        return get_user_by_user_id(db, user_id)


def get_user_by_id(db: Session, user_db_id: int) -> Optional[User]:
    """Get user by database ID"""
    return db.query(User).filter(User.id == user_db_id).first()


def get_user_by_user_id(db: Session, user_id: str) -> Optional[User]:
    """Get user by user_id string"""
    return db.query(User).filter(User.user_id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()


def get_or_create_user(db: Session, user_id: str, email: Optional[str] = None) -> User:
    """Get existing user or create new one"""
    user = get_user_by_user_id(db, user_id)
    if not user:
        user = create_user(db, user_id, email)
    return user


# ===== Document Operations =====

def create_document(
    db: Session,
    filename: str,
    file_path: str,
    original_filename: Optional[str] = None,
    user_id: Optional[int] = None,
    file_size: Optional[int] = None,
    query: Optional[str] = None,
    task_id: Optional[str] = None
) -> Document:
    """
    Create a new document record.
    
    Args:
        db: Database session
        filename: Stored filename
        file_path: Path to stored file
        original_filename: Original uploaded filename
        user_id: Database user ID (optional)
        file_size: File size in bytes
        query: User's analysis query
        task_id: Celery task ID
    
    Returns:
        Document: Created document object
    """
    document = Document(
        filename=filename,
        original_filename=original_filename or filename,
        file_path=file_path,
        user_id=user_id,
        file_size=file_size,
        query=query,
        task_id=task_id,
        status=DocumentStatus.UPLOADED
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def get_document_by_id(db: Session, document_id: int) -> Optional[Document]:
    """Get document by database ID"""
    return db.query(Document).filter(Document.id == document_id).first()


def get_document_by_uuid(db: Session, document_uuid: uuid.UUID) -> Optional[Document]:
    """Get document by UUID"""
    return db.query(Document).filter(Document.document_id == document_uuid).first()


def get_document_by_task_id(db: Session, task_id: str) -> Optional[Document]:
    """Get document by Celery task ID"""
    return db.query(Document).filter(Document.task_id == task_id).first()


def get_documents_by_user(db: Session, user_id: int, limit: int = 100) -> List[Document]:
    """Get all documents for a user"""
    return db.query(Document)\
        .filter(Document.user_id == user_id)\
        .order_by(Document.uploaded_at.desc())\
        .limit(limit)\
        .all()


def update_document_status(
    db: Session,
    document_id: int,
    status: DocumentStatus,
    processed_at: Optional[datetime] = None
) -> Optional[Document]:
    """Update document processing status"""
    document = get_document_by_id(db, document_id)
    if document:
        document.status = status
        if processed_at:
            document.processed_at = processed_at
        elif status == DocumentStatus.COMPLETED:
            document.processed_at = datetime.utcnow()
        db.commit()
        db.refresh(document)
    return document


def update_document_task_id(db: Session, document_id: int, task_id: str) -> Optional[Document]:
    """Update document with Celery task ID"""
    document = get_document_by_id(db, document_id)
    if document:
        document.task_id = task_id
        document.status = DocumentStatus.QUEUED
        db.commit()
        db.refresh(document)
    return document


# ===== Analysis Operations =====

def create_analysis(
    db: Session,
    document_id: int,
    task_id: Optional[str] = None,
    analysis_result: Optional[dict] = None,
    raw_output: Optional[str] = None,
    processing_time_seconds: Optional[float] = None,
    status: str = "pending"
) -> Analysis:
    """
    Create a new analysis record.
    
    Args:
        db: Database session
        document_id: Document database ID
        task_id: Celery task ID
        analysis_result: Analysis results as dictionary
        raw_output: Full raw output text
        processing_time_seconds: Processing time
        status: Analysis status
    
    Returns:
        Analysis: Created analysis object
    """
    analysis = Analysis(
        document_id=document_id,
        task_id=task_id,
        analysis_result=analysis_result,
        raw_output=raw_output,
        processing_time_seconds=processing_time_seconds,
        status=status
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


def get_analysis_by_id(db: Session, analysis_id: int) -> Optional[Analysis]:
    """Get analysis by database ID"""
    return db.query(Analysis).filter(Analysis.id == analysis_id).first()


def get_analysis_by_uuid(db: Session, analysis_uuid: uuid.UUID) -> Optional[Analysis]:
    """Get analysis by UUID"""
    return db.query(Analysis).filter(Analysis.analysis_id == analysis_uuid).first()


def get_analysis_by_task_id(db: Session, task_id: str) -> Optional[Analysis]:
    """Get analysis by Celery task ID"""
    return db.query(Analysis).filter(Analysis.task_id == task_id).first()


def get_analyses_by_document(db: Session, document_id: int) -> List[Analysis]:
    """Get all analyses for a document"""
    return db.query(Analysis)\
        .filter(Analysis.document_id == document_id)\
        .order_by(Analysis.created_at.desc())\
        .all()


def update_analysis_result(
    db: Session,
    analysis_id: int,
    analysis_result: dict,
    raw_output: Optional[str] = None,
    processing_time_seconds: Optional[float] = None,
    status: str = "completed"
) -> Optional[Analysis]:
    """Update analysis with results"""
    analysis = get_analysis_by_id(db, analysis_id)
    if analysis:
        analysis.analysis_result = analysis_result
        if raw_output:
            analysis.raw_output = raw_output
        if processing_time_seconds:
            analysis.processing_time_seconds = processing_time_seconds
        analysis.status = status
        db.commit()
        db.refresh(analysis)
    return analysis


def update_analysis_error(
    db: Session,
    analysis_id: int,
    error_message: str
) -> Optional[Analysis]:
    """Update analysis with error"""
    analysis = get_analysis_by_id(db, analysis_id)
    if analysis:
        analysis.status = "failed"
        analysis.error_message = error_message
        db.commit()
        db.refresh(analysis)
    return analysis


# ===== API Log Operations =====

def create_api_log(
    db: Session,
    endpoint: str,
    method: str,
    status_code: Optional[int] = None,
    user_id: Optional[int] = None,
    response_time_ms: Optional[float] = None,
    error_message: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> APILog:
    """Create an API request log entry"""
    log = APILog(
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        user_id=user_id,
        response_time_ms=response_time_ms,
        error_message=error_message,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_api_logs(
    db: Session,
    limit: int = 100,
    user_id: Optional[int] = None,
    endpoint: Optional[str] = None
) -> List[APILog]:
    """Get API logs with optional filters"""
    query = db.query(APILog)
    
    if user_id:
        query = query.filter(APILog.user_id == user_id)
    if endpoint:
        query = query.filter(APILog.endpoint.like(f"%{endpoint}%"))
    
    return query.order_by(APILog.timestamp.desc()).limit(limit).all()


# ===== Statistics =====

def get_user_document_count(db: Session, user_id: int) -> int:
    """Get total number of documents for a user"""
    return db.query(Document).filter(Document.user_id == user_id).count()


def get_user_analysis_count(db: Session, user_id: int) -> int:
    """Get total number of analyses for a user"""
    return db.query(Analysis)\
        .join(Document)\
        .filter(Document.user_id == user_id)\
        .count()


def get_total_documents(db: Session) -> int:
    """Get total number of documents in system"""
    return db.query(Document).count()


def get_total_analyses(db: Session) -> int:
    """Get total number of analyses in system"""
    return db.query(Analysis).count()
