# JobMate

JobMate is a Streamlit-based job application tracker for organizing applications, reminders, recruiter outreach, interview preparation, and exportable tracking data in one place.

## Live Demo

Public app:

https://ibraheem-21-jobmate-main-bh0rps.streamlit.app/

Important: this deployment should be treated as a public demo, not a private personal tracker. The current app stores data in a local JSON file on the app instance, so a public deployment can expose shared application data between visitors.

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

JobMate stores data locally in `jobmate_data.json` in the project folder. This keeps the app simple and easy to run without a database.

## Notes

- This is currently a local MVP, not a multi-user production app.
- The public Streamlit deployment should not be used for real private job-search data in its current form.
- Reminders are in-app organizational tools and do not yet send real emails or calendar notifications.
- The parser module is kept in the project for future expansion such as resume review, cover letter generation, or structured job-post analysis.

## Planned Next Steps

- Edit and delete actions for applications and reminders
- Resume review tools
- Cover letter generation
- Calendar and email integrations
- Better charts and deeper search analytics
