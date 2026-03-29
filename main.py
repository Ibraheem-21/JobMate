from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import streamlit as st

from constants import APP_TITLE, DEFAULT_REMINDER_TYPES, DEFAULT_STATUSES, INTERVIEW_TIPS, SOURCE_OPTIONS
from storage import add_application, add_reminder, applications_to_csv, load_data, normalize_text


FORM_DEFAULTS = {
    "jobmate_role": "",
    "jobmate_company": "",
    "jobmate_location": "",
    "jobmate_job_link": "",
    "jobmate_recruiter_name": "",
    "jobmate_recruiter_email": "",
    "jobmate_salary_range": "",
    "jobmate_source": "LinkedIn",
    "jobmate_key_skills": "",
    "jobmate_status": "Applied",
    "jobmate_application_date": date.today(),
    "jobmate_notes": "",
    "jobmate_saved_description": "",
    "jobmate_weekly_goal": 5,
}
RESET_FLAG = "jobmate_reset_form"


def get_runtime_mode() -> str:
    return "hosted" if Path("/mount/src").exists() else "local"


def auth_is_configured() -> bool:
    try:
        auth_config = st.secrets.get("auth", {})
    except Exception:
        return False

    required_keys = ["redirect_uri", "cookie_secret", "client_id", "client_secret", "server_metadata_url"]
    return all(auth_config.get(key) for key in required_keys)


def get_user_identity() -> tuple[str | None, str, bool]:
    runtime_mode = get_runtime_mode()
    user_obj = getattr(st, "user", None)
    is_logged_in = bool(getattr(user_obj, "is_logged_in", False))

    if is_logged_in:
        email = getattr(user_obj, "email", None)
        user_id = getattr(user_obj, "sub", None)
        name = getattr(user_obj, "name", None) or email or "Authenticated user"
        return email or user_id, name, True

    if runtime_mode == "local":
        return None, "Local development mode", False

    return None, "Guest", False


def render_auth_gate() -> tuple[str | None, bool]:
    user_key, user_label, is_authenticated = get_user_identity()
    runtime_mode = get_runtime_mode()
    configured = auth_is_configured()

    if is_authenticated:
        st.caption(f"Signed in as {user_label}")
        if hasattr(st, "logout"):
            st.button("Log out", on_click=st.logout)
        return user_key, True

    if runtime_mode == "hosted":
        if not configured:
            st.error("Hosted authentication is not configured for this deployment yet.")
            st.code(
                "[auth]\n"
                'redirect_uri = "https://your-app.streamlit.app/oauth2callback"\n'
                'cookie_secret = "your-cookie-secret"\n'
                'client_id = "your-provider-client-id"\n'
                'client_secret = "your-provider-client-secret"\n'
                'server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"\n',
                language="toml",
            )
            st.caption("Configure these values in your Streamlit app secrets, then redeploy or restart the app.")
            st.stop()

        st.warning("Sign in to access your private JobMate workspace on the hosted app.")
        if hasattr(st, "login"):
            st.button("Sign in", on_click=st.login, type="primary")
        st.stop()

    st.caption("Running in local mode without authentication.")
    return user_key, False


def ensure_form_state() -> None:
    if st.session_state.get(RESET_FLAG):
        for key, value in FORM_DEFAULTS.items():
            st.session_state[key] = value
        st.session_state[RESET_FLAG] = False

    for key, value in FORM_DEFAULTS.items():
        st.session_state.setdefault(key, value)


def queue_form_reset() -> None:
    st.session_state[RESET_FLAG] = True


def calculate_streak(applications: list[dict[str, Any]]) -> int:
    if not applications:
        return 0

    dates = set()
    for app in applications:
        try:
            dates.add(datetime.fromisoformat(app["application_date"]).date())
        except ValueError:
            continue

    streak = 0
    current = date.today()
    while current in dates:
        streak += 1
        current -= timedelta(days=1)
    return streak


def get_application_age_days(application: dict[str, Any]) -> int:
    try:
        applied_on = datetime.fromisoformat(application["application_date"]).date()
    except ValueError:
        return 0
    return (date.today() - applied_on).days


