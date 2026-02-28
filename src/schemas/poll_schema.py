from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class PollOptionBase(BaseModel):
    text: str

class PollOptionCreate(PollOptionBase):
    pass

class PollOption(PollOptionBase):
    id: int
    poll_id: int
    votes_count: Optional[int] = 0

    class Config:
        from_attributes = True  

class PollBase(BaseModel):
    title: str
    description: Optional[str] = None
    is_active: bool = True
    allow_multiple: bool = False
    ends_at: Optional[datetime] = None

class PollCreate(BaseModel):
    title: str
    description: Optional[str] = None
    allow_multiple: bool = False
    options: List[PollOptionCreate]
    
class PollCreate(PollBase):
    pass

class Poll(PollBase):
    id: int
    created_at: datetime
    is_active: bool
    created_by: int 
    options: List[PollOption]
    total_votes: Optional[int] = 0

    class Config:
        from_attributes = True  

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True  

class VoteCreate(BaseModel):
    poll_id: int
    option_id: int

class VoteResponse(BaseModel):
    message: str