"""GaussDB Operations Ticket Viewer - FastAPI App"""
import sqlite3
import json
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="GaussDB Ops Viewer", description="运维工单浏览器")

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")
DATABASE = BASE_DIR / "gaussdb_ops.db"


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def get_all_tickets():
    """Get all tickets with classification info."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT T2."流程ID", C."issueType", C."owner", T2.create_time, T2.update_time,
               T2."问题现象", T2."问题根因", T2."分析过程", T2."解决方案",
               T2.diff_score, T2."得分", T2."理由"
        FROM operations_kb as T2, ticket_classification_2512 as C
        WHERE T2."流程ID" = C."processId"
        ORDER BY T2.update_time DESC, T2.create_time DESC
    ''')
    rows = cursor.fetchall()
    conn.close()

    tickets = []
    for row in rows:
        tickets.append({
            'processId': row[0],
            'issueType': row[1],
            'owner': row[2],
            'createTime': row[3],
            'updateTime': row[4],
            'problem': row[5],
            'rootCause': row[6],
            'analysis': json.loads(row[7]) if row[7] else [],
            'solution': json.loads(row[8]) if row[8] else [],
            'diffScore': row[9],
            'score': row[10],
            'reason': row[11]
        })
    return tickets


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main page."""
    tickets = get_all_tickets()

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
    return get_all_tickets()


@app.get("/api/tickets/{process_id}")
async def api_ticket_detail(process_id: str):
    """API endpoint for single ticket."""
    tickets = get_all_tickets()
    for t in tickets:
        if t['processId'] == process_id:
            return t
    return {"error": "not found"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=3011)
