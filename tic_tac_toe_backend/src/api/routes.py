from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from . import models, db, utils

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def get_current_player(token: str = Depends(oauth2_scheme), db_: Session = Depends(db.get_db)):
    payload = utils.decode_access_token(token)
    if payload is None or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    player = db_.query(db.Player).filter(db.Player.username == payload["sub"]).first()
    if not player:
        raise HTTPException(status_code=401, detail="User not found")
    return player

# ==== Auth Endpoints ====
@router.post("/auth/register", response_model=models.Player, tags=["Auth"])
# PUBLIC_INTERFACE
def register(user: models.PlayerCreate, db_: Session = Depends(db.get_db)):
    """Register a new user/player."""
    if db_.query(db.Player).filter(db.Player.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username taken")
    password_hash = utils.hash_password(user.password)
    new_player = db.Player(username=user.username, password_hash=password_hash)
    db_.add(new_player)
    db_.commit()
    db_.refresh(new_player)
    return models.Player(
        id=new_player.id,
        username=new_player.username,
        created_at=new_player.created_at,
    )

@router.post("/auth/token", response_model=models.Token, tags=["Auth"])
# PUBLIC_INTERFACE
def login(form_data: OAuth2PasswordRequestForm = Depends(), db_: Session = Depends(db.get_db)):
    """Authenticate user and return JWT token."""
    player = db_.query(db.Player).filter(db.Player.username == form_data.username).first()
    if not player or not utils.verify_password(form_data.password, player.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = utils.create_access_token(
        data={"sub": player.username}
    )
    return models.Token(access_token=token, token_type="bearer")

@router.get("/auth/me", response_model=models.Player, tags=["Auth"])
# PUBLIC_INTERFACE
def get_me(current_player: db.Player = Depends(get_current_player)):
    """Get the current logged-in user."""
    return models.Player(
        id=current_player.id,
        username=current_player.username,
        created_at=current_player.created_at,
    )

# ==== Player CRUD ====
@router.get("/players", response_model=list[models.Player], tags=["Players"])
# PUBLIC_INTERFACE
def get_players(skip: int = 0, limit: int = 20, db_: Session = Depends(db.get_db)):
    """Return all registered players."""
    players = db_.query(db.Player).offset(skip).limit(limit).all()
    return [
        models.Player(id=p.id, username=p.username, created_at=p.created_at)
        for p in players
    ]

@router.get("/players/{player_id}", response_model=models.Player, tags=["Players"])
# PUBLIC_INTERFACE
def get_player(player_id: int, db_: Session = Depends(db.get_db)):
    """Get a player by ID."""
    p = db_.query(db.Player).filter(db.Player.id == player_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Player not found")
    return models.Player(id=p.id, username=p.username, created_at=p.created_at)

@router.put("/players/{player_id}", response_model=models.Player, tags=["Players"])
# PUBLIC_INTERFACE
def update_player(player_id: int, update: models.PlayerUpdate, db_: Session = Depends(db.get_db), current_player: db.Player = Depends(get_current_player)):
    """Update current player's info."""
    if player_id != current_player.id:
        raise HTTPException(status_code=403, detail="Can only update your own user")
    player = db_.query(db.Player).filter(db.Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    if update.username:
        if db_.query(db.Player).filter(db.Player.username == update.username).first():
            raise HTTPException(status_code=400, detail="Username taken")
        player.username = update.username
    if update.password:
        player.password_hash = utils.hash_password(update.password)
    db_.commit()
    db_.refresh(player)
    return models.Player(id=player.id, username=player.username, created_at=player.created_at)

@router.delete("/players/{player_id}", status_code=204, tags=["Players"])
# PUBLIC_INTERFACE
def delete_player(player_id: int, db_: Session = Depends(db.get_db), current_player: db.Player = Depends(get_current_player)):
    """Delete user account."""
    if player_id != current_player.id:
        raise HTTPException(status_code=403, detail="Can only delete your own account")
    player = db_.query(db.Player).filter(db.Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    db_.delete(player)
    db_.commit()
    return

# ==== Games CRUD ====
@router.post("/games", response_model=models.Game, tags=["Games"])
# PUBLIC_INTERFACE
def create_game(game: models.GameCreate, current_player: db.Player = Depends(get_current_player), db_: Session = Depends(db.get_db)):
    """Start a new game; opponent can be 'human' or 'computer'."""
    player_o_id = None
    if game.opponent_type == "human":
        pass  # another user can join
    elif game.opponent_type == "computer":
        player_o_id = None  # special computer mode
    else:
        raise HTTPException(400, "Invalid opponent type: must be 'human' or 'computer'")
    new_game = db.Game(
        player_x_id=current_player.id,
        player_o_id=player_o_id,
        board=[[None, None, None], [None, None, None], [None, None, None]],
        turn='X',
        opponent_type=game.opponent_type
    )
    db_.add(new_game)
    db_.commit()
    db_.refresh(new_game)
    return models.Game(
        id=new_game.id,
        player_x_id=new_game.player_x_id,
        player_o_id=new_game.player_o_id,
        board=new_game.board,
        turn=new_game.turn,
        winner=new_game.winner,
        complete=new_game.complete,
        created_at=new_game.created_at
    )

@router.get("/games", response_model=list[models.GameHistoryItem], tags=["Games"])
# PUBLIC_INTERFACE
def list_games(skip: int = 0, limit: int = 20, db_: Session = Depends(db.get_db)):
    """List recent games with summary info."""
    games = db_.query(db.Game).order_by(db.Game.created_at.desc()).offset(skip).limit(limit).all()
    res = []
    for g in games:
        res.append(models.GameHistoryItem(
            id=g.id,
            player_x=g.player_x.username if g.player_x else "Unknown",
            player_o=g.player_o.username if g.player_o else ("Computer" if g.opponent_type == "computer" else "Pending"),
            winner=g.winner,
            created_at=g.created_at
        ))
    return res

@router.get("/games/{game_id}", response_model=models.Game, tags=["Games"])
# PUBLIC_INTERFACE
def get_game(game_id: int, db_: Session = Depends(db.get_db)):
    """Get full info about a game."""
    g = db_.query(db.Game).filter(db.Game.id == game_id).first()
    if not g:
        raise HTTPException(404, "Game not found")
    return models.Game(
        id=g.id,
        player_x_id=g.player_x_id,
        player_o_id=g.player_o_id,
        board=g.board,
        turn=g.turn,
        winner=g.winner,
        complete=g.complete,
        created_at=g.created_at
    )

@router.post("/games/{game_id}/join", response_model=models.Game, tags=["Games"])
# PUBLIC_INTERFACE
def join_game(game_id: int, current_player: db.Player = Depends(get_current_player), db_: Session = Depends(db.get_db)):
    """Join a game as O (human player only, and only if player_o is empty)."""
    g = db_.query(db.Game).filter(db.Game.id == game_id).first()
    if not g:
        raise HTTPException(404, "Game not found")
    if g.opponent_type != "human":
        raise HTTPException(400, "Join is only for human vs human games")
    if g.player_x_id == current_player.id:
        raise HTTPException(400, "Creator can't join as O")
    if g.player_o_id:
        raise HTTPException(409, "Game already has two players")
    g.player_o_id = current_player.id
    db_.commit()
    db_.refresh(g)
    return models.Game(
        id=g.id,
        player_x_id=g.player_x_id,
        player_o_id=g.player_o_id,
        board=g.board,
        turn=g.turn,
        winner=g.winner,
        complete=g.complete,
        created_at=g.created_at
    )

@router.post("/games/{game_id}/move", response_model=models.Game, tags=["Games"])
# PUBLIC_INTERFACE
def play_move(game_id: int, move: models.Move, current_player: db.Player = Depends(get_current_player), db_: Session = Depends(db.get_db)):
    """Make a move in a game (either human or vs computer). Returns new board and winner if any."""
    g = db_.query(db.Game).filter(db.Game.id == game_id).first()
    if not g:
        raise HTTPException(404, "Game not found")
    if g.complete:
        raise HTTPException(400, f"Game is complete, winner: {g.winner}")
    symbol = None
    if g.player_x_id == current_player.id:
        symbol = "X"
    elif g.player_o_id == current_player.id or (g.opponent_type == "computer" and g.player_o_id is None):
        symbol = "O"
    else:
        raise HTTPException(403, "Not your game or not your turn")
    if g.turn != symbol:
        raise HTTPException(400, "Not your turn")
    if not (0 <= move.x < 3 and 0 <= move.y < 3):
        raise HTTPException(400, "Invalid move coordinates")
    board = g.board
    if board[move.x][move.y]:
        raise HTTPException(400, "Cell is not empty")
    board[move.x][move.y] = symbol
    # Save move history
    move_number = sum(1 for row in board for cell in row if cell)
    db_move = db.Move(
        game_id=game_id,
        player_id=current_player.id,
        x=move.x,
        y=move.y,
        symbol=symbol,
        move_number=move_number
    )
    g.board = board
    # Check for winner
    winner = utils.check_winner(board)
    g.complete = False
    if winner:
        g.winner = winner
        g.complete = True
    elif utils.is_board_full(board):
        g.winner = "draw"
        g.complete = True
    else:
        g.turn = "O" if symbol == "X" else "X"
    db_.add(db_move)
    db_.commit()
    db_.refresh(g)
    # --- If vs computer and no winner, make computer move ---
    if g.opponent_type == "computer" and not g.complete and g.turn == "O":
        cx, cy = utils.generate_computer_move(g.board)
        g.board[cx][cy] = "O"
        db_move_comp = db.Move(
            game_id=game_id,
            player_id=None,  # None for computer
            x=cx,
            y=cy,
            symbol="O",
            move_number=move_number+1
        )
        winner = utils.check_winner(g.board)
        if winner:
            g.winner = winner
            g.complete = True
        elif utils.is_board_full(g.board):
            g.winner = "draw"
            g.complete = True
        else:
            g.turn = "X"
        db_.add(db_move_comp)
        db_.commit()
        db_.refresh(g)
    return models.Game(
        id=g.id,
        player_x_id=g.player_x_id,
        player_o_id=g.player_o_id,
        board=g.board,
        turn=g.turn,
        winner=g.winner,
        complete=g.complete,
        created_at=g.created_at
    )

# ==== Game History & Leaderboard ====
@router.get("/history/{player_id}", response_model=list[models.GameHistoryItem], tags=["History"])
# PUBLIC_INTERFACE
def get_player_history(player_id: int, db_: Session = Depends(db.get_db)):
    """Get all games involving a player."""
    games = db_.query(db.Game).filter((db.Game.player_x_id == player_id) | (db.Game.player_o_id == player_id)).order_by(db.Game.created_at.desc()).all()
    res = []
    for g in games:
        res.append(models.GameHistoryItem(
            id=g.id,
            player_x=g.player_x.username if g.player_x else "Unknown",
            player_o=g.player_o.username if g.player_o else ("Computer" if g.opponent_type == "computer" else "Pending"),
            winner=g.winner,
            created_at=g.created_at
        ))
    return res

@router.get("/leaderboard", response_model=list[models.LeaderboardEntry], tags=["Leaderboard"])
# PUBLIC_INTERFACE
def leaderboard(db_: Session = Depends(db.get_db)):
    """Leaderboard based on total wins (excluding draws)."""
    from sqlalchemy import func
    q = db_.query(
        db.Game.winner,
        func.count(db.Game.id).label("win_count")
    ).group_by(db.Game.winner).all()
    # Only X and O (players)
    win_dict = {}
    for row in q:
        winner, cnt = row
        if winner and winner in ("X", "O"):
            win_dict[winner] = cnt
    # correlate to players
    players = db_.query(db.Player).all()
    entries = []
    for p in players:
        wins = 0
        # count games where this player was X and winner was X, or O and winner O
        x_wins = db_.query(db.Game).filter(db.Game.player_x_id == p.id, db.Game.winner == "X").count()
        o_wins = db_.query(db.Game).filter(db.Game.player_o_id == p.id, db.Game.winner == "O").count()
        wins = x_wins + o_wins
        entries.append(models.LeaderboardEntry(player_id=p.id, username=p.username, score=wins))
    entries.sort(key=lambda e: e.score, reverse=True)
    return entries

