"""
SQLAlchemy Database Models

Defines the database schema for users, documents, and analysis results.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
import uuid as uuid_lib

from database import Base


class DocumentStatus(enum.Enum):
    """Enum for document processing status"""
    UPLOADED = "uploaded"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class User(Base):
    """User model for tracking document owners"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    api_key = Column(String(255), unique=True, index=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, user_id={self.user_id}, email={self.email})>"


class Document(Base):
    """Document model for storing uploaded financial documents metadata"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(UUID(as_uuid=True), default=uuid_lib.uuid4, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=True)
    file_path = Column(String(1000), nullable=False)
    file_size = Column(Integer, nullable=True)  # Size in bytes
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.UPLOADED, index=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Celery task tracking
    task_id = Column(String(255), unique=True, index=True, nullable=True)
    
    # User query
    query = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="documents")
    analyses = relationship("Analysis", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename}, status={self.status})>"


class Analysis(Base):
    """Analysis model for storing analysis results"""
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    analysis_id = Column(UUID(as_uuid=True), default=uuid_lib.uuid4, unique=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    task_id = Column(String(255), index=True, nullable=True)
    
    # Analysis results (stored as JSONB for flexibility)
    analysis_result = Column(JSONB, nullable=True)
    
    # Individual analysis components (can be extracted from JSONB or stored separately)
    verification_result = Column(Text, nullable=True)
    financial_analysis = Column(Text, nullable=True)
    investment_recommendations = Column(Text, nullable=True)
    risk_assessment = Column(Text, nullable=True)
    
    # Full raw output
    raw_output = Column(Text, nullable=True)
    
    # Metadata
    processing_time_seconds = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Status
    status = Column(String(50), default="pending")
    error_message = Column(Text, nullable=True)
    
    # Relationships
    document = relationship("Document", back_populates="analyses")
    
    def __repr__(self):
        return f"<Analysis(id={self.id}, document_id={self.document_id}, status={self.status})>"


class APILog(Base):
    """API request logging for tracking usage"""
    __tablename__ = "api_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    endpoint = Column(String(255), nullable=False, index=True)
    method = Column(String(10), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    status_code = Column(Integer, nullable=True)
    response_time_ms = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Request details
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    def __repr__(self):
        return f"<APILog(id={self.id}, endpoint={self.endpoint}, status={self.status_code})>"
