from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv
from .generator import build_comic

load_dotenv()
app = FastAPI(title="ComicForge AI Comic Studio", version="1.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class ComicRequest(BaseModel):
    prompt: str
    character: str
    setting: str
    tone: str
    art_style: str

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate", response_class=HTMLResponse)
async def generate(request: Request, prompt: str=Form(...), character: str=Form(...), setting: str=Form(...), tone: str=Form(...), art_style: str=Form(...)):
    panels, pdf = build_comic(prompt, character, setting, tone, art_style)
    return templates.TemplateResponse("preview.html", {"request":request,"panels":panels,"pdf":pdf,"character":character,"prompt":prompt})

@app.post("/generate-comic/json")
async def generate_json(payload: ComicRequest):
    panels, pdf = build_comic(payload.prompt,payload.character,payload.setting,payload.tone,payload.art_style)
    return JSONResponse({"success":True,"panels":panels,"pdf":pdf})

@app.get("/health")
async def health():
    return {"status":"ok","service":"ComicForge"}
