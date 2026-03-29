# JobMate

JobMate is a Streamlit-based job application tracker for organizing applications, reminders, recruiter outreach, interview preparation, and exportable tracking data in one place.

## Live Demo

Public app:

https://ibraheem-21-jobmate-main-bh0rps.streamlit.app/

Important: the hosted app is now intended to be used with authenticated per-user storage. Local development still works without login, but the public deployment should rely on Streamlit authentication so each signed-in user gets a separate private data file.

## What It Does

- Log and manage job applications manually
- Track application status from saved to offer or rejection
- Save recruiter details, notes, salary info, links, and job descriptions
- Generate recruiter follow-up email drafts automatically
- Create reminders tied to a specific application or general job-search tasks
- Surface interview tips and a prep checklist when an application reaches the interview stage
- Show focus and momentum tools like follow-up queues, weekly goals, streaks, and conversion snapshots
- Export your tracker as CSV for Excel or Google Sheets

## Current Feature Highlights

### Tracker

- Search by company, role, recruiter, or skills
- Filter applications by status
- View application age, priority, and recommended next action
- Surface older applications that likely need attention

### Focus Mode

- Set a weekly application goal
- Track weekly progress visually
- Review a smart follow-up queue for overdue applications

### Reminders

- Create reminders for applications or general tasks
- Track due dates and reminder intent

### Insights

- Application streak
- Interview rate and offer rate
- Source breakdown
- Company focus snapshot
- Average application age
- Stale follow-up count
- Momentum coaching guidance

## Project Structure

```text
JobMate/
|-- main.py           # Streamlit UI and app flow
|-- storage.py        # Persistence, export, and email draft generation
|-- constants.py      # Shared labels, status values, and tips
|-- parser.py         # Reserved parser module for future structured extraction work
|-- requirements.txt  # Python dependencies
`-- jobmate_data.json # Local application and reminder data
```

## Requirements

- Python 3.10+
- `pip`

## Installation

From the project directory:

```powershell
python -m pip install -r requirements.txt
```

## Run The App

```powershell
python -m streamlit run main.py
```

Streamlit will usually open the app automatically in your browser. If it does not, open the local URL shown in the terminal, typically:

```text
http://localhost:8501
```

## How To Use

### Add an application

1. Open the `Add Application` tab.
2. Fill in role, company, status, date, and any extra details you want to keep.
3. Save the application.

### Track and review

1. Open the `Tracker` tab.
2. Search or filter your applications.
3. Expand a record to review notes, recruiter info, saved job description, email draft, and next-step guidance.

### Stay organized

1. Open `Focus Mode` to monitor weekly progress.
2. Review the follow-up queue for applications that may need attention.
3. Add reminders in the `Reminders` tab for deadlines, follow-ups, or interview prep.

### Export your data

1. Open `Export & Roadmap`.
2. Download the tracker CSV.
3. Open it in Excel or import it into Google Sheets.

## Data Storage

JobMate now supports two storage modes:

- Local development: data is stored in `jobmate_data.json`
- Hosted authenticated mode: data is stored in a per-user file under `user_data/`, keyed from the signed-in user's identity

This keeps local setup simple while making the hosted app much safer for public sharing.

## Hosted Privacy Model

For the public Streamlit deployment, JobMate is designed to use Streamlit's login system and separate each user's data by authenticated identity.

- Signed-in users get isolated storage
- Users should not see each other's job tracker data
- Local development can still run without authentication

If you deploy this yourself, configure Streamlit authentication before treating it as a private app.

## Streamlit Authentication Setup

JobMate is prepared for the Streamlit auth flow using `st.login()`, `st.user`, and `st.logout()`.

For a hosted deployment, configure authentication in Streamlit using an OIDC provider and the app's Streamlit secrets. Once configured:

1. Users sign in through Streamlit.
2. The app reads the authenticated identity from `st.user`.
3. JobMate stores each user's tracker data separately.

Official Streamlit auth docs:

https://docs.streamlit.io/develop/tutorials/authentication

## Notes

- This is currently a local MVP, not a multi-user production app.
- The hosted app is much safer when Streamlit authentication is configured, but it is still a lightweight MVP rather than a full production platform.
- Reminders are in-app organizational tools and do not yet send real emails or calendar notifications.
- The parser module is kept in the project for future expansion such as resume review, cover letter generation, or structured job-post analysis.

## Planned Next Steps

- Edit and delete actions for applications and reminders
- Resume review tools
- Cover letter generation
- Calendar and email integrations
- Better charts and deeper search analytics
