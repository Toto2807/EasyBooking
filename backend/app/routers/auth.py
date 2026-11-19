"""Inscription, connexion et profil."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import User
from ..schemas import LoginIn, TokenOut, UserCreate, UserOut
from ..security import create_access_token, dummy_hash, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if db.scalar(select(User.id).where(User.email == payload.email)):
        raise HTTPException(status_code=409, detail="Un compte existe déjà avec cet e-mail")
    if db.scalar(select(User.id).where(func.lower(User.username) == payload.username.lower())):
        raise HTTPException(status_code=409, detail="Ce nom d'utilisateur est déjà pris")

    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:  # deux inscriptions simultanées avec le même e-mail
        db.rollback()
        raise HTTPException(status_code=409, detail="Un compte existe déjà avec cet e-mail")
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email))
    # On vérifie toujours un hash (même factice) pour ne pas révéler si l'e-mail existe via le temps de réponse.
    password_ok = verify_password(payload.password, user.password_hash if user else dummy_hash())
    if user is None or not password_ok:
        raise HTTPException(status_code=401, detail="E-mail ou mot de passe incorrect")
    return TokenOut(
        access_token=create_access_token(user.id),
        user=UserOut.model_validate(user),
    )


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
