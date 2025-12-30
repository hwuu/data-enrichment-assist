"""GaussDB Operations Ticket Viewer - FastAPI App"""
import json
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from config import DATABASE_CONFIG, SERVER_HOST, SERVER_PORT
from database import create_database

app = FastAPI(title="GaussDB Ops Viewer", description="运维工单浏览器")

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# Configure Jinja2 to not escape unicode in tojson
templates.env.policies['json.dumps_kwargs'] = {'ensure_ascii': False}

# Initialize database
db = create_database(DATABASE_CONFIG)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main page - loads only ticket summaries."""
    tickets = db.get_ticket_list()

    # Extract unique values for filters
    issue_types = sorted(set(t['issueType'] for t in tickets))
    owners = sorted(set(t['owner'] for t in tickets))

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "tickets": tickets,
            "issue_types": issue_types,
            "owners": owners
        }
    )


@app.get("/api/tickets")
async def api_tickets():
    """API endpoint for tickets."""
    return db.get_all_tickets()


@app.get("/api/tickets/{process_id}")
async def api_ticket_detail(process_id: str):
    """API endpoint for single ticket."""
    ticket = db.get_ticket_by_id(process_id)
    if ticket:
        return ticket
    return {"error": "not found"}


@app.get("/api/tickets/{process_id}/review")
async def api_get_review(process_id: str):
    """Get review for a ticket."""
    review = db.get_ticket_review(process_id)
    if review:
        return review
    return {"processId": process_id, "content": "", "createTime": None, "updateTime": None}


@app.post("/api/tickets/{process_id}/review")
async def api_save_review(process_id: str, request: Request):
    """Save review for a ticket."""
    body = await request.json()
    content = body.get("content", "")
    review = db.save_ticket_review(process_id, content)
    return review


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
