# ScholarConnect

A companion site for new students arriving in Singapore, built in Streamlit.
Students sign in with a one-time code sent to their email. Staff manage everything from `/staff`.

## What's in the folder

| File | What it does |
|---|---|
| `app.py` | Starts the app, checks who is signed in, sets up the pages |
| `auth.py` | Email code sign-in, staying signed in, staff sign-in |
| `views.py` | The pages: Sign in, Home, Guide, Checklist, Well-being, Feedback, Thank-you wall, Profile, Staff |
| `content.py` + `content.json` | All the guide text, checklist items, polls and forms |
| `storage.py` | Saves everything to Google Sheets (or local CSV files when testing) |
| `styles.py` | The yellow-file look |
| `.streamlit/config.toml` | Theme colours |
| `.streamlit/secrets.toml` | Settings for testing on your laptop (test mode on). Never uploaded to GitHub. |
| `.streamlit/secrets.toml.example` | Template for the real settings when the site goes live |
| `data/students.csv` | Two sample students for testing |

## How students sign in

1. Staff add students on the Staff page → **Students** tab (one at a time, or upload a CSV).
2. The student types their email on the site and taps **Send me a code**.
3. If the email is on the list and active, a 6-digit code is emailed to them. It works once, for 10 minutes.
4. They type the code and they're in. They stay signed in on that phone for 30 days.

Safety rules built in:
- The reply looks the same whether or not the email is on the list, so nobody can check who is registered.
- 5 wrong tries and the code stops working. Max 5 codes per email per hour. 60 seconds between codes.
- Setting a student to **inactive** signs them out and blocks them straight away.
- Students can change their email on the **Profile** page. A code goes to the new address first to prove it's theirs.

## What saves where

| Thing | Saved to (Google Sheet tab) |
|---|---|
| Student list | `students` |
| Checklist ticks (per student) | `progress` |
| Feedback form answers (with the student's email) | `feedback` |
| Poll votes (one per student) | `poll_votes` |
| Thank-you notes (shown only after staff approve them) | `notes` |
| Announcements, timeline, stage dates | `announcements`, `events`, `stages` |

The app creates the tabs by itself the first time it saves something.

## Run it on your laptop (Windows)

1. Unzip the folder somewhere easy, e.g. your Desktop.
2. In VS Code: **File → Open Folder**, go into the `scholarconnect` folder and click **Select Folder**
   (the window only shows folders, so you'll just see `.streamlit` and `data`; that's fine).
3. **Terminal → New Terminal**, then paste this and press Enter:

```
python -m venv venv; Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned; venv\Scripts\activate; pip install -r requirements.txt; streamlit run app.py
```

Your browser opens the site at http://localhost:8501. To stop it, click the terminal and press **Ctrl+C**.
Next time, you only need: `venv\Scripts\activate; streamlit run app.py`

### Testing on your laptop

The included `.streamlit/secrets.toml` turns on **test mode**: the sign-in code appears on screen
instead of being emailed. Try it with a sample student:

- `minh.anh@example.com` or `siti.aisyah@example.com`

Staff page: go to http://localhost:8501/staff, password `staff123`.
To test with your own email, add yourself on the Staff page → Students tab.

Data is saved to CSV files in the `data/` folder (open them in Excel).

## Going live (Streamlit Cloud)

You'll need these in the app's **Settings → Secrets** (see `secrets.toml.example`):

1. **`[smtp]`**: the email account that sends the codes. Ask DxD which official sender to use.
2. **`cookie_secret`**: any long random string (keeps students signed in when the app restarts).
3. **`[staff_accounts]`**: one line per staff member, `"email" = "password"`.
4. **`sheet_url`** and **`[gcp_service_account]`**: the Google Sheet (steps below).
5. **`otp_test_mode = false`**, or leave that line out. Never turn test mode on for the live site.

Then push the folder to GitHub (`secrets.toml` and `data/` are blocked automatically) and create the app
on share.streamlit.io with `app.py` as the main file.

## Connect Google Sheets (one-time)

1. Create an empty Google Sheet. Copy its link.
2. Go to console.cloud.google.com and create a project.
3. In that project, turn on the **Google Sheets API** and the **Google Drive API** (APIs & Services → Library).
4. Go to APIs & Services → Credentials → **Create credentials → Service account**. Give it any name and finish.
5. Open the service account → **Keys** tab → **Add key → Create new key → JSON**. A file downloads.
6. Open your Google Sheet → **Share**. Paste the service account's email (it ends in `iam.gserviceaccount.com`) and give it **Editor** access.
7. Put `sheet_url` and the `[gcp_service_account]` values (from the JSON file) into the secrets.

The Sheet will hold students' names and emails. Check with DxD before real student data goes in.

## Staff page

Go to `/staff` and sign in. From there you can:
- **Students**: add, edit, deactivate; upload a CSV; hold a student at a stage; change the stage for a group (by nationality, school, level, hostel or scholarship type)
- **Feedback**: read and download responses, with the student's name
- **Polls**: see results
- **Thank-you notes**: approve notes before they appear on the wall
- **Announcements, Timeline, Stage dates**: edit what students see (with warnings for gaps or overlaps between stages)
