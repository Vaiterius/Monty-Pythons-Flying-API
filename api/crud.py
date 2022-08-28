import random
import difflib
from fastapi import HTTPException
from sqlalchemy.orm import Session, query
from sqlalchemy.sql import func

from .models import Script


def clamp(n: int|float, min: int|float, max: int|float):
    """Clamps a number between two inclusive values"""
    if n < min:
        return min
    elif n > max:
        return max
    return n


###############################################################################
# QUOTES
###############################################################################

def get_random_quote(
    db: Session, actor: str|None = None, episode: int|None = None,
    sketch: str|None = None, min_length: int|None = None,
    max_length: int|None = None
) -> dict:
    """Search for a random quote with optional arguments"""
    base_query = db.query(
        Script).filter_by(type="Dialogue").order_by(func.random())
    
    # Apply argument filters if given.
    filters = []
    if episode:
        filters.append(Script.episode == str(episode))
    if actor:
        filters.append(Script.actor.like(actor))
    if sketch:
        NUM_MATCHES_ALLOWED: int = 1
        CUTOFF: float = 0.5
        sketches: list[str] = get_all_sketches(db)
        closest_match = difflib.get_close_matches(
            sketch, sketches, NUM_MATCHES_ALLOWED, CUTOFF)
        if closest_match:
            sketch = closest_match[0]
        filters.append(Script.segment.like(sketch))
    
    MAX_SIZE = 9223372036854775807  # Clamp size to prevent overflow.
    MIN_SIZE = 1
    if min_length:
        min_length = clamp(min_length, MIN_SIZE, MAX_SIZE)
        filters.append(func.length(Script.detail) >= min_length)
    if max_length:
        max_length = clamp(max_length, MIN_SIZE, MAX_SIZE)
        filters.append(func.length(Script.detail) <= max_length)
    quote = base_query.filter(*filters).first()

    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    return {
        "episode": quote.episode,
        "sketch": quote.segment,
        "actor": quote.actor,
        "character": quote.character,
        "quote": quote.detail,
    }


###############################################################################
# PEOPLE
###############################################################################

def get_actors(db: Session) -> list[str]:
    """Return a list of all the actors from the show"""
    return [
        actor.actor for actor in
        (
            db.query(Script.actor).filter(Script.actor.isnot(None))
                                  .group_by(Script.actor)
                                  .order_by(func.count(Script.detail).desc())
        )
        
    ]


def get_characters(db: Session) -> list[str]:
    """Return a list of all the characters played in the show"""
    return [
        character.character for character in
        (
            db.query(Script.character).filter(Script.character.isnot(None))
                                      .group_by(Script.character)
                                      .order_by(func.count(Script.detail)
                                      .desc())
        )
    ]

###############################################################################
# SKETCHES
###############################################################################

# MAIN FUNCTIONS

def get_sketch(
    db: Session, sketch: str|None = None, detailed: bool = False
) -> dict[str, str|list[str]]:
    """Return a sketch's lines and directions"""
    choice: str|None = sketch

    # Query random sketch if no sketch is provided.
    sketches: list[str] = get_all_sketches(db)
    if choice is None:
        choice = random.choice(sketches)
    
    # Get closest matching sketch.
    else:
        NUM_MATCHES_ALLOWED: int = 1
        CUTOFF: float = 0.5
        closest_match = difflib.get_close_matches(
            choice, sketches, NUM_MATCHES_ALLOWED, CUTOFF)
        if closest_match:
            choice = closest_match[0]
    
    sketch = db.query(Script).filter(Script.segment.like(choice))

    # Sketch doesn't exist.
    if not sketch.first():
        raise HTTPException(status_code=404, detail="Sketch not found")
    
    return {
        "episode": sketch.first().episode,
        "episode_name": sketch.first().episode_name,
        "sketch": sketch.first().segment,
        "body": get_formatted_sketch_body(sketch, detailed=detailed)
    }


