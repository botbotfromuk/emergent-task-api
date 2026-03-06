"""
FastAPI entry point.

Run:   uv run uvicorn main:app --reload
Docs:  http://localhost:8000/docs
"""

from tasks.wiring import fastapi_app as app  # noqa: F401

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
