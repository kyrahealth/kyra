from ...db.models import (
    SessionLocal,
    ChatSession,
    Message,
    UnansweredQuery,
    User,  # Add User import for type hints
)
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import re
from ...services.auth import get_current_user
from ...services.rag import answer
from ...services.categorization import categorize_question, get_available_categories
from sqlalchemy import select, desc

router = APIRouter()

class ChatIn(BaseModel):
    message: str
    location: str | None = None
    session_id: int | None = None  # Optional session ID for continuing conversation

class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: str
    category: Optional[str] = None
    # sources: Optional[List[str]] = None
    # response_metadata: Optional[dict] = None  # Changed from metadata to response_metadata

class ChatOut(BaseModel):
    response: str
    sources: list[str]
    session_id: int
    messages: List[MessageOut] = []
    metadata: dict = {}  # Include metadata for debugging/analytics

def build_user_context(user: 'User') -> str:
    if not getattr(user, 'consent_to_data_storage', False):
        return ""
    info = []
    if user.full_name:
        info.append(f"Full Name: {user.full_name}")
    if user.date_of_birth:
        info.append(f"Date of Birth: {user.date_of_birth}")
    if user.gender:
        info.append(f"Gender: {user.gender}")
    if user.sex:
        info.append(f"Sex: {user.sex}")
    if user.country:
        info.append(f"Country: {user.country}")
    if user.address:
        info.append(f"Address: {user.address}")
    if user.ethnic_group:
        info.append(f"Ethnic Group: {user.ethnic_group}")
    if user.long_term_conditions:
        info.append(f"Long-term Medical Conditions: {user.long_term_conditions}")
    if user.medications:
        info.append(f"Medications: {user.medications}")
    if not info:
        return ""
    return (
        "The following is background information about the user. Use this to provide more personalized and relevant responses. "
        + " | ".join(info)
    )

