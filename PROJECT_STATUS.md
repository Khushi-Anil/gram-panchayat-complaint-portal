# Project Status - ANVESHAN 2K26

## Current milestone

Citizen account ownership and self-service complaint editing for the local demo.

## Implemented in the workspace

- Citizen complaint submission with anonymous/identified modes; separate private contact records.
- Complaint location fields (village, ward, landmark), optional noticed date, expanded category options, description validation and image upload.
- One-time tracking secret delivered on receipt; only a hash is stored. Reference-only tracking gives basic status; secret-protected view shows details and timestamped history.
- Citizen feedback and reinspection/reopen within seven days after resolution.
- Public grievance ledger with ward/category filters, public status milestones, duplicate suggestions and photo proof after resolution.
- Official assignment, priority/SLA, expanded status workflow, non-deletable action history, mandatory resolution work note/photo, and private contacts.
- Public status/category/ward metrics and average resolution time based on stored resolution actions.
- Category guide, how-it-works, helpdesk information and portal feedback/suggestion pages.
- UI improvements: staff sign-in appears in the public dashboard's top navigation; citizen dashboard and complaint-edit pages are included.
- Migration `0007_full_prototype_workflow.py` adds complaint location, noticed date, tracking-secret hash, categories, and feedback models.
- Citizen login and registration lead to My complaints. Submissions made while signed in link to the account, and the account owner can edit complaint details; edits are written to action history. Staff retain review/status and archive actions, but their separate complaint-details edit option is removed.
- Migration `0009_complaint_submitted_by.py` adds an optional account link. Existing complaints remain unlinked and cannot be attributed automatically.
- Staff cannot reopen the Review screen for Resolved or Closed complaints; eligible citizen reinspection can reopen them.

## Pending user-side steps

- Replace files in Desktop project's nested project folder from the refreshed ZIP, preserving `.venv` and `db.sqlite3`.
- Run `manage.py check` and `manage.py migrate` locally; migration 0009 is pending user-side application.
- Verify citizen login redirect, My complaints, owner-only edit, and staff review/status workflow in the browser.

## Prototype items deliberately not copied as real

- Sample complaint IDs and simulated JavaScript tracking records.
- Prototype demo staff accounts and credentials.
- Placeholder Panchayat address and phone number.
- Prototype SQLite database contents.

## Known limitations

- Current workspace Python does not have Django installed, so Django checks and migration application could not be run here. Python syntax compilation succeeded; browser verification is pending.
- Local Django development media serving works only with `DEBUG=True`; public deployment requires a proper media storage setup.
- Public descriptions and titles can indirectly identify citizens; remind submitters to avoid personal details. This is not a guarantee of absolute anonymity.
- No email/SMS delivery or external feedback forwarding is configured.

## Latest verification

- Python syntax compilation succeeded for the updated Python files.
- Django system checks and migration 0009 still need to be run in the user's local `.venv`; browser verification is pending.

## Next three actions

1. Deliver the refreshed ZIP containing migration 0009 and citizen ownership pages.
2. User extracts over the nested Desktop project, preserving `.venv` and `db.sqlite3`, then runs `manage.py check` and `manage.py migrate`.
3. Verify the citizen-owned complaint flow and staff workflow locally; address any runtime errors.
