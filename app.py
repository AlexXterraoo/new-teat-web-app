from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="RailVPN Panel")

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "used_traffic": "32.5 GB",
        "total_traffic": "100 GB",
        "traffic_percent": 32.5,
        "days_left": "20",
        "expire_date": "2026/09/15",
        "sub_url": "https://railvpn-production.up.railway.app/sub/your-uuid-here"
    })
