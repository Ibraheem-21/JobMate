import csv
import io
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


DATA_FILE = Path(__file__).with_name("jobmate_data.json")


def load_data() -> dict[str, list[dict[str, Any]]]:
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"applications": [], "reminders": []}


def save_data(data: dict[str, list[dict[str, Any]]]) -> None:
    DATA_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


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


def add_application(data: dict[str, list[dict[str, Any]]], application: dict[str, Any]) -> None:
    application["id"] = int(datetime.now().timestamp() * 1000)
    application["created_at"] = datetime.now().isoformat()
    application["email_draft"] = build_email_draft(application)
    data["applications"].append(application)
    save_data(data)


def add_reminder(data: dict[str, list[dict[str, Any]]], reminder: dict[str, Any]) -> None:
    reminder["id"] = int(datetime.now().timestamp() * 1000)
    data["reminders"].append(reminder)
    save_data(data)


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
