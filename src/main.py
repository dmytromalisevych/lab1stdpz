"""
Головний модуль системи голосування (Voting System).
Містить конфігурацію FastAPI, налаштування бази даних, авторизації (JWT), 
а також усі маршрути (endpoints) для роботи з опитуваннями, користувачами та голосами.
"""

import os
import logging
import bcrypt
from pathlib import Path
from sqlalchemy import func, or_

from database.database import get_db, init_db
from fastapi import FastAPI, Depends, HTTPException, Response, status, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timedelta
from typing import List, Optional
from jose import JWTError, jwt

from database.models import User, Poll, Vote, PollOption
from database import SessionLocal, engine
from schemas.poll_schema import UserCreate, PollCreate, VoteCreate, Poll as PollSchema, User as UserSchema, VoteResponse
from services.poll_service import (
    get_user_by_username,
    verify_password,
    create_user,
    get_active_polls,
    get_poll,
    create_poll,
    create_vote
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Voting System")

BASE_DIR = Path(__file__).resolve().parent

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

@app.on_event("startup")
async def startup_event():
    """
    Подія, що викликається при запуску додатку.
    Ініціалізує з'єднання з базою даних.
    
    Raises:
        Exception: Якщо виникає помилка підключення до БД.
    """
    try:
        init_db()
        logger.info("Successfully connected to existing database")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

def get_db():
    """
    Створює та повертає сесію бази даних.
    Після завершення запиту автоматично закриває з'єднання.
    
    Yields:
        Session: Сесія SQLAlchemy.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: dict):
    """
    Генерує JWT токен для авторизації користувача.
    
    Args:
        data (dict): Дані для кодування в токен (наприклад, username).
        
    Returns:
        str: Згенерований JWT токен.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(request: Request):
    """
    Отримує поточного авторизованого користувача з кукі (JWT токен).
    
    Args:
        request (Request): Об'єкт HTTP-запиту з кукі.
        
    Returns:
        User | None: Об'єкт користувача, якщо токен валідний, інакше None.
    """
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        token_type, _, token_value = token.partition(" ")
        if token_type.lower() != "bearer":
            return None
        
        payload = jwt.decode(token_value, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            return None
            
        db = SessionLocal()
        user = db.query(User).filter(User.username == username).first()
        db.close()
        return user
    except:
        return None

@app.get("/poll/{poll_id}/results")
async def poll_results(request: Request, poll_id: int, db: Session = Depends(get_db)):
    """
    Відображає HTML-сторінку з результатами конкретного опитування.
    
    Args:
        request (Request): HTTP запит.
        poll_id (int): Ідентифікатор опитування.
        db (Session): Сесія бази даних.
        
    Returns:
        TemplateResponse: HTML-шаблон poll_results.html.
        
    Raises:
        HTTPException: Якщо опитування не знайдено.
    """
    try:
        poll = db.query(Poll).filter(Poll.id == poll_id).first()
        if not poll:
            raise HTTPException(status_code=404, detail="Голосування не знайдено")
        
        options_with_votes = []
        total_votes = 0
        
        for option in poll.options:
            votes_count = db.query(Vote).filter(Vote.option_id == option.id).count()
            total_votes += votes_count
            options_with_votes.append({
                "id": option.id,
                "text": option.text,
                "votes": votes_count,
                "percentage": round((votes_count / total_votes * 100) if total_votes > 0 else 0, 1)
            })
        
        return templates.TemplateResponse(
            "poll_results.html",
            {
                "request": request,
                "poll": poll,
                "options": options_with_votes,
                "total_votes": total_votes,
                "current_user": await get_current_user(request)
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error showing poll results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.delete("/api/polls/{poll_id}")
async def delete_poll(
    poll_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Видаляє опитування, його варіанти відповідей та всі пов'язані голоси.
    Доступно лише для адміністраторів.
    
    Args:
        poll_id (int): Ідентифікатор опитування для видалення.
        current_user (User): Авторизований користувач (перевіряється на is_admin).
        db (Session): Сесія бази даних.
        
    Returns:
        dict: Статус успішного видалення.
        
    Raises:
        HTTPException: Якщо прав недостатньо або опитування відсутнє.
    """
    try:
        if not current_user or not current_user.is_admin:
            raise HTTPException(
                status_code=403,
                detail="Недостатньо прав для видалення опитування"
            )
        
        poll = db.query(Poll).filter(Poll.id == poll_id).first()
        if not poll:
            raise HTTPException(
                status_code=404,
                detail="Опитування не знайдено"
            )
        
        db.query(Vote).filter(Vote.poll_id == poll_id).delete()
        db.query(PollOption).filter(PollOption.poll_id == poll_id).delete()
        db.delete(poll)
        db.commit()
        
        return {
            "success": True,
            "message": "Опитування успішно видалено",
            "deleted_at": "2025-05-17 21:50:38",
            "deleted_by": "dmytromalisevych"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting poll: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Помилка при видаленні опитування"
        )

@app.get("/")
async def home(request: Request, db: Session = Depends(get_db)):
    """
    Головна сторінка. Відображає список активних опитувань.
    Перевіряє, чи голосував поточний користувач у кожному з них.
    
    Args:
        request (Request): HTTP запит.
        db (Session): Сесія бази даних.
        
    Returns:
        TemplateResponse: HTML-шаблон index.html.
    """
    try:
        current_user = await get_current_user(request)
        
        polls = (
            db.query(Poll)
            .filter(Poll.is_active == True)
            .order_by(Poll.created_at.desc())
            .all()
        )
        
        for poll in polls:
            poll.options = db.query(PollOption).filter(PollOption.poll_id == poll.id).all()
            poll.total_votes = db.query(Vote).filter(Vote.poll_id == poll.id).count()
            
            if current_user:
                poll.user_voted = db.query(Vote).filter(
                    Vote.poll_id == poll.id,
                    Vote.user_id == current_user.id
                ).first() is not None
            else:
                poll.user_voted = False
            
            for option in poll.options:
                option.votes_percent = (
                    (option.votes_count / poll.total_votes * 100)
                    if poll.total_votes > 0
                    else 0
                )

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "polls": polls,
                "current_user": current_user
            }
        )
    except Exception as e:
        logger.error(f"Error in home route: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Аутентифікація користувача та встановлення JWT кукі.
    
    Args:
        form_data (OAuth2PasswordRequestForm): Логін та пароль з форми.
        db (Session): Сесія бази даних.
        
    Returns:
        JSONResponse: Дані користувача з встановленими кукі.
        
    Raises:
        HTTPException: Якщо логін або пароль невірні.
    """
    try:
        user = db.query(User).filter(User.username == form_data.username).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Невірний логін або пароль"
            )
        
        valid_password = bcrypt.checkpw(
            form_data.password.encode('utf-8'),
            user.password_hash.encode('utf-8')
        )
        
        if not valid_password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Невірний логін або пароль"
            )
        
        access_token = create_access_token(
            data={"sub": user.username, "is_admin": user.is_admin}
        )
        
        response = JSONResponse(
            content={
                "access_token": access_token,
                "token_type": "bearer",
                "username": user.username,
                "is_admin": user.is_admin
            }
        )
        
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            max_age=1800,
            expires=1800,
            samesite='lax',
            secure=False  
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Помилка при авторизації"
        )
    
@app.get("/register")
async def register_page(request: Request):
    """
    Відображає HTML-сторінку реєстрації нового користувача.
    """
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "title": "Реєстрація"}
    )

