from fastapi import FastAPI

app = FastAPI(title="DietSheet")


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "ok"}
