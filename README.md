# ANVESHAN 2K26 - Gram Panchayat Complaint Portal

Single-server Django MVP integrating the prototype workflow in one local website.

## Windows setup and run (PowerShell)

Open PowerShell in the folder containing `manage.py`. Run:

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

Activation is not required, so PowerShell execution policy will not block startup. Run `createsuperuser` once per database; if an account already exists, skip it. Keep the server window open. Open `http://127.0.0.1:8000/` in the browser. `check` and `migrate` should be run after every project update.

## Included flows and pages

- Citizen complaint form supports anonymous or identified contact, village, ward, exact location/landmark, optional date first noticed, category, 15-1000 character details, and optional JPG/PNG/WEBP image up to 5 MB. Images are re-encoded to remove metadata.
- A public reference and one-time private tracking secret are generated. The success page shows the secret once; the database stores only its password hash. The reference alone shows basic status. Reference plus secret reveals complaint details, timestamped action history, and evidence, and allows feedback or a reinspection request.
- Reinspection/reopening is available within seven days of the latest resolution. The private secret is required to prove control of the complaint.
- The public grievance ledger is filterable by ward/category, shows anonymized case titles and status milestones, suggests existing open issues for the selected ward/category, and displays resolution photos after resolution. It omits contact details, complaint descriptions, exact landmarks, and citizen photos.
- Official dashboard provides search, filters, status, urgency, assignment, SLA target, escalation, resolution verification and private contact visibility. Staff must write a work summary and upload a photo before resolving; closing requires an earlier photo-backed resolved status.
- Public dashboard shows live database counts by status, category and ward, SLA overdue count, verified resolution count and average resolution time from actual resolved-action records. Each ward is shown separately.
- Category guide, process explanation, transparency/statistics page, citizen helpdesk page, and portal feedback/suggestion form are included.
- Professional public dashboard with clear submit/track actions, live-data overview cards, ward/category panels, and matching step-labeled submission/tracking pages. Shared responsive styling adds visible keyboard focus and mobile-friendly tables.
- Citizen sign-in and registration lead to a private My complaints dashboard. Complaints submitted while signed in are linked to that citizen account; account owners can edit their complaint details, and edits are recorded in action history. Staff retain review/status and archive actions; their separate complaint-details edit option is removed.
- Staff Review is hidden and blocked for Resolved and Closed complaints; a citizen reinspection request can reopen an eligible complaint and make it reviewable again.
- Complaint actions and feedback are available to staff in the official review/admin. The Django admin does not allow deleting or editing action history.

## Prototype fidelity and limitations

The teammate prototype is a separate Flask app. Compatible screens and workflows have been adapted to Django rather than running a second server. The prototype's SQLite database, sample tickets, and demo login accounts were not copied. The helpdesk page now shows clearly labeled fictional demo contact details; they are not real Panchayat contacts. Portal suggestions are stored in the local database for staff review; they are not emailed. Anonymous complaint details and public case titles can still indirectly identify a person, so avoid names or sensitive information in public titles/descriptions. This MVP is for local demo use, not public deployment.

The project uses Django 6.1.2, Python 3.13 and SQLite. Requirements include Pillow for image processing. The included migrations must be applied after extracting an update. Existing complaints created before account linking remain unassigned and do not appear in My complaints. Run `manage.py check` and `manage.py migrate` locally before demoing this update.

## Layout

```text
config/                 Django settings and URL routing
complaints/             Models, forms, views, admin and migrations
templates/complaints/    Citizen, official, ledger and information pages
manage.py
requirements.txt
PROJECT_STATUS.md
```

## Before public deployment

Change `SECRET_KEY`, set `DEBUG = False`, configure `ALLOWED_HOSTS`, review upload and access controls, use HTTPS, add rate limiting, and create least-privilege official accounts. Configure scheduled escalation and verified Panchayat contact details. Do not deploy the development settings as-is.
