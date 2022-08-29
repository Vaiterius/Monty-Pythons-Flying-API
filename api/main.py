import json
from typing import Any

from fastapi import FastAPI, Depends
from fastapi_versioning import VersionedFastAPI, version
from starlette.responses import Response, RedirectResponse
from sqlalchemy.orm import Session

from . import crud, models
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

holy_api = FastAPI(
    title="Monty Python's Flying API",
    description="And now for something completely different...")


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
@version(1)
def get_api_usage():
    """Redirect to v1 docs for API usage"""
    return RedirectResponse(url="/v1/docs")


@holy_api.get("/actors", response_class=PrettyJSONResponse)
@version(1)
def get_actors(db: Session = Depends(get_db)):
    """Get a list of all the actors from the show"""
    return crud.get_actors(db)


@holy_api.get("/characters", response_class=PrettyJSONResponse)
@version(1)
def get_characters(db: Session = Depends(get_db)):
    """Get a list of all the characters from the show"""
    return crud.get_characters(db)


@holy_api.get("/quotes/random", response_class=PrettyJSONResponse)
@version(1)
def get_random_quote(
    actor: str|None = None, episode: int|None = None,
    sketch: str|None = None, min_length: int|None = None,
    max_length: int|None = None,
    db: Session = Depends(get_db)
):
    """Get a random quote.
            
    Args (optional):
    
    `actor`: Search by Monty Python actor.
        
    `episode`: Search by episode number.
    
    `sketch`: Search by sketch name. Or at least the closest match to it.
    
    `min_length`: Provide minimum quote length.
    
    `max_length`: Provide maximum quote length.
    
    Returns:
    
    The random quote along with its author, episode, and sketch.

    Raises:
    
    `HTTPException`: Could not find close enough quote queried for.

    """
    return crud.get_random_quote(
        db, actor=actor, episode=episode, sketch=sketch,
        min_length=min_length, max_length=max_length)


@holy_api.get("/episodes/random", response_class=PrettyJSONResponse)
@version(1)
def get_random_episode(detailed: bool = False, db: Session = Depends(get_db)):
    """Get a random episode.

    Args:
    
    `detailed`: Switch to view more line details of each episode's sketch,
                including its type of line, actor played, and character played,
                if applicable.

    Returns:
    
    The episode's info along with its sketches' lines.
    
    """
    return crud.get_episode(db, detailed=detailed)


@holy_api.get("/episodes/{episode}", response_class=PrettyJSONResponse)
@version(1)
def get_episode(
    episode: int, detailed: bool = False,
    db: Session = Depends(get_db)
):
    """Get an episode by number.

    Args:
    
    `episode`: Search by episode number.
    
    `detailed`: Switch to view more line details of each episode's sketch,
                including its type of line, actor played, and character played,
                if applicable.

    Returns:
    
    The episode's directions and dialogue OR in a more detailed view.
    
    Raises:
    
    `HTTPException`: Searched episode could not be found.
    
    """
    return crud.get_episode(db, number=episode, detailed=detailed)


@holy_api.get("/sketches", response_class=PrettyJSONResponse)
@version(1)
def get_all_sketches(nested: bool = False, db: Session = Depends(get_db)):
    """Get all sketches from the show.
    
    Args:
    
    `nested`: View sketches parented to their respective episode and season.
    
    Returns:
    
    The list of sketches OR if nested, show's hierarchy in
    season->episode->sketch form.
    
    """
    if nested:
        return crud.get_nested_seasons(db)
    return crud.get_all_sketches(db)


@holy_api.get("/sketches/random", response_class=PrettyJSONResponse)
@version(1)
def get_random_sketch(detailed: bool = False, db: Session = Depends(get_db)):
    """Get a random sketch.
        
    Args:
    
    `detailed`: Switch to view more line details of each episode's sketch,
                including its type of line, actor played, and character played,
                if applicable.

    Returns:
    
    The directions and dialogue from the sketch OR in a more detailed view.

    """
    return crud.get_sketch(db, detailed=detailed)


@holy_api.get("/sketches/season/{season}", response_class=PrettyJSONResponse)
@version(1)
def get_season_sketches(
    season: int, nested: bool = False, db: Session = Depends(get_db)
):
    """Get all sketches from a particular season.
    
    Args:
    
    `season`: Search by season number.
    
    `nested`: View the sketch parented to their respective episode and season.
    
    Returns:
    
    The list of sketches OR if nested, show's hierarchy in
    season->episode->sketch form.
    
    Raises:
    
    `HTTPException`: Season number passed in was not valid.
    
    """
    if nested:
        return crud.get_nested_seasons(db, season)
    return crud.get_all_sketches(db, season=season)


@holy_api.get("/sketches/episode/{episode}", response_class=PrettyJSONResponse)
@version(1)
def get_episode_sketches(episode: int, db: Session = Depends(get_db)):
    """Get all sketches from a particular episode.
    
    Args:
    
    `episode`: Search by episode number.
    
    Returns:
    
    A list of sketches from the episode.
    
    Raises:
    
    `HTTPException`: Provided number not in valid range.
    
    """
    return crud.get_episode_sketches(db, episode)


@holy_api.get("/sketches/sketch/{sketch}", response_class=PrettyJSONResponse)
@version(1)
def get_sketch(
    sketch: str|None = None, detailed: bool = False,
    db: Session = Depends(get_db)
):
    """Get a particular sketch from the show.
        
    Args:
    
    `sketch`: Search by name of sketch. Or at least the closest match to it.
    
    `detailed`: Switch to view more line details of each episode's sketch,
                including its type of line, actor played, and character played,
                if applicable.

    Returns:
    
    The directions and dialogue from the sketch OR in a more detailed view.
    
    Raises:
    
    `HTTPException`: Provided sketch does not exist or there were no close
                     matches.

    """
    return crud.get_sketch(db, sketch=sketch, detailed=detailed)


# Wrap for API versioning.
holy_api = VersionedFastAPI(
    holy_api,
    version_format="{major}", prefix_format="/v{major}",
    enable_latest=True)
