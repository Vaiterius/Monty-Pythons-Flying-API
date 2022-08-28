import json
from typing import Any

from fastapi import FastAPI, Depends
from starlette.responses import Response, RedirectResponse
from sqlalchemy.orm import Session

from . import crud, models
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

holy_api = FastAPI()


# Pretty print JSON response.
class PrettyJSONResponse(Response):
    media_type = "application/json"

    def render(self, content: Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=4,
            separators=(", ", ": "),
        ).encode("utf-8")


# Dependency.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  # After request.


@holy_api.get("/")
def get_api_usage():
    """Redirect to docs for API usage"""
    return RedirectResponse(url="/docs")


@holy_api.get("/quotes", response_class=PrettyJSONResponse)
def get_random_quote(
    actor: str|None = None, episode: int|None = None,
    sketch: str|None = None, db: Session = Depends(get_db)
):
    """Get a random quote from the show"""
    return crud.get_random_quote(
        db, actor=actor, episode=episode, sketch=sketch)


@holy_api.get("/actors", response_class=PrettyJSONResponse)
def get_actors(db: Session = Depends(get_db)):
    """Get a list of all the actors from the show"""
    return crud.get_actors(db)


@holy_api.get("/characters", response_class=PrettyJSONResponse)
def get_characters(db: Session = Depends(get_db)):
    """Get a list of all the characters from the show"""
    return crud.get_characters(db)


@holy_api.get("/episodes/random", response_class=PrettyJSONResponse)
def get_random_episode(db: Session = Depends(get_db)):
    """Get a random episode from the show"""
    return crud.get_episode(db)


@holy_api.get("/episodes/{episode_num}", response_class=PrettyJSONResponse)
def get_episode(
    number: int|None = None, detailed: bool = False,
    db: Session = Depends(get_db)
):
    """Get an episode from the show; optional: detailed view"""
    return crud.get_episode(db, number=number, detailed=detailed)


@holy_api.get("/sketches", response_class=PrettyJSONResponse)
def get_all_sketches(nested: bool = False, db: Session = Depends(get_db)):
    """Get all sketches from the show (sans lines)"""
    if nested:
        return crud.get_nested_seasons(db)
    return crud.get_all_sketches(db)


@holy_api.get("/sketches/random", response_class=PrettyJSONResponse)
def get_random_sketch(detailed: bool = False, db: Session = Depends(get_db)):
    """Get a random sketch with lines from the show; optional: detailed view"""
    return crud.get_sketch(db, detailed=detailed)


@holy_api.get("/sketches/season/{season}", response_class=PrettyJSONResponse)
def get_all_sketches(season: int, nested: bool = False, db: Session = Depends(get_db)):
    """Get all sketches from a particular season (sans lines)"""
    if nested:
        return crud.get_nested_seasons(db, season)
    return crud.get_all_sketches(db, season=season)


@holy_api.get("/sketches/episode/{episode}", response_class=PrettyJSONResponse)
def get_all_sketches(episode: int, db: Session = Depends(get_db)):
    """Get all sketches from a particular episode (sans lines)"""
    return crud.get_episode_sketches(db, episode)


@holy_api.get("/sketches/sketch/{sketch}", response_class=PrettyJSONResponse)
def get_sketch(
    sketch: str|None = None, detailed: bool = False,
    db: Session = Depends(get_db)
):
    """Get a sketch from the show; optional: detailed view """
    return crud.get_sketch(db, sketch=sketch, detailed=detailed)