def get_next_action(application: dict[str, Any]) -> str:
    age_days = get_application_age_days(application)
    status = application["status"]
    if status == "Saved":
        return "Submit the application or archive it if it is no longer relevant."
    if status == "Applied" and age_days >= 7:
        return "Good follow-up point. Send a short recruiter email or check the portal."
    if status == "Applied":
        return "Hold for now and track response timing."
    if status == "Follow-Up":
        return "Wait for a reply, then plan a second touchpoint only if appropriate."
    if status == "Interview":
        return "Review stories, company context, and prepare targeted questions."
    if status == "Offer":
        return "Review compensation, timeline, and questions before responding."
    return "Close the loop and capture what you learned from this application."


def get_priority_label(application: dict[str, Any]) -> str:
    age_days = get_application_age_days(application)
    status = application["status"]
    if status == "Interview":
        return "High"
    if status == "Applied" and age_days >= 10:
        return "High"
    if status == "Follow-Up" and age_days >= 5:
        return "Medium"
    return "Normal"


def get_follow_up_candidates(applications: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = []
    for app in applications:
        if app["status"] in {"Applied", "Follow-Up"} and get_application_age_days(app) >= 7:
            candidates.append(app)
    return sorted(candidates, key=get_application_age_days, reverse=True)


def render_metrics(applications: list[dict[str, Any]], reminders: list[dict[str, Any]]) -> None:
    total = len(applications)
    interviews = sum(app["status"] == "Interview" for app in applications)
    offers = sum(app["status"] == "Offer" for app in applications)
    streak = calculate_streak(applications)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Applications", total)
    col2.metric("Interviews", interviews)
    col3.metric("Offers", offers)
    col4.metric("Application streak", f"{streak} days")

    if applications:
        statuses = Counter(app["status"] for app in applications)
        top_source = Counter(app["source"] for app in applications if app["source"]).most_common(1)
        st.info(
            f"Most common status: {statuses.most_common(1)[0][0]} | "
            f"Upcoming reminders: {sum(r['due_date'] >= date.today().isoformat() for r in reminders)} | "
            f"Top source: {top_source[0][0] if top_source else 'N/A'}"
        )


def render_add_application(data: dict[str, list[dict[str, Any]]], user_key: str | None) -> None:
    st.subheader("Log a job application")
    ensure_form_state()
    st.caption("Manual entry only. Keep the saved description field if you want the posting stored with the application.")

    with st.form("application_form", clear_on_submit=True):
        role = st.text_input("Role", key="jobmate_role")
        company = st.text_input("Company", key="jobmate_company")
        location = st.text_input("Location", key="jobmate_location")
        job_link = st.text_input("Job link", key="jobmate_job_link")
        recruiter_name = st.text_input("Recruiter name", key="jobmate_recruiter_name")
        recruiter_email = st.text_input("Recruiter email", key="jobmate_recruiter_email")
        salary_range = st.text_input("Salary range", key="jobmate_salary_range")
        source = st.selectbox("Source", SOURCE_OPTIONS, key="jobmate_source")
        key_skills = st.text_input("Key skills", key="jobmate_key_skills")
        status = st.selectbox("Status", DEFAULT_STATUSES, key="jobmate_status")
        application_date = st.date_input("Application date", key="jobmate_application_date")
        notes = st.text_area(
            "Notes",
            placeholder="Why this role matters, next steps, contacts, preparation notes...",
            key="jobmate_notes",
        )
        saved_description = st.text_area(
            "Saved job description",
            height=180,
            placeholder="Optional if you used manual entry.",
            key="jobmate_saved_description",
        )
        submitted = st.form_submit_button("Save application")

        if submitted:
            application = {
                "role": normalize_text(role),
                "company": normalize_text(company),
                "location": normalize_text(location),
                "job_link": normalize_text(job_link),
                "recruiter_name": normalize_text(recruiter_name),
                "recruiter_email": normalize_text(recruiter_email),
                "salary_range": normalize_text(salary_range),
                "source": source,
                "key_skills": normalize_text(key_skills),
                "status": status,
                "application_date": application_date.isoformat(),
                "notes": notes.strip(),
                "job_description": saved_description.strip(),
            }
            if not application["role"] or not application["company"]:
                st.error("Role and company are required.")
            else:
                add_application(data, application, user_key)
                queue_form_reset()
                st.rerun()


def render_focus_mode(applications: list[dict[str, Any]]) -> None:
    st.subheader("Focus Mode")
    weekly_goal = st.slider("Weekly application goal", min_value=1, max_value=20, key="jobmate_weekly_goal")
    start_of_week = date.today() - timedelta(days=date.today().weekday())
    this_week_count = 0
    for app in applications:
        try:
            applied_on = datetime.fromisoformat(app["application_date"]).date()
        except ValueError:
            continue
        if applied_on >= start_of_week:
            this_week_count += 1

    progress = min(this_week_count / weekly_goal, 1.0)
    st.progress(progress, text=f"{this_week_count} of {weekly_goal} applications logged this week")

    follow_up_candidates = get_follow_up_candidates(applications)
    if follow_up_candidates:
        st.markdown("**Smart follow-up queue**")
        for app in follow_up_candidates[:5]:
            st.write(
                f"- {app['company']} | {app['role']} | {get_application_age_days(app)} days since apply | {get_next_action(app)}"
            )
    else:
        st.write("No overdue follow-ups right now.")


def render_reminders(
    data: dict[str, list[dict[str, Any]]], applications: list[dict[str, Any]], user_key: str | None
) -> None:
    st.subheader("Reminders")
    app_options = ["General reminder"] + [f"{app['company']} | {app['role']}" for app in applications]

    with st.form("reminder_form", clear_on_submit=True):
        linked_app = st.selectbox("Related application", app_options)
        reminder_type = st.selectbox("Reminder type", DEFAULT_REMINDER_TYPES)
        custom_note = st.text_input("Custom reminder note")
        due_date = st.date_input("Due date", value=date.today() + timedelta(days=3))
        reminder_channel = st.multiselect(
            "How do you want to be reminded?",
            ["In-app tracker", "Email yourself", "Calendar copy"],
            default=["In-app tracker"],
        )
        submitted = st.form_submit_button("Add reminder")

        if submitted:
            reminder = {
                "application_label": linked_app,
                "reminder_type": reminder_type,
                "custom_note": custom_note.strip(),
                "due_date": due_date.isoformat(),
                "channels": reminder_channel,
            }
            add_reminder(data, reminder, user_key)
            st.success("Reminder added.")
            st.rerun()

    if data["reminders"]:
        sorted_reminders = sorted(data["reminders"], key=lambda item: item["due_date"])
        for reminder in sorted_reminders:
            due = datetime.fromisoformat(reminder["due_date"]).date()
            label = reminder["custom_note"] or reminder["reminder_type"]
            urgency = "Due today" if due == date.today() else f"Due {due.isoformat()}"
            st.write(f"- {label} | {reminder['application_label']} | {urgency}")


def render_tracker(applications: list[dict[str, Any]]) -> None:
    st.subheader("Tracker")
    if not applications:
        st.write("No applications logged yet.")
        return

    search_term = st.text_input("Search by company, role, recruiter, or skills")
    status_filter = st.multiselect("Filter by status", DEFAULT_STATUSES, default=DEFAULT_STATUSES)
    filtered = [app for app in applications if app["status"] in status_filter]
    if search_term.strip():
        query = search_term.strip().lower()
        filtered = [
            app
            for app in filtered
            if query in " ".join(
                [
                    app.get("company", ""),
                    app.get("role", ""),
                    app.get("recruiter_name", ""),
                    app.get("recruiter_email", ""),
                    app.get("key_skills", ""),
                ]
            ).lower()
        ]
    filtered = sorted(filtered, key=lambda app: app["application_date"], reverse=True)

    follow_up_candidates = get_follow_up_candidates(filtered)
    if follow_up_candidates:
        st.markdown("**Need attention**")
        for app in follow_up_candidates[:3]:
            st.write(f"- {app['company']} | {app['role']} | {get_application_age_days(app)} days old")

    for app in filtered:
        title = f"{app['company']} | {app['role']} | {app['status']}"
        with st.expander(title):
            st.write(f"Applied on: {app['application_date']}")
            st.write(f"Age: {get_application_age_days(app)} days | Priority: {get_priority_label(app)}")
            st.write(f"Recommended next step: {get_next_action(app)}")
            if app["location"]:
                st.write(f"Location: {app['location']}")
            if app["job_link"]:
                st.write(f"Job link: {app['job_link']}")
            if app["salary_range"]:
                st.write(f"Salary: {app['salary_range']}")
            if app["key_skills"]:
                st.write(f"Key skills: {app['key_skills']}")
            if app["notes"]:
                st.write(f"Notes: {app['notes']}")
            if app["recruiter_email"] or app["recruiter_name"]:
                st.write(
                    f"Recruiter: {app.get('recruiter_name') or 'Unknown'} | "
                    f"{app.get('recruiter_email') or 'No email saved'}"
                )

            st.text_area(
                "Recruiter email draft",
                value=app["email_draft"],
                height=200,
                key=f"email_draft_{app['id']}",
            )

            if app["job_description"]:
                st.text_area(
                    "Saved job description",
                    value=app["job_description"],
                    height=220,
                    key=f"jd_{app['id']}",
                )

            if app["status"] == "Interview":
                st.markdown("**Interview tips**")
                for category, tips in INTERVIEW_TIPS.items():
                    st.write(f"{category.title()}:")
                    for tip in tips:
                        st.write(f"- {tip}")
                st.markdown("**Prep checklist**")
                st.write("- Re-read your resume and match it to the role.")
                st.write("- Prepare 3 impact stories with metrics.")
                st.write("- Write 5 questions for the interviewer.")
                st.write("- Review the company product, team, and recent news.")


def render_insights(applications: list[dict[str, Any]]) -> None:
    st.subheader("Insights")
    if not applications:
        st.write("Insights will appear after you log applications.")
        return

    statuses = Counter(app["status"] for app in applications)
    sources = Counter(app["source"] for app in applications if app["source"])
    companies = Counter(app["company"] for app in applications)
    stale_apps = sum(
        app["status"] in {"Applied", "Follow-Up"} and get_application_age_days(app) >= 7 for app in applications
    )
    avg_age = sum(get_application_age_days(app) for app in applications) / len(applications)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Status distribution**")
        for status, count in statuses.items():
            st.write(f"- {status}: {count}")
        st.markdown("**Company focus**")
        for company, count in companies.most_common(5):
            st.write(f"- {company}: {count}")

    with col2:
        st.markdown("**Source performance**")
        for source, count in sources.most_common():
            st.write(f"- {source}: {count}")

        interviews = sum(app["status"] == "Interview" for app in applications)
        offers = sum(app["status"] == "Offer" for app in applications)
        conversion = (interviews / len(applications)) * 100
        offer_rate = (offers / len(applications)) * 100
        st.markdown("**Conversion snapshot**")
        st.write(f"- Interview rate: {conversion:.1f}%")
        st.write(f"- Offer rate: {offer_rate:.1f}%")
        st.write(f"- Average application age: {avg_age:.1f} days")
        st.write(f"- Stale follow-ups: {stale_apps}")

    st.markdown("**Momentum coach**")
    if stale_apps >= 5:
        st.warning("You have a backlog of older applications. Spend one session on follow-ups before sending new apps.")
    elif interviews > 0:
        st.success("Interview traction is showing up. Shift some time from volume to prep quality.")
    else:
        st.info("No interview traction yet. Tighten targeting, refine resume bullets, and prioritize referrals where possible.")


def render_exports(applications: list[dict[str, Any]]) -> None:
    st.subheader("Export")
    if not applications:
        st.write("Add applications before exporting.")
        return

    csv_data = applications_to_csv(applications)
    st.download_button(
        "Download tracker CSV for Excel or Google Sheets",
        data=csv_data,
        file_name="jobmate_tracker.csv",
        mime="text/csv",
    )
    st.caption("Import the CSV into Excel or upload it to Google Sheets.")


def render_roadmap() -> None:
    st.subheader("Planned expansion")
    st.write("Next scalable additions for JobMate:")
    st.write("- Resume reviews against a saved job description")
    st.write("- Tailored cover letter generation from the posting")
    st.write("- Stronger AI parsing of job descriptions and outreach suggestions")
    st.write("- Calendar and email integrations for real notifications")


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    st.title(APP_TITLE)
    st.write(
        "Track applications, save job descriptions, draft recruiter outreach, manage reminders, "
        "prepare for interviews, and export your tracker for Excel or Google Sheets."
    )

    user_key, _ = render_auth_gate()
    data = load_data(user_key)
    applications = data["applications"]
    reminders = data["reminders"]

    render_metrics(applications, reminders)

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        ["Add Application", "Tracker", "Focus Mode", "Reminders", "Insights", "Export & Roadmap"]
    )

    with tab1:
        render_add_application(data, user_key)
    with tab2:
        render_tracker(applications)
    with tab3:
        render_focus_mode(applications)
    with tab4:
        render_reminders(data, applications, user_key)
    with tab5:
        render_insights(applications)
    with tab6:
        render_exports(applications)
        render_roadmap()


if __name__ == "__main__":
    main()
