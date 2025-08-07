from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncAttrs, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, synonym
from sqlalchemy import String, ForeignKey, JSON, func, Text, Column, Integer, Float, DateTime
from ..core.config import get_settings

settings = get_settings()
engine = create_async_engine(settings.database_url, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_pw: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    date_of_birth: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # ISO date string
    gender: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sex: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ethnic_group: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    long_term_conditions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    medications: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    consent_to_data_storage: Mapped[bool] = mapped_column(default=False)
    is_admin: Mapped[bool] = mapped_column(default=False)  # Admin flag

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    location: Mapped[Optional[str]]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    
    user: Mapped["User"] = relationship(backref="sessions")

class Message(Base):
    __tablename__ = "messages"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("chat_sessions.id"))
    role: Mapped[str] = mapped_column(String(10))  # "user" / "assistant" / "system"
    content: Mapped[str] = mapped_column(Text)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # RAG score
    sources: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Question category
    user_question: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Original user question for this answer
    # response_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)  # Store metadata as JSON (renamed from metadata)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

class UnansweredQuery(Base):
    __tablename__ = "unanswered_queries"
    
    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    location = Column(String, nullable=True)
    reason = Column(String, nullable=True)  # NEW
    score = Column(Float, nullable=True)  # NEW
    category = Column(String(50), nullable=True)  # Question category
    created_at = Column(DateTime, default=datetime.utcnow)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=True) 
    sources = Column(JSON, nullable=True) 