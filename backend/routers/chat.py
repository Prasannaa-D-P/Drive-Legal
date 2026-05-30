from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from backend.database import get_db
from backend.models import ChatSession, ChatMessage
from backend.schemas import ChatSessionBase, ChatMessageBase, ChatMessageCreate

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)

@router.post("/session", response_model=ChatSessionBase)
def create_or_get_session(session_id: str, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        session = ChatSession(id=session_id, created_at=datetime.utcnow().isoformat())
        db.add(session)
        db.commit()
        db.refresh(session)
    return session

@router.post("/message", response_model=ChatMessageBase)
def save_message(msg: ChatMessageCreate, db: Session = Depends(get_db)):
    # Ensure session exists
    session = db.query(ChatSession).filter(ChatSession.id == msg.session_id).first()
    if not session:
        session = ChatSession(id=msg.session_id, created_at=datetime.utcnow().isoformat())
        db.add(session)
        db.commit()
    
    new_msg = ChatMessage(
        session_id=msg.session_id,
        sender=msg.sender,
        text=msg.text,
        timestamp=msg.timestamp
    )
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)
    return new_msg

@router.get("/{session_id}", response_model=ChatSessionBase)
def get_chat_history(session_id: str, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