def get_episode(
    db: Session, number: int|None = None, detailed: bool = False
) -> dict[str, str|list[dict[str, str|list[str]]]]:
    """Search an episode by argument or random if not provided"""
    episode_name: str|None = None

    # Query random episode if no episode number is provided.
    query = None
    if number:
        number = clamp(number, 1, 45)
        query = db.query(Script).filter(Script.episode == number)
    else:
        number = random.randint(1, 45)
        query = db.query(Script).filter(Script.episode == number)
    
    # Episode not found.
    if not query.first():
        raise HTTPException(status_code=404, detail="Episode not found")
    
    episode_name = query.first().episode_name
    sketches: list[str] = get_episode_sketches(db, number)
    body: list[dict[str, str|list[str]]] = []

    # Body will be separated by sketches, with each sketch including its lines;
    # assuming that there is only one "null" sketch per episode, found in the
    # beginning.
    for sketch_name in sketches:
        sketch = None
        if not sketch_name:
            sketch = (db.query(Script).filter_by(episode=number)
                                   .filter(Script.segment
                                   .is_(None)))
        else:
            sketch = (db.query(Script).filter_by(episode=number)
                                         .filter(Script.segment
                                         .like(sketch_name)))
        # Insert the lines belonging to a sketch.
        body.append(
            {
                "sketch": sketch_name,
                "lines": get_formatted_sketch_body(sketch, detailed=detailed)
            }
        )
    
    return {
        "episode": number,
        "episode_name": episode_name,
        "body": body,
    }


def get_nested_seasons(
    db: Session, season: int|None = None
) -> dict[str: dict[str, list[str]]]:
    """Return nested sketches based on their season and episode"""
    # Retrieving a specific season.
    if season:
        if season not in [1, 2, 3, 4]:
            raise HTTPException(status_code=404, detail="Season not found")
        return get_nested_season_sketches(db, season)
    
    # Fetch every season.
    all_season_sketches = {}
    for season in [1, 2, 3, 4]:
        all_season_sketches.update(get_nested_season_sketches(db, season))
    return all_season_sketches


# HELPERS

def get_all_sketches(db: Session, season: int|None = None) -> list[str]:
    """Return list of every sketch in the show, optional from a season"""
    base_query = (db.query(Script.segment).distinct(Script.segment)
                                          .filter(Script.segment.isnot(None)))
    
    if season:  # Filter only sketches from the season.
        if season not in [1, 2, 3, 4]:
            raise HTTPException(status_code=404, detail="Season out of range")
        
        # Fetch sketches that fall into the episodes from the season.
        lower = Script.season_ranges[season - 1][0]
        upper = Script.season_ranges[season - 1][-1]
        base_query = base_query.filter(
            Script.episode.between(lower, upper))
    
    return [sketch.segment for sketch in base_query]


def get_episode_sketches(db: Session, episode: int) -> list[str]:
    """Returns a list of sketches from an episode"""
    if episode < 1 or episode > 45:
        raise HTTPException(status_code=404, detail="Episode out of range")

    return [
        sketch.segment for sketch in
        (db.query(Script.segment).filter_by(episode=episode)
                                 .distinct(Script.segment)
                                 .filter(Script.segment.isnot(None)))
    ]


def get_nested_episode_sketches(
    db: Session, episode: int
) -> dict[str, list[str]]:
    """Return sketches from a particular episode"""
    return {
        f"episode_{episode}": [
            sketch for sketch in
            get_episode_sketches(db, episode)
        ]
    }


def get_nested_season_sketches(
    db: Session, season: int) -> dict[str, list[dict[str, list[str]]]]:
    """Returns a nested list of sketches per episode from a season"""
    return {
        f"season_{season}": [
            get_nested_episode_sketches(db, episode)
            for episode in Script.season_ranges[season - 1]
        ]
    }


def get_formatted_sketch_body(
    sketch: "query.Query[Script]", detailed: bool = False
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

