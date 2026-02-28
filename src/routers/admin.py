from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database.database import get_db
from schemas.poll_schema import PollCreate, PollResponse
from services.poll_service import PollService

router = APIRouter()

@router.post("/polls/", response_model=PollResponse)
def create_poll(poll_data: PollCreate, db: Session = Depends(get_db)):
    try:
        return PollService.create_poll(db, poll_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/polls/", response_model=List[PollResponse])
def get_polls(db: Session = Depends(get_db)):
    return PollService.get_active_polls(db)