@router.post("/chat", response_model=ChatOut)
async def chat(body: ChatIn, user=Depends(get_current_user)):
    async with SessionLocal() as db:
        # ---------- Get or create chat session ---------------------------
        session = None
        print(f"[DEBUG] Request session_id: {body.session_id}")
        
        if body.session_id:
            # Try to get existing session
            result = await db.execute(
                select(ChatSession).where(
                    ChatSession.id == body.session_id,
                    ChatSession.user_id == user.id
                )
            )
            session = result.scalar_one_or_none()
            print(f"[DEBUG] Found existing session: {session.id if session else 'None'}")
        
        if not session:
            # Create new session
            print(f"[DEBUG] Creating new session")
            session = ChatSession(
                user_id=user.id,
                location=body.location
            )
            db.add(session)
            await db.commit()
            await db.refresh(session)
            print(f"[DEBUG] Created new session with ID: {session.id}")
        
        # ---------- Get conversation history for context ------------------
        # Get history BEFORE adding current message to build proper context
        history_result = await db.execute(
            select(Message)
            .where(Message.session_id == session.id)
            .order_by(Message.created_at)
            .limit(20)  # Limit to last 20 messages for context
        )
        history_messages = history_result.scalars().all()
        
        print(f"[DEBUG] Found {len(history_messages)} existing messages in session {session.id}")
        
        # Build conversation history for GPT-4o (existing messages only)
        conversation_history = []
        for msg in history_messages[-10:]:  # Use last 10 for context
            role = "assistant" if msg.role == "assistant" else msg.role
            conversation_history.append({
                "role": role, 
                "content": msg.content
            })
        # Build user context string (do not prepend to conversation_history)
        user_context = build_user_context(user)
        
        print(f"[DEBUG] Built conversation history with {len(conversation_history)} messages")
        if conversation_history:
            print(f"[DEBUG] Conversation history details:")
            for i, msg in enumerate(conversation_history):
                print(f"  {i+1}. {msg['role']}: {msg['content'][:100]}...")
        else:
            print(f"[DEBUG] No conversation history found - history_messages length was {len(history_messages)}")
            
        # Additional debugging - print raw database messages
        print(f"[DEBUG] Raw database messages:")
        for i, msg in enumerate(history_messages):
            print(f"  DB {i+1}. ID:{msg.id} Role:{msg.role} Content:{msg.content[:50]}...")
        
        # ---------- Categorize ALL questions BEFORE saving user message ---------------
        category = None
        try:
            category = categorize_question(body.message)
            print(f"[DEBUG] Question categorized as: {category}")
            print(f"[DEBUG] Category type: {type(category)}")
            print(f"[DEBUG] Category length: {len(category) if category else 0}")
        except Exception as e:
            print(f"[DEBUG] Categorization error: {e}")
            category = None
        
        # ---------- Save user message AFTER getting history ---------------
        print(f"[DEBUG] Creating user message with category: '{category}'")
        user_message = Message(
            session_id=session.id,
            role="user",
            content=body.message,
            category=category  # Now properly categorized for all questions
        )
        db.add(user_message)
        # Don't commit yet - we'll commit both messages together
        
        # ---------- Generate response with hybrid system -----------------
        try:
            # Build contextual query for RAG (if medical)
            contextual_query = body.message  # Default to just the current message
            
            if conversation_history:
                print(f"[DEBUG] Building contextual query with {len(conversation_history)} previous messages")
                
                # Create context-aware query for RAG classification and retrieval
                context_messages = []
                for msg in conversation_history[-5:]:  # Last 5 for context
                    context_messages.append(f"{msg['role']}: {msg['content']}")
                
                # Add current message to context
                context_messages.append(f"user: {body.message}")
                
                contextual_query = f"Previous conversation:\n" + "\n".join(context_messages[:-1]) + f"\n\nCurrent question: {body.message}"
                print(f"[DEBUG] Contextual query: {contextual_query[:300]}...")
            else:
                print(f"[DEBUG] No conversation history, using direct query: {body.message}")
            
            print(f"[DEBUG] Calling answer() with:")
            print(f"  - Query: {contextual_query[:100]}...")
            print(f"  - Original query: {body.message}")
            print(f"  - Conversation history items: {len(conversation_history)}")
            
            # Call the hybrid RAG + GPT-4o system
            response, sources, metadata = answer(
                query=contextual_query,
                conversation_history=conversation_history,
                original_query=body.message,
                user_context=user_context
            )
            
            # Determine which sources to save
            if metadata.get("used_rag"):
                sources_to_save = sources if sources else None
            else:
                sources_to_save = re.findall(r'\((https?://[^\s)]+)\)', response)  # fallback, could extract from response if needed

            # ---------- Save unanswered if needed ----------------------------
            if metadata.get("is_medical", False) and not metadata.get("used_rag", False):
                print(f"[DEBUG] Saving unanswered query with category: '{category}'")
                unanswered_query = UnansweredQuery(
                    text=body.message,
                    location=body.location,
                    reason=f"medical_question_no_rag",
                    score=metadata.get('rag_score', 0.0),
                    category=category,  # Already categorized above
                    session_id=session.id,
                    sources=sources_to_save,
                )
                db.add(unanswered_query)
                await db.commit()
                await db.refresh(unanswered_query)
                print(f"[DEBUG] Unanswered query saved with ID: {unanswered_query.id}, category: '{unanswered_query.category}'")
            
        except Exception as e:
            # Log the error
            db.add(
                UnansweredQuery(
                    text=body.message,
                    location=body.location,
                    reason=f"system_error: {str(e)}",
                    category=category,  # Will be None if categorization failed
                    session_id=session.id,
                    sources=sources if sources else None,
                )
            )
            
            # Save error message
            error_message = Message(
                session_id=session.id,
                role="assistant",
                content="I'm having trouble responding right now. Please try again in a moment."
            )
            db.add(error_message)
            await db.commit()
            
            # Get all messages for response
            all_messages_result = await db.execute(
                select(Message)
                .where(Message.session_id == session.id)
                .order_by(Message.created_at)
            )
            all_messages = all_messages_result.scalars().all()
            
            return {
                "response": "I'm having trouble responding right now. Please try again in a moment.",
                "sources": [],
                "session_id": session.id,
                "messages": [
                    MessageOut(
                        id=msg.id,
                        role=msg.role,
                        content=msg.content,
                        created_at=msg.created_at.isoformat(),
                        category=msg.category
                    ) for msg in all_messages
                ],
                "metadata": {"error": True}
            }
        
        # ---------- Success - save both messages together ---------------------
        print(f"[DEBUG] Creating assistant message with category: '{category}'")
        assistant_message = Message(
            session_id=session.id,
            role="assistant",
            content=response,
            confidence_score=metadata.get("rag_score") if metadata else None,
            sources=sources_to_save,
            user_question=body.message,  # Store the original user question
            category=category,  # Include the category for the assistant response
            # sources=sources,  # Store sources with the message
            # response_metadata=metadata  # Store metadata with the message (renamed from metadata)
        )
        db.add(assistant_message)
        
        # Commit both messages together
        await db.commit()
        await db.refresh(user_message)
        await db.refresh(assistant_message)
        print(f"[DEBUG] User message saved with ID: {user_message.id}, category: '{user_message.category}'")
        print(f"[DEBUG] Assistant message saved with ID: {assistant_message.id}, category: '{assistant_message.category}'")
        
        # Get all messages for response
        all_messages_result = await db.execute(
            select(Message)
            .where(Message.session_id == session.id)
            .order_by(Message.created_at)
        )
        all_messages = all_messages_result.scalars().all()
        
        return {
            "response": response,
            "sources": sources,
            "session_id": session.id,
            "messages": [
                MessageOut(
                    id=msg.id,
                    role=msg.role,
                    content=msg.content,
                    created_at=msg.created_at.isoformat(),
                    category=msg.category,
                    # sources=msg.sources,
                    # response_metadata=msg.response_metadata
                ) for msg in all_messages
            ],
            "metadata": metadata
        }

