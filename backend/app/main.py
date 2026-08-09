from app.database import engine
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {
        "message": "Intelligent Data Quality Assessment and Anomaly Detection Framework"
    }