@app.post("/api/register")
async def register_user(user_data: UserCreate):
    """
    Реєструє нового користувача в базі даних.
    Перевіряє унікальність логіна та email, хешує пароль.
    
    Args:
        user_data (UserCreate): Схема з даними користувача.
        
    Returns:
        dict: Статус успішної реєстрації.
        
    Raises:
        HTTPException: Якщо користувач вже існує.
    """
    try:
        db = SessionLocal()
        existing_user = db.query(User).filter(
            or_(
                User.username == user_data.username,
                User.email == user_data.email
            )
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Користувач з таким логіном або email вже існує"
            )
        
        hashed_password = bcrypt.hashpw(
            user_data.password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')
        
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password,
            is_active=True,
            is_admin=False
        )
        
        db.add(new_user)
        db.commit()
        
        return {"success": True, "message": "Реєстрація успішна"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Помилка при реєстрації"
        )
    finally:
        db.close()

@app.get("/logout")
async def logout():
    """
    Вихід із системи. Видаляє кукі доступу та перенаправляє на головну.
    """
    response = RedirectResponse(url="/")
    response.delete_cookie("access_token")
    return response

@app.get("/")
async def root(request: Request):
    """
    Альтернативний маршрут для головної сторінки (логіювання доступу).
    """
    logger.info("Accessing root page")
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "user": None,  
            "polls": [],  
            "debug_message": "This is a debug message"
        }
    )

