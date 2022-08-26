from fastapi import FastAPI, Depends
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session

from . import crud, models
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

holy_api = FastAPI()


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


@holy_api.get("/quotes")
def get_random_quote(
    actor: str|None = None, episode: int|None = None,
    sketch: str|None = None, db: Session = Depends(get_db)
):
    """Get a random quote from the show"""
    return crud.get_random_quote(
        db, actor=actor, episode=episode, sketch=sketch)


@holy_api.get("/episodes/random")
def get_random_episode(db: Session = Depends(get_db)):
    """Get a random episode from the show"""
    return crud.get_episode(db)


@holy_api.get("/episodes/{episode_num}")
def get_episode(
    number: int|None = None, detailed: bool = False,
    db: Session = Depends(get_db)
):
    """Get an episode from the show; optional: detailed view"""
    return crud.get_episode(db, number=number, detailed=detailed)


@holy_api.get("/sketches")
def get_all_sketches(nested: bool = False, db: Session = Depends(get_db)):
    """Get all sketches from the show (sans lines)"""
    if nested:
        return crud.get_nested_sketches(db)
    return crud._get_all_sketches(db)


@holy_api.get("/sketches/random")
def get_random_sketch(detailed: bool = False, db: Session = Depends(get_db)):
    """Get a random sketch with lines from the show; optional: detailed view"""
    return crud.get_sketch(db, detailed=detailed)


@holy_api.get("/sketches/{sketch}")
def get_sketch(
    sketch: str|None = None, detailed: bool = False,
    db: Session = Depends(get_db)
):
    """Get a sketch from the show; optional: detailed view """
    return crud.get_sketch(db, sketch=sketch, detailed=detailed)

