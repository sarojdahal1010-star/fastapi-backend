import json
from pathlib import Path
from colorama import Fore, Style, init
from logbook import backfill_logs, load_syllabi  # import your backfill + syllabi loader

init(autoreset=True)

LOG_DIR = Path("logs")
SYLLABI_FILE = Path("syllabi_all.json")

def backfill_all():
    syllabi = load_syllabi()
    start_date = input("📅 Enter start date (BS, e.g. 2082-07-12): ").strip()
    end_date = input("📅 Enter end date (BS, e.g. 2082-08-18): ").strip()
    holidays_input = input("📅 Enter holiday dates (comma separated BS dates, or leave empty): ").strip()
    holidays = [h.strip() for h in holidays_input.split(",")] if holidays_input else []

    from routine import routine
    for subject in syllabi:
        print(f"\n🔄 Backfilling {subject['subject']}...")
        backfill_logs(subject, start_date, end_date, routine, holidays)
    print("\n✅ Backfill completed for all subjects!")

def show_logbook(subject_name):
    # Unified logbook
    log_file = LOG_DIR / f"{subject_name.replace(' ', '_').lower()}_log.json"
    if not log_file.exists():
        print(Fore.YELLOW + f"⚠️ No logbook found for {subject_name}." + Style.RESET_ALL)
    else:
        with open(log_file, "r", encoding="utf-8") as f:
            entries = json.load(f)
            if not entries:
                print(Fore.YELLOW + "⚠️ No entries found." + Style.RESET_ALL)
            else:
                entries.sort(key=lambda e: (e.get("Date_BS", ""), e.get("Time_from", "")))
                total_hours = sum(e.get("Credit_hours", 0) for e in entries)

                print(Fore.MAGENTA + f"\n📖 Logbook for {subject_name}:" + Style.RESET_ALL)
                for i, e in enumerate(entries, start=1):
                    date_bs = e.get("Date_BS", "")
                    topic = e.get("Topic", "")
                    time_from = e.get("Time_from", "")
                    time_to = e.get("Time_to", "")
                    hours = e.get("Credit_hours", 0)
                    section = e.get("Section", "")

                    print(
                        f"{Fore.CYAN}{i}{Style.RESET_ALL}. "
                        f"{Fore.YELLOW}{date_bs}{Style.RESET_ALL} "
                        f"{time_from}-{time_to} "
                        f"{Fore.BLUE}{topic}{Style.RESET_ALL} "
                        f"({section.upper()}) {Fore.RED}{hours} hrs{Style.RESET_ALL}"
                    )

                print(Fore.MAGENTA + f"\n🧾 Total sessions: {len(entries)} | Total credit hours: {total_hours}" + Style.RESET_ALL)

    # Extra logbook
    extra_file = LOG_DIR / f"{subject_name.replace(' ', '_').lower()}_extra_log.json"
    if extra_file.exists():
        with open(extra_file, "r", encoding="utf-8") as f:
            extra_entries = json.load(f)
            if extra_entries:
                extra_entries.sort(key=lambda e: (e.get("Date_BS", ""), e.get("Time_from", "")))
                total_extra = sum(e.get("Credit_hours", 0) for e in extra_entries)

                print(Fore.MAGENTA + f"\n📖 Extra Logbook (16:00–16:50) for {subject_name}:" + Style.RESET_ALL)
                for i, e in enumerate(extra_entries, start=1):
                    date_bs = e.get("Date_BS", "")
                    topic = e.get("Topic", "")
                    time_from = e.get("Time_from", "")
                    time_to = e.get("Time_to", "")
                    hours = e.get("Credit_hours", 0)
                    section = e.get("Section", "")

                    print(
                        f"{Fore.CYAN}{i}{Style.RESET_ALL}. "
                        f"{Fore.YELLOW}{date_bs}{Style.RESET_ALL} "
                        f"{time_from}-{time_to} "
                        f"{Fore.BLUE}{topic}{Style.RESET_ALL} "
                        f"({section.upper()}) {Fore.RED}{hours} hrs{Style.RESET_ALL}"
                    )

                print(Fore.MAGENTA + f"\n🧾 Extra sessions: {len(extra_entries)} | Extra credit hours: {total_extra}" + Style.RESET_ALL)

def get_logged_hours(subject_name):
    total = 0
    log_file = LOG_DIR / f"{subject_name.replace(' ', '_').lower()}_log.json"
    if log_file.exists():
        with open(log_file, "r", encoding="utf-8") as f:
            entries = json.load(f)
            for e in entries:
                total += e.get("Credit_hours", 0)
    return total

def get_extra_hours(subject_name):
    total = 0
    extra_file = LOG_DIR / f"{subject_name.replace(' ', '_').lower()}_extra_log.json"
    if extra_file.exists():
        with open(extra_file, "r", encoding="utf-8") as f:
            entries = json.load(f)
            for e in entries:
                total += e.get("Credit_hours", 0)
    return total

def render_bar(completed, total, width=40, label="Progress"):
    filled = int((completed / total) * width) if total > 0 else 0
    empty = width - filled
    bar = Fore.GREEN + "█" * filled + Fore.YELLOW + "░" * empty + Style.RESET_ALL
    percent = round((completed / total) * 100) if total > 0 else 0
    return f"{label}: {bar} {Fore.CYAN}{completed} / {total} hrs ({percent}%)"

def run_backfill():
    syllabi = load_syllabi()
    for i, subject in enumerate(syllabi, start=1):
        print(f"{i}. {subject['subject']}")
    choice = int(input("👉 Enter subject number to backfill: ")) - 1
    subject = syllabi[choice]

    start_date = input("📅 Enter start date (BS, e.g. 2082-07-12): ").strip()
    end_date = input("📅 Enter end date (BS, e.g. 2082-08-18): ").strip()
    holidays_input = input("📅 Enter holiday dates (comma separated BS dates, or leave empty): ").strip()
    holidays = [h.strip() for h in holidays_input.split(",")] if holidays_input else []

    # You must define your routine dictionary somewhere globally
    from routine import routine  # assuming you keep routine in routine.py
    backfill_logs(subject, start_date, end_date, routine, holidays)

def main():
    print(Fore.MAGENTA + "\n📊 Dashboard Menu\n" + "-"*40 + Style.RESET_ALL)
    print("1. View Progress Dashboard")
    print("2. Backfill Logs Single Subject)")
    print("3. Backfill All Subjects")

    choice = input("\n👉 Enter choice: ").strip()
    if choice == "1":
        syllabi = load_syllabi()
        subjects = []
        for i, subject in enumerate(syllabi, start=1):
            name = subject["subject"]
            total = subject["total_credit_hours"]
            completed = get_logged_hours(name)

            print(Fore.RED + f"\n{i}. {name}" + Style.RESET_ALL)
            print(render_bar(completed, total, label="Main"))

            if subject.get("is_extra_paid", False):
                extra_completed = get_extra_hours(name)
                print(render_bar(extra_completed, total, label="Extra (16:00–16:50)"))

            subjects.append(name)

        choice = input("\n👉 Enter subject number to view logbook (or press Enter to exit): ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(subjects):
                show_logbook(subjects[idx])

    elif choice == "2":
        run_backfill()
    elif choice== "3":
        backfill_all()

if __name__ == "__main__":
    main()