import csv
import hashlib
import io
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


DATA_FILE = Path(__file__).with_name("jobmate_data.json")
USER_DATA_DIR = Path(__file__).with_name("user_data")


def get_data_file(user_key: str | None = None) -> Path:
    if user_key:
        USER_DATA_DIR.mkdir(exist_ok=True)
        safe_name = hashlib.sha256(user_key.encode("utf-8")).hexdigest()[:24]
        return USER_DATA_DIR / f"{safe_name}.json"
    return DATA_FILE


def load_data(user_key: str | None = None) -> dict[str, list[dict[str, Any]]]:
    data_file = get_data_file(user_key)
    if data_file.exists():
        try:
            return json.loads(data_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"applications": [], "reminders": []}


def save_data(data: dict[str, list[dict[str, Any]]], user_key: str | None = None) -> None:
    data_file = get_data_file(user_key)
    data_file.write_text(json.dumps(data, indent=2), encoding="utf-8")


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def build_email_draft(application: dict[str, Any]) -> str:
    company = application["company"] or "your company"
    role = application["role"] or "the role"
    recruiter = application.get("recruiter_name") or "Hiring Team"
    status = application["status"]
    follow_up_angle = {
        "Applied": "I wanted to follow up on my application and reiterate my interest.",
        "Follow-Up": "I am checking in on the status of my application and next steps.",
        "Interview": "Thank you for coordinating the interview process. I am looking forward to the conversation.",
        "Offer": "Thank you for the offer and the time invested throughout the process.",
    }.get(status, "I wanted to reconnect regarding my candidacy.")
    skills = application.get("key_skills") or "my experience"

    return (
        f"Subject: Following up on {role} application\n\n"
        f"Hi {recruiter},\n\n"
        f"I hope you're doing well. {follow_up_angle} "
        f"I'm excited about the opportunity to contribute to {company}, especially given the role's focus on {skills}.\n\n"
        f"If there is anything else I can provide, I would be happy to share it. "
        f"Thank you for your time and consideration.\n\n"
        f"Best,\n"
        f"[Your Name]"
    )


def add_application(
    data: dict[str, list[dict[str, Any]]], application: dict[str, Any], user_key: str | None = None
) -> None:
    application["id"] = int(datetime.now().timestamp() * 1000)
    application["created_at"] = datetime.now().isoformat()
    application["email_draft"] = build_email_draft(application)
    data["applications"].append(application)
    save_data(data, user_key)


def add_reminder(
    data: dict[str, list[dict[str, Any]]], reminder: dict[str, Any], user_key: str | None = None
) -> None:
    reminder["id"] = int(datetime.now().timestamp() * 1000)
    data["reminders"].append(reminder)
    save_data(data, user_key)


def applications_to_csv(applications: list[dict[str, Any]]) -> str:
    buffer = io.StringIO()
    fieldnames = [
        "company",
        "role",
        "status",
        "application_date",
        "location",
        "job_link",
        "recruiter_name",
        "recruiter_email",
        "key_skills",
        "salary_range",
        "source",
        "notes",
        "job_description",
    ]
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    for app in applications:
        writer.writerow({field: app.get(field, "") for field in fieldnames})
    return buffer.getvalue()
