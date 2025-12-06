import json
from pathlib import Path
from nepali_datetime import date as nep_date
from datetime import timedelta as nep_timedelta

LOG_DIR = Path("logs")
SYLLABI_FILE = Path("syllabi_all.json")

def slug(text: str) -> str:
    return text.replace(" ", "_").lower()

def log_session_manual(subject, section, date_bs, time_from, time_to):
    unit, session = next_unlogged_session(subject, section)
    if not session:
        return {"error": "No unlogged sessions left"}
    log_session(subject, section, unit, session, time_from, time_to, date_bs=date_bs)
    return {"status": "success", "topic": session.get("title")}

def calculate_progress(subject):
    subject_slug = slug(subject["subject"])
    log_file = LOG_DIR / f"{subject_slug}_log.json"

    total_sessions = sum(len(unit.get("sessions", [])) for unit in subject.get("syllabus", {}).get("theory", []))
    total_sessions += sum(len(unit.get("sessions", [])) for unit in subject.get("syllabus", {}).get("practical", []))

    logged_sessions = 0
    if log_file.exists():
        with open(log_file, "r", encoding="utf-8") as f:
            logged_sessions = len(json.load(f))

    return {
        "subject": subject["subject"],
        "logged": logged_sessions,
        "total": total_sessions,
        "progress_percent": round((logged_sessions / total_sessions) * 100, 2) if total_sessions else 0
    }

def load_syllabi():
    with open(SYLLABI_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def show_logbook(subject_name):
    subject_slug = slug(subject_name)
    log_file = LOG_DIR / f"{subject_slug}_log.json"
    if not log_file.exists():
        return []
    with open(log_file, "r", encoding="utf-8") as f:
        return json.load(f)
        
def next_unlogged_session(subject, section):
    subject_slug = slug(subject["subject"])
    log_file = LOG_DIR / f"{subject_slug}_log.json"

    # Load existing log
    logged_titles = set()
    if log_file.exists():
        with open(log_file, "r", encoding="utf-8") as f:
            logged = json.load(f)
            for entry in logged:
                logged_titles.add(entry.get("Topic"))

    # Debug print
    print(f"🔍 Checking {subject['subject']} [{section}]")
    print(f"Already logged: {logged_titles}")

    # Look inside syllabus → section
    syllabus_section = subject.get("syllabus", {}).get(section, [])
    for unit in syllabus_section:
        for session in unit.get("sessions", []):
            if session.get("title") not in logged_titles:
                print(f"➡️ Next unlogged: {session.get('title')}")
                return unit, session

    print("⚠️ No unlogged sessions found.")
    return None, None

def log_session(subject, section, unit, session, time_from=None, time_to=None, date_bs=None, log_path=None):
    if log_path is None:
        log_path = LOG_DIR / f"{slug(subject['subject'])}_log.json"

    if date_bs is None:
        date_bs = str(nep_date.today())

    is_extra = subject.get("is_extra_paid", False) and (time_from == "16:00" and time_to == "16:50")

    entry = {
        "S.No": 1,
        "Date_BS": date_bs,
        "Topic": session.get("title", "Unknown"),
        "Time_from": time_from,
        "Time_to": time_to,
        "Credit_hours": session.get("hours", 1),
        "Remarks": "",
        "Unit": unit.get("unit", "Unknown"),
        "Section": section,
        "Extra_paid": is_extra
    }


    data = []
    if log_path.exists():
        with open(log_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        entry["S.No"] = len(data) + 1

    data.append(entry)
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Logged: {entry['Topic']} ({section.upper()}) on {date_bs}")

def backfill_logs(subject, start_date_bs, end_date_bs, routine, holidays=None):
    """
    Fill logs from start_date_bs to end_date_bs using routine schedule.
    Skips Saturdays and any holidays provided.
    Marks 16:00-16:50 classes as extra (separate log).
    """
    log_file = LOG_DIR / f"{slug(subject['subject'])}_log.json"
    extra_file = LOG_DIR / f"{slug(subject['subject'])}_extra_log.json"

    # Convert BS dates to nepali_datetime objects
    start_y, start_m, start_d = map(int, start_date_bs.split("-"))
    end_y, end_m, end_d = map(int, end_date_bs.split("-"))

    start_bs = nep_date(start_y, start_m, start_d)
    end_bs = nep_date(end_y, end_m, end_d)

    # Normalize holidays list
    holidays = set(holidays or [])

    current = start_bs
    while current <= end_bs:
        current_str = str(current)

        # Skip Saturdays
        if current.weekday() == 6:  # 0=Sunday, 6=Saturday
            current += nep_timedelta(days=1)
            continue

        # Skip custom holidays
        if current_str in holidays:
            print(f"⛔ Holiday skipped: {current_str}")
            current += nep_timedelta(days=1)
            continue

        # Check routine for this weekday
        weekday = current.strftime("%A").lower()
        if weekday not in routine:
            current += nep_timedelta(days=1)
            continue

        for cls in routine[weekday]:
            subject_name = cls["subject"]
            if subject_name != subject["subject"]:
                continue

            section = cls["section"].lower()
            time_from, time_to = cls["time"]

            # Get next unlogged session
            unit, session = next_unlogged_session(subject, section)
            if not session:
                continue

            # Log normally
            log_session(subject, section, unit, session, time_from, time_to, date_bs=current_str)

            # If extra class (16:00–16:50), also log into extra file
            if subject.get("is_extra_paid", False) and time_from == "16:00" and time_to == "16:50":
                log_session(subject, section, unit, session, time_from, time_to, date_bs=str(current), log_path=extra_file) 

        current += nep_timedelta(days=1)