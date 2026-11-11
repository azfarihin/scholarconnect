"""Student sign-in with a one-time code sent by email, and staff sign-in.

How it works
- Staff add students on the Staff page (Students tab). Only emails on that list can sign in.
- A student types their email. If it's on the list and active, a 6-digit code is emailed to them.
- The code works once, for 10 minutes. Five wrong tries and they need a new code.
- After signing in, a cookie keeps them signed in on that device for 30 days.

Settings (in .streamlit/secrets.toml or Streamlit Cloud Secrets)
- [smtp] host / port / username / password / sender : the email account that sends the codes
- cookie_secret : a long random string; keeps sign-ins valid across app restarts
- otp_test_mode = true : FOR TESTING ONLY. Shows the code on screen instead of emailing it.
"""
import base64
import datetime as dt
import hashlib
import hmac
import json
import re
import secrets as pysecrets
import smtplib
import threading
import time
from email.message import EmailMessage

import streamlit as st
import streamlit.components.v1 as components

import storage

COOKIE = "sc_auth"
COOKIE_DAYS = 30
CODE_MINUTES = 10
MAX_TRIES = 5
RESEND_SECONDS = 60
MAX_CODES_PER_HOUR = 5
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------------- settings ----------------
@st.cache_resource(show_spinner=False)
def _fallback_secret():
    # Used only when cookie_secret isn't set: sign-ins then reset whenever the app restarts.
    return pysecrets.token_hex(32)


def _key():
    return str(storage.secret("cookie_secret") or _fallback_secret()).encode()


def test_mode():
    return bool(storage.secret("otp_test_mode", False))


def smtp_ready():
    cfg = storage.secret("smtp", {}) or {}
    try:
        return all(cfg.get(k) for k in ("host", "username", "password", "sender"))
    except Exception:
        return False


def clean(email):
    return (email or "").strip().lower()


def mask(email):
    name, _, domain = email.partition("@")
    return (name[:2] + "•" * max(1, len(name) - 2)) + "@" + domain


# ---------------- students ----------------
def find_student(email):
    """Return the student's row (dict) if the email is on the list and active."""
    email = clean(email)
    if not email:
        return None
    try:
        df = storage.read("students")
    except Exception:
        df = None
    rows = df[df["email"].str.strip().str.lower() == email] if df is not None else None
    if rows is None or rows.empty:
        return _demo_student(email)
    row = rows.iloc[0].to_dict()
    if row.get("status", "").strip().lower() in ("inactive", "withdrawn"):
        return None
    row["email"] = email
    return row


def _demo_student(email):
    """In test mode only: emails listed under [demo_students] in the secrets can always sign in.
    Handy for demos, because the online copy forgets its student list when it restarts."""
    if not test_mode():
        return None
    demo = storage.secret("demo_students", {}) or {}
    try:
        demo = {clean(k): str(v) for k, v in dict(demo).items()}
    except Exception:
        return None
    if email not in demo:
        return None
    return {"email": email, "name": demo[email], "preferred_name": demo[email], "status": "active",
            "nationality": "", "school_level": "", "school": "", "hostel": "", "scholarship_type": "", "stage_override": ""}


# ---------------- rate limits (shared by everyone using the app) ----------------
@st.cache_resource(show_spinner=False)
def _sent_log():
    return {"lock": threading.Lock(), "sent": {}}


def _allowed_to_send(email):
    log = _sent_log()
    now = time.time()
    with log["lock"]:
        recent = [t for t in log["sent"].get(email, []) if now - t < 3600]
        if len(recent) >= MAX_CODES_PER_HOUR:
            log["sent"][email] = recent
            return False
        recent.append(now)
        log["sent"][email] = recent
        return True


# ---------------- codes ----------------
def _hash(code, email):
    return hmac.new(_key(), f"{email}:{code}".encode(), hashlib.sha256).hexdigest()


def _send_email(to, code):
    cfg = storage.secret("smtp", {})
    from content import SITE_NAME
    msg = EmailMessage()
    msg["Subject"] = f"Your {SITE_NAME} code is {code}"
    msg["From"] = cfg["sender"]
    msg["To"] = to
    msg.set_content(
        f"Hi!\n\nYour {SITE_NAME} sign-in code is {code}\n\n"
        f"It works for {CODE_MINUTES} minutes. If you didn't ask for this code, you can ignore this email.\n")
    msg.add_alternative(f"""<div style="font-family:Arial,sans-serif;font-size:16px;color:#1E2B45">
<p>Hi!</p><p>Your {SITE_NAME} sign-in code is</p>
<p style="font-size:32px;font-weight:bold;letter-spacing:6px;background:#FCEBB0;display:inline-block;padding:8px 16px;border-radius:8px">{code}</p>
<p>It works for {CODE_MINUTES} minutes. If you didn't ask for this code, you can ignore this email.</p></div>""", subtype="html")
    port = int(cfg.get("port", 587))
    if port == 465:
        server = smtplib.SMTP_SSL(cfg["host"], port, timeout=20)
    else:
        server = smtplib.SMTP(cfg["host"], port, timeout=20)
        server.starttls()
    with server:
        server.login(cfg["username"], cfg["password"])
        server.send_message(msg)


