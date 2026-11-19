from fastapi import FastAPI

app = FastAPI(title="CSV Insights API")


@app.get("/health")
def health():
    return {"status": "ok"}