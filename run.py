# ============================================================
# run.py
# Purpose: Simple launcher for the FastAPI server.
# Usage:   python run.py
# ============================================================

import uvicorn
# uvicorn -> the ASGI server that runs FastAPI apps.

if __name__ == "__main__":
    # "app.main:app" means: module app/main.py, variable `app`.
    # host 0.0.0.0 -> accessible from other devices on your LAN.
    # port 8000    -> default FastAPI port.
    # reload=True  -> auto-restart on code changes (dev only).
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)