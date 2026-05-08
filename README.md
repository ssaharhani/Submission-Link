# 📝 Classroom Submission App

A lightweight tool for collecting student handwritten solutions via photo upload.
Students scan a QR code → fill in name & ID → upload a photo.
You control open/close from a simple password-protected panel.

---

## Project Structure

```
submission_app/
│
├── app.py                        ← Entry point. Controls routing (admin vs student).
│
├── components/
│   ├── admin_view.py             ← Your control panel UI (toggle, question ID, storage link).
│   └── student_view.py          ← The form students see and submit.
│
├── services/
│   ├── sheets_service.py         ← Reads/writes the Google Sheet (Open/Closed + Question ID).
│   ├── drive_service.py          ← Uploads files to Supabase Storage with auto-naming.
│   └── image_utils.py            ← Compresses photos before upload (fast on 4G).
│
├── requirements.txt              ← Python dependencies for Streamlit Cloud.
└── .streamlit/
    └── secrets.toml.example      ← Template for your credentials (never commit the real one).
```

**Rule of thumb:** if something isn't working, the file named after the broken thing is where to look.

---

## One-Time Setup (≈15 minutes)

### Step 1 — Google Cloud Service Account (for Sheets only)

1. Go to [console.cloud.google.com](https://console.cloud.google.com).
2. Create a project (or use an existing one).
3. Enable the **Google Sheets API**.
4. Go to **IAM & Admin → Service Accounts → Create Service Account**.
5. Give it any name. Click through to finish.
6. Open the service account → **Keys → Add Key → JSON**. Download the file.

### Step 2 — Google Sheet (Control Plane)

1. Create a new Google Sheet.
2. In cell **A1** type `Status`, in **B1** type `Question_ID`, in **C1** type `Opened_At`.
3. In cell **A2** type `Closed`, in **B2** type `Q1`, leave **C2** empty.
4. **Share** the sheet with the `client_email` from your JSON key file → give it **Editor** access.
5. Copy the sheet's full URL.

### Step 3 — Supabase Storage (File Storage)

1. Go to [supabase.com](https://supabase.com) → Sign Up Free.
2. Create a new project → give it any name.
3. Go to **Storage** → **New bucket** → name it `submissions` → make it **private**.
4. Go to **Settings → API** → copy two values:
   - **Project URL** (looks like `https://xxxx.supabase.co`)
   - **service_role** key (the long secret key, not the anon key)

### Step 4 — Deploy on Streamlit Cloud

1. Push this folder to a GitHub repository.
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app** → connect your repo.
3. Set **Main file path** to `app.py`.
4. Open **Advanced settings → Secrets** and paste your credentials using the format in `.streamlit/secrets.toml.example`.
5. Deploy. Share the plain URL with students. You access the admin panel by adding `?role=admin` to the URL.

---

## Secrets Template

```toml
[google_credentials]
type = "service_account"
project_id = "your-project-id"
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@your-project.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"

[settings]
sheet_url = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
supabase_url = "https://xxxxxxxxxxxx.supabase.co"
supabase_key = "your-service-role-key"
supabase_bucket = "submissions"
admin_password = "YourPasswordHere"
```

---

## Daily Use

### Opening a session

1. Go to `your-app-url?role=admin`
2. Enter the admin password in the sidebar.
3. Type the Question ID (e.g., `Midterm_Q3`).
4. Click **OPEN submissions** — the session auto-closes after 15 minutes.
5. Display the student URL (or a QR code) on the projector.

### Closing a session

1. Click **CLOSE submissions** when done.
2. Click the Supabase Storage link in the admin panel to see all uploaded files.

### Student filenames

Every file is automatically saved as:
```
{Question_ID}_{Student_Name}_{Student_ID}.jpg
```
Example: `Midterm_Q3_Ali_Hassan_202312345.jpg`

For multiple photos: `Midterm_Q3_Ali_Hassan_202312345_1.jpg`, `_2.jpg`, etc.

---

## Customisation Reference

| What you want to change | Where to change it |
|---|---|
| Session auto-close duration | `services/sheets_service.py` → `AUTO_CLOSE_MINUTES` |
| Admin session timeout | `app.py` → `ADMIN_SESSION_MINUTES` |
| Max photo resolution | `services/image_utils.py` → `MAX_DIMENSION` |
| JPEG quality (file size vs clarity) | `services/image_utils.py` → `JPEG_QUALITY` |
| Admin password | `secrets.toml` → `settings.admin_password` |
| Page title / icon | `app.py` → `st.set_page_config(...)` |
| Student form fields | `components/student_view.py` |
| Admin panel layout | `components/admin_view.py` |

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| "Could not connect to Google Sheets" | Service account not shared with sheet | Share the sheet with `client_email` as Editor |
| Upload fails | Wrong Supabase key or bucket name | Make sure you used the `service_role` key, not the `anon` key. Check bucket name matches exactly (case-sensitive) |
| Student sees "Closed" after you opened | Sheet cache (5s delay) | Student clicks 🔄 Refresh |
| Student can't resubmit | Duplicate prevention by Student ID | Intended behaviour. Clear the Submissions tab in the Google Sheet to reset |
| Photos arrive sideways | EXIF rotation | `image_utils.py` handles this; if it still happens, update Pillow |
| App crashes on deploy | Missing secret key | Check all fields in secrets match the template above |