@router.get("/chat/sessions", response_model=List[dict])
async def get_chat_sessions(user=Depends(get_current_user)):
    """Get all chat sessions for the current user"""
    async with SessionLocal() as db:
        result = await db.execute(
            select(ChatSession)
            .where(ChatSession.user_id == user.id)
            .order_by(desc(ChatSession.created_at))
        )
        sessions = result.scalars().all()
        
        session_list = []
        for session in sessions:
            # Get the first message for preview
            first_msg_result = await db.execute(
                select(Message)
                .where(Message.session_id == session.id, Message.role == "user")
                .order_by(Message.created_at)
                .limit(1)
            )
            first_message = first_msg_result.scalar_one_or_none()
            
            session_list.append({
                "id": session.id,
                "created_at": session.created_at.isoformat(),
                "location": session.location,
                "preview": first_message.content[:50] + "..." if first_message else "New conversation"
            })
        
        return session_list

@router.get("/chat/session/{session_id}", response_model=List[MessageOut])
async def get_session_messages(session_id: int, user=Depends(get_current_user)):
    """Get all messages for a specific session"""
    async with SessionLocal() as db:
        # Verify session belongs to user
        session_result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.user_id == user.id
            )
        )
        session = session_result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get messages
        messages_result = await db.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at)
        )
        messages = messages_result.scalars().all()
        
        return [
            MessageOut(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at.isoformat(),
                category=msg.category,
                # sources=msg.sources,
                # response_metadata=msg.response_metadata
            ) for msg in messages
        ]

@router.delete("/chat/session/{session_id}")
async def delete_chat_session(session_id: int, user=Depends(get_current_user)):
    """Delete a chat session and all its messages for the current user"""
    async with SessionLocal() as db:
        # Verify session belongs to user
        session_result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.user_id == user.id
            )
        )
        session = session_result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        # Delete all messages for this session
        await db.execute(
            Message.__table__.delete().where(Message.session_id == session_id)
        )
        # Delete the session itself
        await db.execute(
            ChatSession.__table__.delete().where(ChatSession.id == session_id)
        )
        await db.commit()
        return {"success": True, "session_id": session_id}

@router.get("/chat/categories")
async def get_categories():
    """Get available question categories for filtering"""
    return {"categories": get_available_categories()}