@app.get("/login")
async def login_page(request: Request):
    """
    Відображає HTML-сторінку входу в систему.
    """
    logger.info("Accessing login page")
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "title": "Вхід в систему"}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """
    Глобальний обробник HTTP помилок для всього додатку.
    """
    logger.error(f"HTTP error: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """
    Глобальний обробник непередбачуваних помилок сервера.
    """
    logger.error(f"General error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )

@app.get("/polls/active")
async def get_active_polls(db: Session = Depends(get_db)):
    """
    Отримує список усіх активних опитувань (JSON формат для API).
    
    Returns:
        List[dict]: Масив активних опитувань з варіантами відповідей.
    """
    try:
        polls = (
            db.query(Poll)
            .filter(Poll.is_active == True)
            .all()
        )
        
        result = []
        for poll in polls:
            options = (
                db.query(PollOption)
                .filter(PollOption.poll_id == poll.id)
                .all()
            )
            
            poll_data = {
                "id": poll.id,
                "title": poll.title,
                "description": poll.description,
                "created_at": poll.created_at.isoformat() if poll.created_at else None,
                "ends_at": poll.ends_at.isoformat() if poll.ends_at else None,
                "is_active": poll.is_active,
                "created_by": poll.created_by,
                "options": [
                    {"id": opt.id, "text": opt.text}
                    for opt in options
                ]
            }
            result.append(poll_data)
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting active polls: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Помилка при отриманні голосувань"
        )

@app.get("/api/polls/{poll_id}", response_model=PollSchema)
def read_poll(poll_id: int, db: Session = Depends(get_db)):
    """
    Отримує повну інформацію про конкретне опитування за ID.
    
    Args:
        poll_id (int): Ідентифікатор опитування.
        db (Session): Сесія бази даних.
        
    Returns:
        PollSchema: Схема опитування.
    """
    poll = get_poll(db, poll_id)
    if poll is None:
        raise HTTPException(status_code=404, detail="Poll not found")
    
    for option in poll.options:
        option.votes_count = db.query(func.count(Vote.id))\
            .filter(Vote.option_id == option.id)\
            .scalar()
    poll.total_votes = sum(option.votes_count for option in poll.options)
    return poll

@app.post("/api/polls")
async def create_poll(
    poll_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Створює нове опитування. Доступно лише адміністраторам.
    
    Args:
        poll_data (dict): Дані для створення (назва, опис, варіанти).
        current_user (User): Поточний користувач.
        
    Returns:
        dict: Результат створення з ID нового опитування.
    """
    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Недостатньо прав")
    
    try:
        new_poll = Poll(
            title=poll_data["title"],
            description=poll_data.get("description", ""),
            is_active=True,
            created_by=current_user.id
        )
        db.add(new_poll)
        db.flush()

        for option_data in poll_data.get("options", []):
            option = PollOption(
                poll_id=new_poll.id,
                text=option_data["text"],  
                votes_count=0
            )
            db.add(option)

        db.commit()
        return {"success": True, "id": new_poll.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/api/polls/{poll_id}/options")
async def get_poll_options(poll_id: int, db: Session = Depends(get_db)):
    """
    Отримує лише варіанти відповідей для конкретного опитування.
    """
    try:
        options = db.query(PollOption).filter(PollOption.poll_id == poll_id).all()
        if not options:
            raise HTTPException(status_code=404, detail="Варіанти відповідей не знайдено")
        return {"options": [{"id": opt.id, "text": opt.text} for opt in options]}
    except Exception as e:
        logger.error(f"Error getting poll options: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin")
async def admin_panel(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Відображає панель адміністратора зі статистикою додатку.
    """
    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Доступ заборонено")
    
    stats = {
        "active_polls": db.query(Poll).filter(Poll.is_active == True).count(),
        "total_users": db.query(User).count(),
        "total_votes": db.query(Vote).count()
    }
    
    polls = db.query(Poll).all()
    for poll in polls:
        poll.total_votes = db.query(Vote).filter(Vote.poll_id == poll.id).count()
    
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "current_user": current_user,
            "stats": stats,
            "polls": polls
        }
    )

@app.post("/api/polls/{poll_id}/toggle")
async def toggle_poll_status(
    poll_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Змінює статус опитування (Активне / Закрите). Доступно адмінам.
    """
    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Доступ заборонено")
    
    poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail="Голосування не знайдено")
    
    poll.is_active = not poll.is_active
    db.commit()
    
    return {"success": True}

@app.post("/api/vote")
async def vote(
    vote_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Обробляє голос користувача.
    Перевіряє, чи активне опитування, і чи не голосував користувач раніше.
    
    Args:
        vote_data (dict): Дані голосування (poll_id, option_id).
        current_user (User): Поточний авторизований користувач.
        
    Returns:
        dict: Статус успішного голосування.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Необхідно увійти для голосування")
    
    poll_id = vote_data.get("poll_id")
    option_id = vote_data.get("option_id")
    
    try:
        poll = db.query(Poll).filter(Poll.id == poll_id).first()
        if not poll:
            raise HTTPException(status_code=404, detail="Голосування не знайдено")
            
        if not poll.is_active:
            raise HTTPException(status_code=400, detail="Голосування закрите")

        existing_vote = db.query(Vote).filter(
            Vote.poll_id == poll_id,
            Vote.user_id == current_user.id
        ).first()
        
        if existing_vote:
            raise HTTPException(status_code=400, detail="Ви вже голосували в цьому опитуванні")
        
        option = db.query(PollOption).filter(
            PollOption.id == option_id,
            PollOption.poll_id == poll_id
        ).first()
        
        if not option:
            raise HTTPException(status_code=404, detail="Варіант відповіді не знайдено")

        new_vote = Vote(
            user_id=current_user.id,
            poll_id=poll_id,
            option_id=option_id,
            voted_at=datetime.utcnow()
        )
        db.add(new_vote)
        
        option.votes_count += 1
        
        db.commit()
        return {"success": True, "message": "Ваш голос враховано"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Vote error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/api/polls/{poll_id}/results")
async def get_poll_results(
    poll_id: int,
    db: Session = Depends(get_db)
):
    """
    Отримує результати голосування у JSON форматі (відсотки, кількість голосів).
    """
    try:
        poll = db.query(Poll).filter(Poll.id == poll_id).first()
        if not poll:
            raise HTTPException(
                status_code=404,
                detail="Голосування не знайдено"
            )
        
        results = []
        total_votes = 0
        
        for option in poll.options:
            votes_count = db.query(Vote).filter(
                Vote.option_id == option.id
            ).count()
            total_votes += votes_count
            results.append({
                "option_id": option.id,
                "text": option.text,
                "votes": votes_count
            })
        
        for result in results:
            result["percentage"] = round(
                (result["votes"] / total_votes * 100) if total_votes > 0 else 0,
                1
            )
        
        return {
            "poll_id": poll.id,
            "title": poll.title,
            "total_votes": total_votes,
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Помилка при отриманні результатів: {str(e)}"
        )

@app.get("/archive")
async def archive_page(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Відображає сторінку архіву з закритими опитуваннями.
    """
    try:
        current_user = await get_current_user(request)
        archived_polls = await get_archived_polls(db)
        
        return templates.TemplateResponse(
            "archive.html",
            {
                "request": request,
                "title": "Архів голосувань",
                "current_user": current_user,
                "polls": archived_polls
            }
        )
    except Exception as e:
        logger.error(f"Error rendering archive page: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/polls/archived")
async def get_archived_polls(
    db: Session = Depends(get_db)
):
    """
    Отримує масив закритих (неактивних) опитувань для архіву.
    """
    try:
        archived_polls = db.query(Poll).filter(
            Poll.is_active == False
        ).order_by(Poll.created_at.desc()).all()
        
        polls_data = []
        for poll in archived_polls:
            total_votes = db.query(Vote).filter(
                Vote.poll_id == poll.id
            ).count()
            
            polls_data.append({
                "id": poll.id,
                "title": poll.title,
                "description": poll.description,
                "created_at": poll.created_at,
                "ends_at": poll.ends_at,
                "total_votes": total_votes
            })
        
        return polls_data
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Помилка при отриманні архіву: {str(e)}"
        )

@app.get("/admin")
async def admin_panel(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Дублюючий маршрут адмін-панелі (залишено для сумісності з попереднім кодом).
    """
    if not current_user or not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    all_polls = db.query(Poll).all()
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "user": current_user,
            "polls": all_polls
        }
    )

@app.get("/polls/{poll_id}")
async def view_poll(
    request: Request,
    poll_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Відображає сторінку окремого опитування з деталями та можливістю голосувати.
    """
    poll = get_poll(db, poll_id)
    if poll is None:
        raise HTTPException(status_code=404, detail="Poll not found")
    
    for option in poll.options:
        option.votes_count = db.query(func.count(Vote.id))\
            .filter(Vote.option_id == option.id)\
            .scalar()
    poll.total_votes = sum(option.votes_count for option in poll.options)

    user_voted = False
    if current_user:
        user_voted = db.query(Vote)\
            .filter(Vote.user_id == current_user.id,
                   Vote.poll_id == poll_id)\
            .first() is not None

    return templates.TemplateResponse(
        "poll.html",
        {
            "request": request,
            "user": current_user,
            "poll": poll,
            "user_voted": user_voted
        }
    )

@app.post("/api/register", response_model=UserSchema)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Дублюючий маршрут реєстрації з використанням вбудованої функції сервісу.
    """
    db_user = get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    return create_user(db, user)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="127.0.0.1", 
        port=8000,  
        reload=True,  
        workers=1,  
        log_level="info" 
    )