"""Where the app saves things.

If Google Sheets details are in .streamlit/secrets.toml (or Streamlit Cloud
Secrets), everything is saved to that Google Sheet, one tab per table.
Otherwise it falls back to CSV files in a local data/ folder. That is fine for
testing on your laptop, but on Streamlit Cloud those files are wiped whenever
the app restarts.
"""
import os
import threading

import pandas as pd
import streamlit as st

# New columns are always added at the end, so older saved tables still line up.
TABLES = {
    "students": ["email", "name", "preferred_name", "nationality", "school_level", "school", "hostel",
                 "scholarship_type", "status", "stage_override"],
    "progress": ["email", "ticks", "updated_at"],
    "feedback": ["submitted_at", "response_id", "form_id", "form_title", "question", "answer", "email"],
    "poll_votes": ["voted_at", "poll_id", "option", "session"],
    "notes": ["created_at", "to", "message", "from", "approved", "email"],
    "announcements": ["date", "title", "body", "link", "pinned"],
    "events": ["date", "label", "title", "link"],
    "stages": ["name", "start", "end"],
}

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
_lock = threading.Lock()


def secret(key, default=None):
    """Read a value from secrets without crashing when there is no secrets file."""
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default


def _has_sheets():
    """True only when real Google Sheets details are filled in (not the example placeholders)."""
    url = str(secret("sheet_url", "") or "")
    acct = secret("gcp_service_account", {}) or {}
    try:
        key = str(acct.get("private_key", ""))
    except Exception:
        return False
    return bool(url) and "YOUR_SHEET_ID" not in url and "BEGIN PRIVATE KEY" in key and "\n...\n" not in key


def backend():
    return "Google Sheets" if _has_sheets() else "Local CSV (testing only)"


@st.cache_resource(show_spinner=False)
def _book():
    import gspread
    gc = gspread.service_account_from_dict(dict(st.secrets["gcp_service_account"]))
    return gc.open_by_url(st.secrets["sheet_url"])


def _worksheet(name):
    import gspread
    book = _book()
    cols = TABLES[name]
    try:
        ws = book.worksheet(name)
        if ws.row_values(1) != cols:
            ws.update([cols], "A1")
    except gspread.WorksheetNotFound:
        ws = book.add_worksheet(title=name, rows=500, cols=len(cols))
        ws.append_row(cols)
    return ws


def _csv(name):
    return os.path.join(DATA_DIR, f"{name}.csv")


def _read_raw(name):
    cols = TABLES[name]
    if _has_sheets():
        rows = _worksheet(name).get_all_values()
        body = rows[1:] if rows else []
        width = len(cols)
        df = pd.DataFrame([(r + [""] * width)[:width] for r in body], columns=cols) if body else pd.DataFrame(columns=cols)
    else:
        path = _csv(name)
        df = pd.read_csv(path, dtype=str, keep_default_na=False) if os.path.exists(path) else pd.DataFrame(columns=cols)
    return df.reindex(columns=cols).fillna("").astype(str)


@st.cache_data(ttl=60, show_spinner=False)
def read(name):
    """Return a table as a DataFrame (all values as text). Cached for a minute."""
    return _read_raw(name)


def append(name, rows):
    """Add one row (dict) or several rows (list of dicts) to a table."""
    if isinstance(rows, dict):
        rows = [rows]
    cols = TABLES[name]
    values = [[str(r.get(c, "")) for c in cols] for r in rows]
    with _lock:
        if _has_sheets():
            _worksheet(name).append_rows(values, value_input_option="RAW")
        else:
            os.makedirs(DATA_DIR, exist_ok=True)
            df = pd.concat([_read_raw(name), pd.DataFrame(values, columns=cols)], ignore_index=True)
            df.to_csv(_csv(name), index=False)
    read.clear()


def replace(name, df):
    """Overwrite a whole table (used by the Staff page editors)."""
    cols = TABLES[name]
    df = df.reindex(columns=cols).fillna("").astype(str)
    with _lock:
        if _has_sheets():
            ws = _worksheet(name)
            ws.clear()
            ws.update([cols] + df.values.tolist())
        else:
            os.makedirs(DATA_DIR, exist_ok=True)
            df.to_csv(_csv(name), index=False)
    read.clear()


def upsert(name, key, row):
    """Update the row whose `key` column matches row[key], or add it if there is none."""
    cols = TABLES[name]
    values = [str(row.get(c, "")) for c in cols]
    with _lock:
        if _has_sheets():
            ws = _worksheet(name)
            keys = ws.col_values(cols.index(key) + 1)
            target = str(row[key])
            if target in keys[1:]:
                r = keys.index(target, 1) + 1
                ws.update([values], f"A{r}")
            else:
                ws.append_row(values, value_input_option="RAW")
        else:
            os.makedirs(DATA_DIR, exist_ok=True)
            df = _read_raw(name)
            mask = df[key] == str(row[key])
            if mask.any():
                df.loc[mask, cols] = values
            else:
                df = pd.concat([df, pd.DataFrame([values], columns=cols)], ignore_index=True)
            df.to_csv(_csv(name), index=False)
    read.clear()


def content(name, defaults):
    """Staff-editable content: the saved table, or the starting samples if nothing is saved yet."""
    try:
        df = read(name)
    except Exception:
        df = pd.DataFrame()
    if df.empty:
        return pd.DataFrame(defaults, columns=TABLES[name]).fillna("").astype(str), True
    return df, False
