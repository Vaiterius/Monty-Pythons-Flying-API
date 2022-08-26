import random

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from . import models


# HELPERS #

def _get_all_sketches(db: Session) -> list[str]:
    """Return list of every sketch in the show"""
    return [
        sketch.segment for sketch in
        (db.query(models.Script.segment)
                   .distinct(models.Script.segment)
                   .filter(models.Script.segment.isnot(None)))
    ]


def _get_formatted_sketch_body(
    sketch: dict, detailed: bool = False
) -> list[dict[str, str]]:
    """Return lines of a sketch in detailed or default view"""
    if detailed:
        return [  # Breaks up each line's info.
            {
                "type": line.type,
                "actor": line.actor,
                "character": line.character,
                "detail": line.detail
            }
            for line in sketch
        ]
    else:
        return [  # Condense into one line depending on dialogue or direction.
            f"{line.character}: {line.detail}"
            if (line.type == "Dialogue") else
            f"*{line.detail}*"
            for line in sketch
        ]


def _get_episode_sketch(db: Session, episode: int) -> list[str]:
    """Returns a list of sketches from an episode"""
    return [
        sketch.segment for sketch in
        (db.query(models.Script.segment)
                   .filter_by(episode=episode)
                   .distinct(models.Script.segment))
    ]


# MAIN FUNCTIONS #

def get_sketch(
    db: Session, sketch: str|None = None, detailed: bool = False
) -> dict[str, str|list[str]]:
    """Return a sketch's lines and directions.
        
    Args:
        sketch: Include name of sketch.
        detailed: View more details of each line of sketch.

    Returns:
        dict: The lines and info of a particular sketch.
    
    Raises:
        HTTPException: Searched-for sketch does not exist.

    """
    # Query random sketch if no sketch is provided.
    choice: str|None = sketch
    if choice is None:
        sketches: list[str] = _get_all_sketches(db)
        choice = random.choice(sketches)
    sketch = db.query(models.Script).filter(models.Script.segment.like(choice))

    # Sketch doesn't exist.
    if not sketch.first():
        raise HTTPException(status_code=404, detail="Sketch not found")
    
    return {
        "sketch": sketch.first().segment,
        "episode": sketch.first().episode,
        "episode_name": sketch.first().episode_name,
        "body": _get_formatted_sketch_body(sketch, detailed=detailed)
    }


def get_random_quote(
    db: Session, actor: str|None = None, episode: int|None = None,
    sketch: str|None = None
) -> dict:
    """Search for a random quote with optional arguments.
            
    Args:
        actor: Search by Monty Python actor.
        episode: Search by episode.

    Return:
        dict: The random quote of actor or from episode if provided.
    
    Raises:
        HTTPException: Could not find a quote queried for.

    """
    base_query = db.query(
        models.Script).filter_by(type="Dialogue").order_by(func.random())
    
    # Apply argument filters if given.
    filters = []
    if episode:
        filters.append(models.Script.episode == str(episode))
    if actor:
        filters.append(models.Script.actor.like(actor))
    if sketch:
        filters.append(models.Script.segment.like(sketch))
    quote = base_query.filter(*filters).first()

    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    return {
        "episode": quote.episode,
        "sketch": quote.segment,
        "actor": quote.actor,
        "quote": quote.detail,
    }


def get_episode(
    db: Session, number: int|None = None, detailed: bool = False
) -> dict[str, str|list[dict[str, str|list[str]]]]:
    """Search an episode by argument or random if not provided.

    Args:
        number: Search episode by its number.
        detailed: View more detail of lines of each episode's sketch.

    Returns:
        dict: The episode's info along with its sketches' lines.
    
    Raises:
        HTTPException: Searched episode could not be found.
    
    """
    episode_name: str|None = None

    # Query random episode if no episode number is provided.
    query = None
    if number:
        query = db.query(models.Script).filter(models.Script.episode == str(number))
    else:
        number = random.randint(1, 45)
        query = db.query(models.Script).filter(models.Script.episode == number)
    
    # Episode not found.
    if not query.first():
        raise HTTPException(status_code=404, detail="Episode not found")
    
    sketches: list[str] = _get_episode_sketch(db, number)
    body: list[dict[str, str|list[str]]] = []

    # Body will be separated by sketches, with each sketch including its lines;
    # assuming that there is only one "null" sketch per episode, found in the
    # beginning.
    for sketch_name in sketches:
        sketch = None
        if not sketch_name:
            sketch = (db.query(models.Script).filter_by(episode=number)
                                   .filter(models.Script.segment
                                   .is_(None)))
        else:
            sketch = (db.query(models.Script).filter_by(episode=number)
                                         .filter(models.Script.segment
                                         .like(sketch_name)))
        # Insert the lines belonging to a sketch.
        body.append(
            {
                "sketch": sketch_name,
                "lines": _get_formatted_sketch_body(sketch, detailed=detailed)
            }
        )
    
    return {
        "episode": number,
        "episode_name": episode_name,
        "body": body,
    }


# TODO: options: list of sketches or nested sketches.
def get_nested_sketches(
    db: Session, season: int|None = None,
    episode: int|None = None
) -> dict[str: dict[str, list[str]]]:
    """Return nested sketches based on their season and episode.
    
    Args:
        season: TODO
        episode: TODO
    
    Returns:
        dict: The show's hierarchy in season->episode->sketch form.
    
    """
    return {
        "season_1": {
            f"episode_{ep}": [
                sketch for sketch in
                _get_episode_sketch(db, ep)
            ] for ep in range(1, 14)
        },
        "season_2": {
            f"episode_{ep}": [
                sketch for sketch in
                _get_episode_sketch(db, ep)
            ] for ep in range(14, 27)
        },
        "season_3": {
            f"episode_{ep}": [
                sketch for sketch in
                _get_episode_sketch(db, ep)
            ] for ep in range(27, 40)
        },
        "season_4": {
            f"episode_{ep}": [
                sketch for sketch in
                _get_episode_sketch(db, ep)
            ] for ep in range(40, 46)
        },
    }

