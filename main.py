from fastapi import FastAPI
from pydantic import BaseModel
from logbook import backfill_logs, load_syllabi
from routine import routine
from progress_dashboard import show_logbook
from logbook import log_session_manual
from logbook import log_session_manual, calculate_progress, show_logbook

app = FastAPI(title="Class Log API")

# Request models
class BackfillRequest(BaseModel):
    subject: str
    start_date: str
    end_date: str
    holidays: list[str] = []

class BackfillAllRequest(BaseModel):
    start_date: str
    end_date: str
    holidays: list[str] = []

@app.get("/syllabi")
def get_syllabi():
    """Return all subjects and metadata."""
    return load_syllabi()

@app.post("/backfill")
def backfill_subject(req: BackfillRequest):
    """Backfill a single subject."""
    syllabi = load_syllabi()
    subject = next((s for s in syllabi if s["subject"] == req.subject), None)
    if not subject:
        return {"error": f"Subject {req.subject} not found"}
    backfill_logs(subject, req.start_date, req.end_date, routine, req.holidays)
    return {"status": "success", "subject": req.subject}

@app.post("/backfill_all")
def backfill_all(req: BackfillAllRequest):
    """Backfill all subjects."""
    syllabi = load_syllabi()
    for subject in syllabi:
        backfill_logs(subject, req.start_date, req.end_date, routine, req.holidays)
    return {"status": "success", "subjects": [s["subject"] for s in syllabi]}

# Progress endpoint
@app.get("/progress/{subject}")
def get_progress(subject: str):
    syllabi = load_syllabi()
    subj = next((s for s in syllabi if s["subject"] == subject), None)
    if not subj:
        return {"error": f"Subject {subject} not found"}
    return calculate_progress(subj)

# Logbook viewer endpoint
@app.get("/logbook/{subject}")
def get_logbook(subject: str):
    return show_logbook(subject)

# Manual logging endpoint
class ManualLogRequest(BaseModel):
    subject: str
    section: str
    date_bs: str
    time_from: str
    time_to: str

@app.post("/log_manual")
def log_manual(req: ManualLogRequest):
    syllabi = load_syllabi()
    subj = next((s for s in syllabi if s["subject"] == req.subject), None)
    if not subj:
        return {"error": f"Subject {req.subject} not found"}
    return log_session_manual(subj, req.section, req.date_bs, req.time_from, req.time_to)

# Routine endpoint
@app.get("/routine")
def get_routine():
    """Return the routine schedule."""
    return routine
