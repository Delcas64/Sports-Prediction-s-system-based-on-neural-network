from fastapi import FastAPI,Query
from fastapi.staticfiles import StaticFiles  
from starlette.responses import FileResponse
from app.api import matches, prediction
from app.services.nba_api import get_upcoming_matches
from fastapi.middleware.cors import CORSMiddleware
import os


app = FastAPI(title="NBA Match Predictor")


app.include_router(matches.router)
app.include_router(prediction.router)


# ← CAMBIO AQUÍ: ruta absoluta a statics/ (hermana de app/)
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
# Servir frontend estático

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def read_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    return FileResponse(index_path)



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)