def start(email, purpose="signin"):
    """Create a code for this email and send it. Returns (ok, message).

    For sign-in, the reply is the same whether or not the email is on the list,
    so nobody can use the form to find out who is registered.
    """
    email = clean(email)
    if not EMAIL_RE.match(email):
        return False, "That doesn't look like an email address. Check it and try again."
    if not test_mode() and not smtp_ready():
        return False, "Sign-in codes can't be sent yet because email sending isn't set up. Please tell the staff team."
    ss = st.session_state
    pending = ss.get("otp")
    if pending and pending["email"] == email and time.time() - pending["sent"] < RESEND_SECONDS:
        wait = int(RESEND_SECONDS - (time.time() - pending["sent"]))
        return False, f"Please wait {wait} seconds before asking for another code."

    send_to_real = purpose != "signin" or find_student(email) is not None
    code = f"{pysecrets.randbelow(10**6):06d}"
    ss.otp = {"email": email, "hash": _hash(code, email), "sent": time.time(),
              "expires": time.time() + CODE_MINUTES * 60, "tries": 0, "purpose": purpose,
              "real": send_to_real, "shown": code if (test_mode() and send_to_real) else None}
    if send_to_real:
        if not _allowed_to_send(email):
            ss.otp["real"] = False
            return False, "Too many codes were asked for this email. Please try again in an hour."
        if not test_mode():
            try:
                _send_email(email, code)
            except Exception:
                ss.pop("otp", None)
                return False, "We couldn't send the email just now. Please try again in a few minutes."
    return True, ""


def verify(code):
    """Check the code the person typed. Returns (email or None, message)."""
    ss = st.session_state
    p = ss.get("otp")
    if not p:
        return None, "Ask for a code first."
    code = re.sub(r"\D", "", code or "")
    if time.time() > p["expires"]:
        ss.pop("otp", None)
        return None, "This code has expired. Ask for a new one."
    if p["tries"] >= MAX_TRIES:
        ss.pop("otp", None)
        return None, "Too many wrong tries. Ask for a new code."
    p["tries"] += 1
    if p["real"] and len(code) == 6 and hmac.compare_digest(_hash(code, p["email"]), p["hash"]):
        ss.pop("otp", None)
        return p["email"], ""
    left = MAX_TRIES - p["tries"]
    return None, f"That code isn't right. {left} tr{'y' if left == 1 else 'ies'} left." if left else "That code isn't right. Ask for a new code."


# ---------------- staying signed in ----------------
def _b64(s):
    return base64.urlsafe_b64encode(s.encode()).decode().rstrip("=")


def _unb64(s):
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4)).decode()


def make_token(email):
    exp = int(time.time()) + COOKIE_DAYS * 86400
    body = f"{_b64(email)}.{exp}"
    sig = hmac.new(_key(), body.encode(), hashlib.sha256).hexdigest()[:32]
    return f"{body}.{sig}"


def read_token(token):
    try:
        e64, exp, sig = token.split(".")
        body = f"{e64}.{exp}"
        good = hmac.new(_key(), body.encode(), hashlib.sha256).hexdigest()[:32]
        if not hmac.compare_digest(sig, good) or int(exp) < time.time():
            return None
        return _unb64(e64)
    except Exception:
        return None


def _set_cookie(value, max_age):
    # Streamlit can't set cookies itself, so a tiny invisible script sets it on the page.
    components.html(
        "<script>(function(){var d=window.parent.document;var secure=window.parent.location.protocol==='https:'?'; Secure':'';"
        f"d.cookie={json.dumps(COOKIE)}+'='+{json.dumps(value)}+'; path=/; max-age={int(max_age)}; SameSite=Lax'+secure;}})();</script>",
        height=0,
    )


def sign_in(email):
    ss = st.session_state
    ss.user = clean(email)
    ss.signed_out = False
    ss.pending_cookie = make_token(ss.user)


def sign_out():
    ss = st.session_state
    for k in list(ss.keys()):
        if k.startswith("ck_") or k in ("user", "otp", "progress_loaded", "votes", "forms_done", "note_sent", "login_step"):
            del ss[k]
    ss.signed_out = True
    ss.clear_cookie = True


def current_user():
    """Who is signed in on this device, or None. Also writes/clears the cookie when needed."""
    ss = st.session_state
    if ss.get("clear_cookie"):
        _set_cookie("", 0)
        ss.clear_cookie = False
    if ss.get("pending_cookie"):
        _set_cookie(ss.pending_cookie, COOKIE_DAYS * 86400)
        ss.pending_cookie = None
    if not ss.get("user") and not ss.get("signed_out"):
        token = None
        try:
            token = st.context.cookies.get(COOKIE)
        except Exception:
            pass
        email = read_token(token) if token else None
        if email:
            ss.user = email
    if ss.get("user"):
        student = find_student(ss.user)
        if student is None:  # removed from the list or deactivated since signing in
            sign_out()
            return None
        return student
    return None


# ---------------- staff ----------------
def staff_check(email, password):
    """Staff sign in with email + password from [staff_accounts] in secrets,
    or with just admin_password if no staff accounts are set."""
    accounts = storage.secret("staff_accounts", {}) or {}
    try:
        accounts = {clean(k): str(v) for k, v in dict(accounts).items()}
    except Exception:
        accounts = {}
    if accounts:
        want = accounts.get(clean(email))
        return bool(want) and hmac.compare_digest(want, password or "")
    pw = storage.secret("admin_password")
    return bool(pw) and hmac.compare_digest(str(pw), password or "")


def staff_uses_email():
    accounts = storage.secret("staff_accounts", {}) or {}
    try:
        return bool(dict(accounts))
    except Exception:
        return False


def staff_configured():
    return staff_uses_email() or bool(storage.secret("admin_password"))
