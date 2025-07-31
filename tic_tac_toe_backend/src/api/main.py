from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import routes, db

openapi_tags = [
    {"name": "Auth", "description": "User registration, login, authentication"},
    {"name": "Players", "description": "CRUD for player accounts"},
    {"name": "Games", "description": "Create, join, and play Tic Tac Toe games"},
    {"name": "History", "description": "View game history for a player"},
    {"name": "Leaderboard", "description": "Overall player leaderboard"},
]

app = FastAPI(
    title="Tic Tac Toe API",
    description="Backend API for a Tic Tac Toe game, offering user management, auth, multiplayer and single-player (vs computer) modes, game records, history, and leaderboard.",
    version="1.0.0",
    openapi_tags=openapi_tags
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    db.create_all_tables()

@app.get("/", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {"message": "Healthy"}

app.include_router(routes.router)
