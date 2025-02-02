from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# 静的ファイルのルート設定
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def get_index():
    html = Path("templates/index.html").read_text(encoding="utf-8")
    return HTMLResponse(content=html, status_code=200)


