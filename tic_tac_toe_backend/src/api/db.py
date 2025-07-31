import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Get DB config from environment variables (see README and env setup)
POSTGRES_URL = os.getenv("POSTGRES_URL")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_URL}:{POSTGRES_PORT}/{POSTGRES_DB}"

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Player(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    games_x = relationship("Game", back_populates="player_x", foreign_keys='Game.player_x_id')
    games_o = relationship("Game", back_populates="player_o", foreign_keys='Game.player_o_id')

class Game(Base):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True, index=True)
    player_x_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    player_o_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    board = Column(JSON, default=lambda: [[None, None, None], [None, None, None], [None, None, None]])
    turn = Column(String, default='X')
    winner = Column(String, nullable=True)
    complete = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    opponent_type = Column(String, default="human")

    player_x = relationship("Player", back_populates="games_x", foreign_keys=[player_x_id])
    player_o = relationship("Player", back_populates="games_o", foreign_keys=[player_o_id])
    moves = relationship("Move", back_populates="game", cascade="all, delete-orphan")

class Move(Base):
    __tablename__ = "moves"
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    symbol = Column(String, nullable=False)
    move_number = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    game = relationship("Game", back_populates="moves")

# Useful for dependency injection in FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_all_tables():
    # Used for development & setup
    Base.metadata.create_all(bind=engine)

