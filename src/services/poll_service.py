from datetime import datetime
from sqlalchemy.orm import Session
from passlib.context import CryptContext


from database.models import User, Poll, PollOption, Vote
from schemas.poll_schema import UserCreate, PollCreate, VoteCreate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        is_active=True,
        is_admin=False
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_active_polls(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Poll)\
        .filter(Poll.is_active == True)\
        .offset(skip)\
        .limit(limit)\
        .all()

def get_poll(db: Session, poll_id: int):
    return db.query(Poll).filter(Poll.id == poll_id).first()

def create_poll(db: Session, poll: PollCreate, user_id: int):
    db_poll = Poll(
        title=poll.title,
        description=poll.description,
        ends_at=poll.ends_at,
        allow_multiple=poll.allow_multiple,
        created_by=user_id,
        is_active=True
    )
    db.add(db_poll)
    db.commit()
    db.refresh(db_poll)

    for option_text in poll.options:
        db_option = PollOption(
            text=option_text,
            poll_id=db_poll.id
        )
        db.add(db_option)
    
    db.commit()
    db.refresh(db_poll)
    return db_poll

def create_vote(db: Session, vote: VoteCreate, user_id: int):
    option = db.query(PollOption).filter(PollOption.id == vote.option_id).first()
    if not option or option.poll_id != vote.poll_id:
        return False

    db_vote = Vote(
        user_id=user_id,
        poll_id=vote.poll_id,
        option_id=vote.option_id
    )
    db.add(db_vote)
    db.commit()
    return True