from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
import random
from typing import List, Optional

SECRET_KEY = "supersecret"  # Use env for production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def generate_computer_move(board: List[List[Optional[str]]]) -> (int, int):
    empty_cells = [(i, j) for i in range(3) for j in range(3) if not board[i][j]]
    if not empty_cells:
        return None
    return random.choice(empty_cells)

def check_winner(board: List[List[Optional[str]]]) -> Optional[str]:
    # Check rows, columns, diagonals
    for symbol in ["X", "O"]:
        for i in range(3):
            if all(cell == symbol for cell in board[i]):  # row
                return symbol
            if all(board[r][i] == symbol for r in range(3)):  # column
                return symbol
        # diagonals
        if all(board[i][i] == symbol for i in range(3)):
            return symbol
        if all(board[i][2 - i] == symbol for i in range(3)):
            return symbol
    # No winner
    return None

def is_board_full(board: List[List[Optional[str]]]) -> bool:
    return all(cell for row in board for cell in row)

