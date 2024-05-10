import os

import fastapi
from .sensors.controller import router as sensorsRouter
from yoyo import read_migrations
from yoyo import get_backend

backend = get_backend('postgresql://timescale:timescale@timescale:5433/timescale')
path = os.path.dirname(os.path.realpath('migrations_ts/migrations_ts.sql'))
migrations = read_migrations(path)

with backend.lock():
    # Apply any outstanding migrations
    backend.apply_migrations(backend.to_apply(migrations))

app = fastapi.FastAPI(title="Senser", version="0.1.0-alpha.1")

#TODO: Apply new TS migrations using Yoyo
#Read docs: https://ollycope.com/software/yoyo/latest/

app.include_router(sensorsRouter)

@app.get("/")
def index():
    #Return the api name and version
    return {"name": app.title, "version": app.version}
