import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Any, List
from backend.database import get_db
from backend.models import ChatSession, ChatMessage, FAQKnowledge, State
from backend.schemas import ChatSessionBase, ChatMessageBase, ChatMessageCreate, ChatRequest

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

@router.post("/")
def query_faq_bot(req: ChatRequest, db: Session = Depends(get_db)):
    # 1. Resolve State
    state = db.query(State).filter(State.state_code.ilike(req.state_code)).first()
    state_id = state.state_id if state else None
    
    # 2. Query faq_knowledge
    faqs = db.query(FAQKnowledge).all()
    if state_id:
        state_faqs = [f for f in faqs if f.state_id == state_id]
        if state_faqs:
            faqs = state_faqs
            
    # Simple word overlap matching
    user_words = set(re.findall(r'\w+', req.message.lower()))
    
    best_faq = None
    max_overlap = 0
    
    for faq in faqs:
        q_words = set(re.findall(r'\w+', faq.question.lower()))
        overlap = len(user_words.intersection(q_words))
        if overlap > max_overlap:
            max_overlap = overlap
            best_faq = faq
            
    # Substring match if overlap is 0
    if max_overlap == 0:
        for faq in faqs:
            if faq.question.lower() in req.message.lower() or req.message.lower() in faq.question.lower():
                best_faq = faq
                break
                
    if best_faq:
        answer = best_faq.answer
    else:
        answer = "I'm sorry, I couldn't find a specific traffic law answer for your question. Please try asking about helmet rules, seatbelts, speeding, or drunk driving."
        
    return {
        "status": "success",
        "answer": answer,
        "matched_question": best_faq.question if best_faq else None
    }
