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
│   ├── admin_view.py             ← Your control panel UI (toggle, question ID, Drive link).
│   └── student_view.py          ← The form students see and submit.
│
├── services/
│   ├── sheets_service.py         ← Reads/writes the Google Sheet (Open/Closed + Question ID).
│   ├── drive_service.py          ← Uploads files to Google Drive with auto-naming.
│   └── image_utils.py            ← Compresses photos before upload (fast on 4G).
│
├── requirements.txt              ← Python dependencies for Streamlit Cloud.
└── .streamlit/
    └── secrets.toml.example      ← Template for your credentials (never commit the real one).
```

**Rule of thumb:** if something isn't working, the file named after the broken thing is where to look.

---

## One-Time Setup (≈20 minutes)

### Step 1 — Google Cloud Service Account

1. Go to [console.cloud.google.com](https://console.cloud.google.com).
2. Create a project (or use an existing one).
3. Enable two APIs: **Google Sheets API** and **Google Drive API**.
4. Go to **IAM & Admin → Service Accounts → Create Service Account**.
5. Give it any name. Click through to finish.
6. Open the service account → **Keys → Add Key → JSON**. Download the file.

### Step 2 — Google Sheet (Control Plane)

1. Create a new Google Sheet.
2. In cell **A1** type `Status`, in **B1** type `Question_ID`.
3. In cell **A2** type `Closed`, in **B2** type `Q1`.
4. **Share** the sheet with the `client_email` from your JSON key file → give it **Editor** access.
5. Copy the sheet's URL.

### Step 3 — Google Drive Folder (Data Plane)

1. Create a folder in Google Drive for submissions (e.g., "Class Submissions").
2. **Share** the folder with the same `client_email` → **Editor** access.
3. Copy the folder ID from the URL: `drive.google.com/drive/folders/`**`THIS_PART`**

### Step 4 — Deploy on Streamlit Cloud

1. Push this folder to a GitHub repository.
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app** → connect your repo.
3. Set **Main file path** to `app.py`.
4. Open **Advanced settings → Secrets** and paste your credentials using the format in `.streamlit/secrets.toml.example`.
5. Deploy. Share the URL with students (they get the plain URL; you add `?role=admin`).

---

## Daily Use

### Opening a session

1. Go to `your-app-url?role=admin`
2. Enter the admin password (set in secrets.toml).
3. Type the Question ID (e.g., `Midterm_Q3`).
4. Click **OPEN submissions**.
5. Display the student URL (or a QR code) on the projector.

### Closing a session

1. Click **CLOSE submissions** once enough students have submitted.
2. Click the Drive folder link to see all named files immediately.

### Student filenames

Every file is automatically saved as:
```
{Question_ID}_{Student_Name}_{Student_ID}.jpg
```
Example: `Bonus_Q1_Ali_Hassan_202312345.jpg`

---

## Customisation Reference

| What you want to change | Where to change it |
|---|---|
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
| Upload fails with 403 | Service account not shared with Drive folder | Share the folder with `client_email` as Editor |
| Student sees "Closed" even after you opened | Sheet latency | Student clicks 🔄 Refresh |
| Photos arrive sideways | EXIF rotation data missing | `image_utils.py` handles this; if it still happens, update Pillow |
| App crashes on deploy | Missing secret key | Check all fields in secrets match the `.example` template |
