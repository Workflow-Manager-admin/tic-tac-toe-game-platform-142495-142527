from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

# PUBLIC_INTERFACE
class PlayerBase(BaseModel):
    username: str = Field(..., description="Unique username for the player")

# PUBLIC_INTERFACE
class PlayerCreate(PlayerBase):
    password: str = Field(..., description="Player's password")

# PUBLIC_INTERFACE
class Player(PlayerBase):
    id: int = Field(..., description="Player's unique ID")
    created_at: datetime = Field(..., description="Player created timestamp")

    class Config:
        orm_mode = True

# PUBLIC_INTERFACE
class PlayerLogin(BaseModel):
    username: str = Field(..., description="Username for login")
    password: str = Field(..., description="Password for login")

# PUBLIC_INTERFACE
class Token(BaseModel):
    access_token: str
    token_type: str

# PUBLIC_INTERFACE
class GameBase(BaseModel):
    player_x_id: int
    player_o_id: Optional[int] = None # opponent could be computer or another player

# PUBLIC_INTERFACE
class GameCreate(GameBase):
    opponent_type: str = Field(..., description="Type of opponent: 'human' or 'computer'")

# PUBLIC_INTERFACE
class Move(BaseModel):
    player_id: int
    x: int = Field(..., description="Row 0-2")
    y: int = Field(..., description="Col 0-2")

# PUBLIC_INTERFACE
class BoardState(BaseModel):
    state: List[List[Optional[str]]] = Field(..., description="3x3 board state: 'X', 'O', or None")

# PUBLIC_INTERFACE
class Game(GameBase):
    id: int
    board: List[List[Optional[str]]]
    turn: str
    winner: Optional[str]
    complete: bool
    created_at: datetime

    class Config:
        orm_mode = True

# PUBLIC_INTERFACE
class GameHistoryItem(BaseModel):
    id: int
    player_x: str
    player_o: Optional[str]
    winner: Optional[str]
    created_at: datetime

# PUBLIC_INTERFACE
class LeaderboardEntry(BaseModel):
    player_id: int
    username: str
    score: int

# PUBLIC_INTERFACE
class PlayerUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None

