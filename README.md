# Monty Python's Flying API

**A tribute to this legendary comedy troupe**

This RESTful API serves sketch quotes and dialogue from the original TV series *Monty Python's Flying Circus*. Utilizes [FastAPI](https://fastapi.tiangolo.com/) and runs on [Uvicorn](https://www.uvicorn.org/). Deployed with [Docker](https://www.docker.com/) hosted on [Fly.io](https://fly.io/).

## Usage
Endpoints are prefixed with `/v1/` or whatever version it's currently on.

Head to `/v1/docs` or `/v1/redoc` for a fully-detailed view of each URL endpoint.

The app is currently dockerized on
```
https://monty-pythons-flying-api.fly.dev/v1/
```

### Examples
`/v1/quotes/random`
```
{
  "episode": 15,
  "sketch": "The Spanish Inquisition",
  "actor": "Graham Chapman",
  "character": "Reg",
  "quote": "I didn't expect a kind of Spanish Inquisition."
}
```

With optional arguments

`/v1/quotes/random?episode=33&actor=john cleese&max_length=30`
```
{
  "episode": 33,
  "sketch": "Cheese shop",
  "actor": "John Cleese",
  "character": "Mousebender",
  "quote": "I want to buy some cheese."
}
```

Sketches from an episode

`/v1/sketches/episode/32`
```
[
  "Tory Housewives Clean-up Campaign",
  "Gumby brain specialist",
  "The Minister for not listening to people",
  "Tuesday documentary/children's story/party political broadcast",
  "Expedition to Lake Pahoe",
  "The silliest interview we've ever had",
  "The silliest sketch we've ever done"
]
```

Dialogue from a sketch

`/v1/sketches/random`

```
{
  "episode": 32,
  "episode_name": "Episode Thirty-two",
  "sketch": "The silliest interview we've ever had",
  "body": [
    "*Cut to an interview set.*",
    "Interviewer: The Magna Carta - was it a document signed at Runnymede in 1215 by King John pledging independence to the English barons, or was it a piece of chewing gum on a bedspread in Dorset? The latter idea is the brainchild of a man new to the field of historical research. Mr Badger, why - why are you on this programme?",
    "*Pull back to show Mr Badger. He wears a flat cap and has a Scots accent.*",
    "Badger: Well, I think I can answer this question most successfully in mime.",
    "*mimes incomprehensibly*",
    "Interviewer: But why Dorset?",
    "Badger: Well, I have for a long time been suffering from a species of brain injury which I incurred during the rigours of childbirth, and I'd like to conclude by putting my finger up my nose.",
    "Interviewer: Mr Badger, I think you're the silliest person we've ever had on this programme, and so I'm going to ask you to have dinner with me."
  ]
}
```

## Database
All the scripts are stored in a SQLite database that was downloaded from this [dataset](https://www.kaggle.com/datasets/allank/monty-python-flying-circus). The HTML used to create this was originally sourced from this [website](http://www.ibras.dk/montypython/justthewords.htm).

Schema:

```
CREATE TABLE IF NOT EXISTS "scripts" (
"index" INTEGER,
  "episode" INTEGER,
  "episode_name" TEXT,
  "segment" TEXT,
  "type" TEXT,
  "actor" TEXT,
  "character" TEXT,
  "detail" TEXT,
  "record_date" TIMESTAMP,
  "series" TEXT,
  "transmission_date" TIMESTAMP
);
CREATE INDEX "ix_scripts_index"ON "scripts" ("index");
```

## Other
If there is out there a database containing scripts from *Monty Python and The Holy Grail*, *Monty Python's Life of Brian*, or any of their other movies, _**please**_ let me know! Or if you are making one, even better!

##### **Disclaimer**: This API is not affiliated, associated, authorized, endorsed by, or officially connected in any way with Python (Monty) Pictures Limited nor does it claim to be. All material is respectfully copyright to them.