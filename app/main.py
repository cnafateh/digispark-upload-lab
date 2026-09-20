from fastapi import FastAPI

app = FastAPI(title="Digispark Upload Lab", version="1.0.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "Digispark Upload Lab"}
