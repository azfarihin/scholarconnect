"""The pages of the site. Each function draws one page."""
import datetime as dt
import html as _html
import uuid
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

import auth
import content as C
import nav
import storage

SG = ZoneInfo("Asia/Singapore")


# ---------------- helpers ----------------
def html(s):
    """Render HTML. Lines are stripped so Markdown never treats indented HTML as code."""
    st.markdown("\n".join(l.strip() for l in s.splitlines() if l.strip()), unsafe_allow_html=True)


def esc(s):
    return _html.escape(str(s or ""))


def today():
    return dt.datetime.now(SG).date()


def parse_date(s):
    try:
        return dt.date.fromisoformat(str(s).strip())
    except ValueError:
        return None


def short_date(d):
    return f"{d.day} {d.strftime('%b')}"


def label(title, sample=""):
    html(f'<div class="hs-label"><b>{esc(title)}</b>{f"<span class=hs-sample>{esc(sample)}</span>" if sample else ""}</div>')


def me():
    """The signed-in student's details (dict), or an empty dict."""
    return st.session_state.get("student") or {}


def my_email():
    return me().get("email", "")


def first_name():
    s = me()
    return (s.get("preferred_name") or s.get("name") or "").strip()


def init_state():
    ss = st.session_state
    ss.setdefault("sid", uuid.uuid4().hex[:12])
    ss.setdefault("votes", {})
    ss.setdefault("forms_done", {})
    ss.setdefault("note_sent", False)
    load_progress()


def now_iso():
    return dt.datetime.now(SG).isoformat(timespec="seconds")


# ---------------- saved checklist ticks ----------------
ALL_ITEMS = [it["id"] for lst in C.CHECKLISTS for it in lst["items"]]


def load_progress():
    ss = st.session_state
    if ss.get("progress_loaded") == my_email() or not my_email():
        return
    try:
        df = storage.read("progress")
        row = df[df["email"] == my_email()]
        ticks = set(row.iloc[0]["ticks"].split(",")) if not row.empty else set()
    except Exception:
        ticks = set()
    for i in ALL_ITEMS:
        ss[check_key(i)] = i in ticks
    ss.progress_loaded = my_email()


def save_progress():
    if not my_email():
        return
    ticks = ",".join(i for i in ALL_ITEMS if st.session_state.get(check_key(i)))
    try:
        storage.upsert("progress", "email", {"email": my_email(), "ticks": ticks, "updated_at": now_iso()})
    except Exception:
        st.toast("Your tick couldn't be saved just now. It will save next time you tick something.")


def stages():
    df, _ = storage.content("stages", C.DEFAULT_STAGES)
    out = []
    for r in df.to_dict("records"):
        s, e = parse_date(r["start"]), parse_date(r["end"])
        if r["name"] and s and e:
            out.append({"name": r["name"], "start": s, "end": e})
    return sorted(out, key=lambda x: x["start"]) or [{"name": "Pre-Arrival", "start": today(), "end": today()}]


def current_stage():
    st_list, t = stages(), today()
    held = (me().get("stage_override") or "").strip()
    names = [s["name"] for s in st_list]
    if held in names:
        return names.index(held), st_list
    for i, s in enumerate(st_list):
        if s["start"] <= t <= s["end"]:
            return i, st_list
    return (0 if t < st_list[0]["start"] else len(st_list) - 1), st_list


def events():
    df, sample = storage.content("events", C.DEFAULT_EVENTS)
    out = []
    for r in df.to_dict("records"):
        d = parse_date(r["date"])
        if d and r["title"]:
            out.append({**r, "d": d})
    return sorted(out, key=lambda e: e["d"]), sample


def link_html(link, text):
    url = C.route(link)
    if not url:
        return ""
    target = "_blank" if url.startswith("http") else "_self"
    return f'<a href="{esc(url)}" target="{target}">{esc(text)}</a>'


def check_key(item_id):
    return f"ck_{item_id}"


# ---------------- polls ----------------
def poll_counts(poll_id, options):
    try:
        df = storage.read("poll_votes")
    except Exception:
        df = pd.DataFrame(columns=storage.TABLES["poll_votes"])
    df = df[df["poll_id"] == poll_id]
    latest = df.drop_duplicates(subset="session", keep="last") if not df.empty else df
    return [int((latest["option"] == o).sum()) for o in options]


def my_vote(poll_id):
    if poll_id in st.session_state.votes:
        return st.session_state.votes[poll_id]
    try:
        df = storage.read("poll_votes")
        mine = df[(df["poll_id"] == poll_id) & (df["session"] == voter_id())]
        return mine.iloc[-1]["option"] if not mine.empty else None
    except Exception:
        return None


def voter_id():
    return my_email() or st.session_state.sid


def poll(p):
    with st.container(key=f"card_poll_{p['id']}"):
        label("Quick poll")
        html(f"<h3 style='margin:0;padding:0;font-size:1.1rem'>{esc(p['title'])}</h3><p style='color:var(--ink-soft);margin:.1rem 0 .6rem'>{esc(p['q'])}</p>")
        mine = my_vote(p["id"])
        if mine is None:
            cols = st.columns(2)
            for i, o in enumerate(p["opts"]):
                if cols[i % 2].button(o, key=f"vote_{p['id']}_{i}", width="stretch"):
                    try:
                        storage.append("poll_votes", {"voted_at": dt.datetime.now(SG).isoformat(timespec="seconds"),
                                                      "poll_id": p["id"], "option": o, "session": voter_id()})
                        st.session_state.votes[p["id"]] = o
                    except Exception:
                        st.error("Your vote couldn't be saved just now. Please try again in a minute.")
                    st.rerun()
            st.caption("Tap an option to vote and see the results.")
        else:
            counts = poll_counts(p["id"], p["opts"])
            total = sum(counts) or 1
            rows = "".join(
                f'<div class="bar {"mine" if o == mine else ""}"><i style="width:{round(c / total * 100)}%"></i>'
                f'<span>{esc(o)}{" · your pick" if o == mine else ""}</span><span class="pct">{round(c / total * 100)}%</span></div>'
                for o, c in zip(p["opts"], counts))
            html(f'<div class="bars">{rows}</div>')
            c1, c2 = st.columns([3, 2])
            c1.caption(f"{sum(counts)} vote{'s' if sum(counts) != 1 else ''} so far")
            if c2.button("Change my vote", key=f"revote_{p['id']}"):
                st.session_state.votes[p["id"]] = None
                st.rerun()


# ---------------- pages ----------------
def home():
    init_state()
    i, st_list = current_stage()
    steps = "".join(f'<div class="hs-step {"done" if k < i else "now" if k == i else ""}"><i></i>{esc(s["name"])}</div>'
                    for k, s in enumerate(st_list))
    html(f"""<p class="hs-hand">{C.GREETINGS}</p>
    <h1 class="hs-h1">Hi{(", " + esc(first_name())) if first_name() else " there"}! Welcome to your Singapore journey.</h1>
    <p class="hs-lede">You're in the <b>{esc(st_list[i]['name'])}</b> stage. Here's what to look out for.</p>
    <div class="hs-stepper">{steps}</div>""")

    # search
    st.write("")
    q = st.text_input("Search the guide", placeholder="Search: SIM card, luggage, stay out…", key="q", label_visibility="collapsed")
    if len(q.strip()) >= 2:
        results, terms = C.search(q)
        if not results:
            st.caption(f'Nothing found for "{q}". Try a shorter word, like "SIM" or "hostel".')
        for k, r in enumerate(results):
            with st.container(key=f"card_res_{k}"):
                if r.get("ch"):
                    qp = {"ch": r["ch"]}
                    if r["open"] is not None:
                        qp["open"] = str(r["open"])
                    st.page_link(nav.PAGES["guide"], label=r["head"], query_params=qp)
                else:
                    st.page_link(nav.PAGES[r["page"]], label=r["head"])
                html(f'<small style="color:var(--ink-soft)">{esc(r["where"])} · {C.snippet(r["text"], terms)}</small>')

    # next up
    evs, ev_sample = events()
    t = today()
    upcoming = [e for e in evs if e["d"] >= t]
    if upcoming:
        n = upcoming[0]
        days = (n["d"] - t).days
        when = "today!" if days == 0 else "tomorrow" if days == 1 else f"in {days} days"
        after = "".join(f'<div><time>{short_date(e["d"])}</time><span>{esc(e["title"])}</span></div>' for e in upcoming[1:3])
        more = link_html(n.get("link"), "Read more")
        with st.container(key="card_next"):
            label("Next up", "sample dates" if ev_sample else "")
            html(f"""<div class="next"><div class="cal"><div class="cal-m">{n['d'].strftime('%b').upper()}</div>
            <div class="cal-d">{n['d'].day}</div><div class="cal-w">{n['d'].strftime('%a')}</div></div>
            <div><h3>{esc(n['title'])}</h3><span class="count">{when}</span>
            <p>{esc(n.get('label') or '')}{' · ' if n.get('label') and more else ''}{more}</p></div></div>
            <div class="after">{after}</div>""")

    # to do
    fly = C.CHECKLISTS[0]
    left = [it for it in fly["items"] if not st.session_state.get(check_key(it["id"]))]
    done_n = len(fly["items"]) - len(left)
    with st.container(key="card_todo"):
        label("To do before you fly")
        if left:
            html('<ul class="todo">' + "".join(f'<li><span>✏️</span><span>{esc(it["t"])}<small>{esc(it["d"])}</small></span></li>' for it in left[:4]) + "</ul>")
        else:
            html('<p class="hs-hand">All done. You\'re ready to fly!</p>')
        html(f'<div class="prog"><i style="width:{round(done_n / len(fly["items"]) * 100)}%"></i></div><span class="prog-txt">{done_n} of {len(fly["items"])} done</span>')
        st.page_link(nav.PAGES["checklist"], label="Open my checklist", icon=":material/edit:")

    # announcements
    df, ann_sample = storage.content("announcements", C.DEFAULT_ANNOUNCEMENTS)
    anns = sorted(df.to_dict("records"), key=lambda a: a.get("pinned", "").lower() != "yes")
    if anns:
        label("Announcements", "sample" if ann_sample else "")
        cards = ""
        for a in anns:
            pinned = a.get("pinned", "").strip().lower() == "yes"
            go = link_html(a.get("link"), "Go to it")
            cards += (f'<article class="ann {"pinned" if pinned else ""}">{"<span class=stamp>MUST READ</span>" if pinned else ""}'
                      f'<time>{esc(a["date"])}</time><h3>{esc(a["title"])}</h3><p>{esc(a["body"])}</p>{go}</article>')
        html(f'<div class="anns">{cards}</div>')

    # timeline
    if evs:
        st.write("")
        label("Your journey at a glance", "sample dates" if ev_sample else "")
        nxt = upcoming[0] if upcoming else None
        items = "".join(f'<li class="{"done" if e["d"] < t else ""} {"is-next" if e is nxt else ""}"><time>{esc(e.get("label") or short_date(e["d"]))}</time><span>{esc(e["title"])}</span></li>' for e in evs)
        html(f'<div class="tl-wrap"><ol class="tl">{items}</ol></div>')

    poll(C.POLLS[0])

    st.write("")
    label("Life here", "photos coming soon")
    html('<div class="photos">' + "".join(f'<figure class="polaroid"><div class="ph">photo</div><figcaption>{esc(p)}</figcaption></figure>' for p in C.PHOTOS) + "</div>")

    st.write("")
    label("Emails you may have missed", "sample")
    html('<div class="edms">' + "".join(f'<a class="edm" href="{C.route(e["go"])}" target="_self"><b>{esc(e["title"])}</b><small>{esc(e["sub"])}</small></a>' for e in C.EDMS) + "</div>")

    st.write("")
    with st.container(key="teaser_home"):
        html('<div class="teaser"><b>Thank-you wall</b><p>Someone helped you settle in? Leave them a note.</p></div>')
        st.page_link(nav.PAGES["thanks"], label="Go to the thank-you wall", icon=":material/favorite:")


def guide():
    ids = C.CHAPTER_IDS
    short = {c["id"]: c["short"] for c in C.CHAPTERS}
    ss = st.session_state
    qp = st.query_params.get("ch")
    if qp in ids and ss.get("_ch_from_url") != qp:
        ss.ch_sel = qp
        ss._ch_from_url = qp
    if ss.get("ch_sel") not in ids:
        ss.ch_sel = ss.get("_ch_last", "welcome")
    ss._ch_last = ss.ch_sel

    html("""<h1 class="hs-h1">Information for New Students</h1>
    <p class="hs-lede" style="margin-bottom:1rem">Everything you need before you fly and after you land.</p>""")

    with st.container(key="chtabs"):
        st.pills("Guide sections", ids, format_func=lambda i: short[i], key="ch_sel", label_visibility="collapsed")
    sel = ss.ch_sel or ss._ch_last
    ss._ch_last = sel
    if st.query_params.get("ch") != sel:
        st.query_params["ch"] = sel
        ss._ch_from_url = sel
    ch = C.CHAPTER_BY_ID[sel]

    open_i = st.query_params.get("open")
    with st.container(key="sheet"):
        body = f"<h2>{esc(ch['title'])}</h2>" + (ch.get("intro") or "")
        if ch.get("sections"):
            secs = "".join(f'<section class="blk">{f"<h3>{s["h"]}</h3>" if s["h"] else ""}{s["html"]}</section>' for s in ch["sections"])
            body += f'<div class="{"cards" if ch.get("layout") == "cards" else ""}">{secs}</div>'
        body += ch.get("outro") or ""
        html(body)
        for k, f in enumerate(ch.get("faqs") or []):
            tag = f"**{f['tag']}** · " if f.get("tag") else ""
            with st.expander(f"{k + 1:02d} · {tag}{f['q']}", expanded=(open_i == str(k))):
                html(f["a"])

    k = ids.index(sel)
    c1, c2 = st.columns(2)

    def go(target):
        st.session_state.ch_sel = target
        st.query_params.pop("open", None)

    if k > 0:
        c1.button(f"← {short[ids[k - 1]]}", on_click=go, args=(ids[k - 1],), width="stretch")
    if k < len(ids) - 1:
        c2.button(f"{short[ids[k + 1]]} →", on_click=go, args=(ids[k + 1],), width="stretch")


def checklist():
    init_state()
    html("""<h1 class="hs-h1">My Checklist</h1>
    <p class="hs-lede" style="margin-bottom:1rem">Tick things off as you go. Your ticks are saved, so you can come back any time.</p>""")
    tabs = st.tabs([c["tab"] for c in C.CHECKLISTS])
    for tab, lst in zip(tabs, C.CHECKLISTS):
        with tab:
            n = sum(1 for it in lst["items"] if st.session_state.get(check_key(it["id"])))
            total = len(lst["items"])
            with st.container(key=f"book_{lst['id']}"):
                html(f'<div class="book-head"><p class="hs-hand">{esc(lst["hand"])}</p>'
                     f'<div class="prog"><i style="width:{round(n / total * 100)}%"></i></div><span class="prog-txt">{n} of {total} done</span></div>')
                for it in lst["items"]:
                    with st.container(key=f"ckrow_{it['id']}"):
                        st.checkbox(it["t"], key=check_key(it["id"]), on_change=save_progress)
                        more = link_html(it.get("go"), "More") if it.get("go") else ""
                        html(f'<p class="d">{esc(it["d"])} {more}</p>')

            def clear(items=lst["items"]):
                for it in items:
                    st.session_state[check_key(it["id"])] = False
                save_progress()

            st.button("Clear ticks on this list", key=f"clear_{lst['id']}", on_click=clear, type="tertiary")


def wellbeing():
    html("""<h1 class="hs-h1">Well-being</h1>
    <div class="calm"><b class="t">Your well-being matters!</b>
    <p>Looking after your personal well-being is important.</p>
    <p>By taking good care of your physical, social, emotional and mental well-being, you will be better able to manage stress and anxiety and achieve personal success.</p>
    <p>Scroll down for some ways you can take care of your well-being.</p></div>""")
    st.write("")
    label("Small things that help")
    html('<ul class="tips">' + "".join(f'<li><span class="h">♥</span><span>{esc(t)}</span></li>' for t in C.TIPS) + "</ul>")
    st.write("")
    label("Resources")
    for k, r in enumerate(C.RESOURCES):
        with st.container(key=f"card_res_wb_{k}"):
            links = "".join(f'<li><a href="{l[0]}" target="_blank">{esc(l[1])}</a></li>' for l in r["links"])
            html(f'<b style="font-family:var(--f-display)">{esc(r["h"])}</b><ul style="margin:.3rem 0 0">{links}</ul>')
    with st.container(key="card_talk"):
        label("Need to talk to someone now?")
        html("""<div class="help"><div><span>Samaritans of Singapore (SOS), 24 hours</span><b>1800 221 4444</b></div>
        <div><span>TOUCHline (Counselling), 9am - 6pm weekdays</span><b>1800 377 2252</b></div></div>
        <p style="margin:0;font-size:.92rem;color:var(--ink-soft)">You can also speak to your teachers, hostel staff or a school counsellor.</p>""")


def form_done(form_id):
    if form_id in st.session_state.forms_done:
        return st.session_state.forms_done[form_id]
    if not my_email():
        return None
    try:
        df = storage.read("feedback")
        mine = df[(df["form_id"] == form_id) & (df["email"] == my_email())]
        if mine.empty:
            return None
        d = parse_date(mine.iloc[-1]["submitted_at"][:10])
        return f"{d.day} {d.strftime('%b %Y')}" if d else "an earlier date"
    except Exception:
        return None


def feedback():
    init_state()
    html("""<h1 class="hs-h1">Feedback</h1>
    <p class="hs-lede" style="margin-bottom:1rem">Tell us how things are going. It helps us make settling in easier for everyone. Staff can see who sent each answer, so they can follow up if you need help.</p>""")
    label("Forms for you")
    t = today()
    for f in C.FORMS:
        closes = parse_date(C.FORM_CLOSES.get(f["id"], ""))
        if closes and t > closes:
            continue
        done = form_done(f["id"])
        with st.expander(f"**{f['title']}** · {f['when']}" + (" · ✓ Completed" if done else "")):
            if done:
                html(f'<div style="text-align:center"><span class="big-stamp">RECEIVED</span><p style="color:var(--ink-soft)">Thank you! You sent this form on {esc(done)}.</p></div>')
                continue
            with st.form(f"form_{f['id']}", clear_on_submit=True):
                answers = []
                for k, fl in enumerate(f["fields"]):
                    key = f"{f['id']}_{k}"
                    req = " *" if fl.get("req") else ""
                    if fl["type"] == "rating":
                        v = st.radio(fl["label"] + req, [1, 2, 3, 4, 5], index=None, horizontal=True, key=key,
                                     captions=None, help=f"1 = {fl['lo']}, 5 = {fl['hi']}")
                    elif fl["type"] == "choice":
                        v = st.radio(fl["label"] + req, fl["opts"], index=None, key=key)
                    elif fl["type"] == "short":
                        v = st.text_input(fl["label"] + req, key=key)
                    else:
                        v = st.text_area(fl["label"] + req, key=key)
                    answers.append((fl, v))
                sent = st.form_submit_button("Send")
            if sent:
                missing = [fl["label"] for fl, v in answers if fl.get("req") and (v is None or str(v).strip() == "")]
                if missing:
                    st.error(f"Please answer: {missing[0]}")
                else:
                    now = dt.datetime.now(SG).isoformat(timespec="seconds")
                    rid = uuid.uuid4().hex[:10]
                    rows = [{"submitted_at": now, "response_id": rid, "form_id": f["id"], "form_title": f["title"],
                             "question": fl["label"], "answer": "" if v is None else v, "email": my_email()} for fl, v in answers]
                    try:
                        storage.append("feedback", rows)
                        st.session_state.forms_done[f["id"]] = f"{t.day} {t.strftime('%b %Y')}"
                        st.rerun()
                    except Exception:
                        st.error("Your answers couldn't be sent just now. Please try again in a minute.")
    st.write("")
    for p in C.POLLS:
        poll(p)
    with st.container(key="teaser_fb"):
        html('<div class="teaser"><b>Thank-you wall</b><p>Leave a note for someone who helped you.</p></div>')
        st.page_link(nav.PAGES["thanks"], label="Go to the thank-you wall", icon=":material/favorite:")
    with st.container(key="card_help"):
        label("Need help?")
        html(f"""<p><b>Before you arrive:</b> reply to the official email you received about your arrival arrangements.</p>
        <p><b>After you arrive:</b> speak to your hostel staff or Teacher Mentor.</p>
        <p style="margin:0"><b>In an emergency:</b> see the {link_html('useful-info', 'emergency numbers')}.</p>""")


def thanks():
    init_state()
    html("""<h1 class="hs-h1">Thank-you wall</h1>
    <p class="hs-lede" style="margin-bottom:1rem">Say thanks to someone who helped you settle in: hostel staff, a Teacher Mentor, a senior or a friend.</p>""")
    with st.container(key="card_noteform"):
        if st.session_state.note_sent:
            st.success("Thank you! Your note will appear on the wall once a staff member has checked it.")
            if st.button("Write another note"):
                st.session_state.note_sent = False
                st.rerun()
        else:
            with st.form("note_form", clear_on_submit=True):
                to = st.text_input("To", placeholder="e.g. My roommate", max_chars=60)
                msg = st.text_area("Your note", placeholder="Thank you for…", max_chars=200)
                frm = st.text_input("From (optional)", placeholder="e.g. a new JC1 student", max_chars=40,
                                    help="Please don't write your full name.")
                ok = st.form_submit_button("Pin my note")
            if ok:
                if not to.strip() or not msg.strip():
                    st.error("Add who it is for and your note, then pin it.")
                else:
                    try:
                        storage.append("notes", {"created_at": dt.datetime.now(SG).isoformat(timespec="seconds"),
                                                 "to": to.strip(), "message": msg.strip(), "from": frm.strip(), "approved": "no",
                                                 "email": my_email()})
                        st.session_state.note_sent = True
                        st.rerun()
                    except Exception:
                        st.error("Your note couldn't be saved just now. Please try again in a minute.")
    try:
        df = storage.read("notes")
        live = df[df["approved"].str.lower() == "yes"].iloc[::-1].to_dict("records")
    except Exception:
        live = []
    notes = [{"to": n["to"], "msg": n["message"], "from": n["from"]} for n in live]
    show_samples = len(notes) < 4
    if show_samples:
        notes += C.SAMPLE_NOTES
    st.write("")
    label("Notes on the wall", "samples included" if show_samples else "")
    html('<div class="notes">' + "".join(
        f'<div class="note"><span class="to">To {esc(n["to"])},</span>{esc(n["msg"])}<span class="from">{"– " + esc(n["from"]) if n.get("from") else ""}</span></div>'
        for n in notes) + "</div>")


# ---------------- staff ----------------
def _stage_warnings(df):
    rows = []
    for r in df.to_dict("records"):
        s, e = parse_date(r["start"]), parse_date(r["end"])
        if not r["name"]:
            continue
        if not s or not e:
            rows.append(f"{r['name']}: dates must look like 2027-01-26.")
            continue
        if e < s:
            rows.append(f"{r['name']}: end date is before the start date.")
        rows.append((r["name"], s, e))
    msgs = [x for x in rows if isinstance(x, str)]
    spans = sorted([x for x in rows if not isinstance(x, str)], key=lambda x: x[1])
    for (n1, s1, e1), (n2, s2, e2) in zip(spans, spans[1:]):
        if s2 <= e1:
            msgs.append(f"{n1} and {n2} overlap.")
        elif (s2 - e1).days > 1:
            msgs.append(f"There's a gap between {n1} and {n2} ({(s2 - e1).days - 1} day(s)).")
    return msgs


def _editor(name, defaults, help_text, column_config=None):
    df, sample = storage.content(name, defaults)
    if sample:
        st.info("Showing the starting samples. Edit them and save to make them live.")
    st.caption(help_text)
    edited = st.data_editor(df, num_rows="dynamic", hide_index=True, key=f"ed_{name}", column_config=column_config,
                            width="stretch")
    return edited


STUDENT_COLS_HELP = ("email (required), name (required), preferred_name (what we call them, optional), nationality, "
                     "school_level, school, hostel, scholarship_type, status (active or inactive), "
                     "stage_override (leave blank to follow the dates)")


def _clean_students(df):
    """Tidy a student table and return (clean_df, list of problems)."""
    df = df.reindex(columns=storage.TABLES["students"]).fillna("").astype(str)
    df = df.apply(lambda c: c.str.strip())
    df = df[(df["email"] != "") | (df["name"] != "")]
    df["email"] = df["email"].str.lower()
    df["status"] = df["status"].str.lower().replace("", "active")
    problems = []
    bad = df[~df["email"].str.match(auth.EMAIL_RE)]
    if not bad.empty:
        problems.append(f"Check these emails: {', '.join(bad['email'].replace('', '(blank)').head(5))}")
    dup = df[df["email"].duplicated(keep=False) & (df["email"] != "")]
    if not dup.empty:
        problems.append(f"These emails appear more than once: {', '.join(sorted(set(dup['email']))[:5])}")
    if (df["name"] == "").any():
        problems.append("Every student needs a name.")
    names = [x["name"] for x in stages()]
    wrong = df[(df["stage_override"] != "") & (~df["stage_override"].isin(names))]
    if not wrong.empty:
        problems.append(f"stage_override must be blank or one of: {', '.join(names)}")
    return df.reset_index(drop=True), problems


def _students_tab():
    df = storage.read("students")
    active = df[df["status"].str.lower() != "inactive"]
    st.caption(f"{len(active)} active student(s), {len(df) - len(active)} inactive. "
               "Only active students on this list can sign in. Set status to inactive to remove someone's access.")

    with st.expander("Upload a CSV of students"):
        st.caption("Columns: " + STUDENT_COLS_HELP + ". Students already on the list (same email) are updated.")
        sample = pd.DataFrame([{"email": "student@example.com", "name": "Full Name", "preferred_name": "Name",
                                "nationality": "", "school_level": "JC1", "school": "", "hostel": "",
                                "scholarship_type": "", "status": "active", "stage_override": ""}])
        st.download_button("Download a blank template", sample.to_csv(index=False).encode("utf-8"),
                           file_name="students_template.csv", mime="text/csv")
        up = st.file_uploader("Choose CSV file", type=["csv"], key="stu_upload")
        if up is not None:
            try:
                new = pd.read_csv(up, dtype=str, keep_default_na=False)
                new.columns = [c.strip().lower().replace(" ", "_") for c in new.columns]
            except Exception:
                st.error("That file couldn't be read. Save it from Excel as 'CSV UTF-8' and try again.")
                new = None
            if new is not None:
                missing = [c for c in ("email", "name") if c not in new.columns]
                if missing:
                    st.error(f"The file needs these columns: {', '.join(missing)}")
                else:
                    merged = pd.concat([df, new.reindex(columns=storage.TABLES["students"])], ignore_index=True)
                    merged["email"] = merged["email"].str.strip().str.lower()
                    merged = merged.drop_duplicates(subset="email", keep="last")
                    clean, problems = _clean_students(merged)
                    for m in problems:
                        st.warning(m)
                    st.caption(f"Preview: {len(new)} row(s) in the file, {len(clean)} student(s) after merging.")
                    if st.button("Add these students", type="primary", disabled=bool(problems)):
                        storage.replace("students", clean)
                        st.success("Students saved.")
                        st.rerun()

    with st.expander("Change the stage for a group of students"):
        st.caption("Pick who to change, then the stage. Choose 'Follow the dates' to undo a hold.")
        filt = {}
        cols = st.columns(2)
        for k, col in enumerate(["nationality", "school", "school_level", "hostel", "scholarship_type"]):
            opts = sorted(x for x in df[col].unique() if x)
            if opts:
                filt[col] = cols[k % 2].multiselect(col.replace("_", " ").capitalize(), opts, key=f"bulk_{col}")
        group = df[df["status"].str.lower() != "inactive"]
        for col, vals in filt.items():
            if vals:
                group = group[group[col].isin(vals)]
        names = [x["name"] for x in stages()]
        target = st.selectbox("Set stage to", ["Follow the dates"] + names, key="bulk_stage")
        st.caption(f"This will change {len(group)} active student(s).")
        if st.button("Apply to this group", disabled=group.empty):
            df.loc[group.index, "stage_override"] = "" if target == "Follow the dates" else target
            storage.replace("students", df)
            st.success(f"Updated {len(group)} student(s).")
            st.rerun()

    st.caption("Edit directly in the table. Add a row at the bottom for a new student. Then save.")
    ed = st.data_editor(
        df, num_rows="dynamic", hide_index=True, key="ed_students", width="stretch",
        column_config={
            "email": st.column_config.TextColumn("email", required=True),
            "status": st.column_config.SelectboxColumn("status", options=["active", "inactive"]),
            "stage_override": st.column_config.SelectboxColumn("stage_override", options=[""] + [x["name"] for x in stages()]),
        })
    clean, problems = _clean_students(ed)
    for m in problems:
        st.warning(m)
    c1, c2 = st.columns(2)
    if c1.button("Save students", type="primary", disabled=bool(problems)):
        storage.replace("students", clean)
        st.success("Saved.")
    c2.download_button("Download list as CSV", df.to_csv(index=False).encode("utf-8"), file_name="students.csv", mime="text/csv")


def staff():
    html('<h1 class="hs-h1">Staff</h1>')
    if not auth.staff_configured():
        st.warning("Staff sign-in isn't set up yet. Add admin_password (or [staff_accounts]) to the app's secrets. See README.md.")
        return
    if not st.session_state.get("staff_ok"):
        with st.form("staff_login"):
            email = st.text_input("Staff email") if auth.staff_uses_email() else ""
            given = st.text_input("Password", type="password")
            if st.form_submit_button("Sign in"):
                if auth.staff_check(email, given):
                    st.session_state.staff_ok = True
                    st.rerun()
                else:
                    st.error("That email or password isn't right.")
        return

    b = storage.backend()
    (st.success if b == "Google Sheets" else st.warning)(
        f"Saving to: **{b}**" + ("" if b == "Google Sheets" else ". Data here is wiped when the app restarts on Streamlit Cloud."))
    if auth.test_mode():
        st.error("Test mode is ON: sign-in codes show on screen instead of being emailed. Turn it off before students use the site.")
    elif not auth.smtp_ready():
        st.error("Email sending isn't set up, so students can't get sign-in codes. Add the [smtp] settings to the secrets.")

    t_stu, t_fb, t_poll, t_notes, t_ann, t_ev, t_stage = st.tabs(
        ["Students", "Feedback", "Polls", "Thank-you notes", "Announcements", "Timeline", "Stage dates"])

    with t_stu:
        _students_tab()

    with t_fb:
        df = storage.read("feedback")
        if df.empty:
            st.caption("No feedback yet.")
        else:
            names = storage.read("students").set_index("email")["name"].to_dict()
            df = df.copy()
            df["student"] = df["email"].map(lambda e: names.get(e, e or "(not signed in)"))
            forms = sorted(df["form_title"].unique())
            pick = st.selectbox("Form", forms)
            sub = df[df["form_title"] == pick]
            wide = sub.pivot_table(index=["submitted_at", "response_id", "student"], columns="question", values="answer",
                                   aggfunc="first").reset_index()
            st.caption(f"{len(wide)} response(s)")
            st.dataframe(wide.drop(columns=["response_id"]), hide_index=True, width="stretch")
            st.download_button("Download as CSV", wide.to_csv(index=False).encode("utf-8"), file_name=f"{pick}.csv", mime="text/csv")

    with t_poll:
        for p in C.POLLS:
            counts = poll_counts(p["id"], p["opts"])
            st.markdown(f"**{p['title']}** · {sum(counts)} vote(s)")
            st.bar_chart(pd.DataFrame({"votes": counts}, index=p["opts"]), horizontal=True)

    with t_notes:
        df = storage.read("notes")
        if df.empty:
            st.caption("No notes yet.")
        else:
            st.caption("Tick 'Show on wall' for notes that are kind and safe to share, then save.")
            view = df.copy()
            view["approved"] = view["approved"].str.lower() == "yes"
            ed = st.data_editor(view, hide_index=True, key="ed_notes", width="stretch",
                                disabled=["created_at", "to", "message", "from", "email"],
                                column_config={"approved": st.column_config.CheckboxColumn("Show on wall")})
            if st.button("Save notes", type="primary"):
                ed["approved"] = ed["approved"].map(lambda x: "yes" if x else "no")
                storage.replace("notes", ed)
                st.success("Saved.")

    with t_ann:
        ed = _editor("announcements", C.DEFAULT_ANNOUNCEMENTS,
                     "Link: a guide section (e.g. phone-line, faq-leave) or a page (checklist, wellbeing, feedback, thanks). Pinned: yes or no.",
                     {"pinned": st.column_config.SelectboxColumn("pinned", options=["yes", "no"])})
        if st.button("Save announcements", type="primary"):
            storage.replace("announcements", ed)
            st.success("Saved. The Home page now shows these.")

    with t_ev:
        ed = _editor("events", C.DEFAULT_EVENTS,
                     "Date as YYYY-MM-DD (used for order and countdown). Label is optional text shown instead of the date, e.g. 'Mid Jan'.")
        if st.button("Save timeline", type="primary"):
            bad = [r["title"] for r in ed.to_dict("records") if r["title"] and not parse_date(r["date"])]
            if bad:
                st.error(f"Fix the date for: {bad[0]} (use YYYY-MM-DD).")
            else:
                storage.replace("events", ed)
                st.success("Saved.")

    with t_stage:
        ed = _editor("stages", C.DEFAULT_STAGES, "Dates as YYYY-MM-DD. The Home page works out the current stage from today's date.")
        for m in _stage_warnings(ed):
            st.warning(m)
        if st.button("Save stage dates", type="primary"):
            storage.replace("stages", ed)
            st.success("Saved.")

    if st.button("Sign out of staff"):
        st.session_state.staff_ok = False
        st.rerun()


# ---------------- sign in ----------------
def _code_box(purpose):
    """Shared 'enter your code' step. Returns the verified email or None."""
    p = st.session_state.get("otp") or {}
    shown = p.get("shown")
    if auth.test_mode():
        if shown:
            st.info(f"Test mode: your code is **{shown}**. (Students would get this by email.)")
        elif purpose == "signin":
            st.info("Test mode: no code was made, which means this email isn't on the student list or is inactive.")
    with st.form(f"code_form_{purpose}", clear_on_submit=True):
        code = st.text_input("6-digit code", max_chars=6, placeholder="123456", key=f"code_{purpose}")
        go = st.form_submit_button("Continue")
    if go:
        email, err = auth.verify(code)
        if email:
            return email
        st.error(err)
    return None


def login():
    html(f"""<p class="hs-hand">{C.GREETINGS}</p>
    <h1 class="hs-h1">Welcome! Let's get you signed in.</h1>""")
    ss = st.session_state
    step = ss.get("login_step", "email")
    with st.container(key="card_login"):
        if step == "email":
            html('<p style="margin:0 0 .5rem">Type the email address where you get our emails. We\'ll send you a 6-digit code.</p>')
            with st.form("email_form"):
                email = st.text_input("Email address", placeholder="you@example.com", key="login_email")
                go = st.form_submit_button("Send me a code")
            if go:
                ok, msg = auth.start(email)
                if ok:
                    ss.login_step = "code"
                    ss.login_to = auth.clean(email)
                    st.rerun()
                else:
                    st.error(msg)
        else:
            html(f'<p style="margin:0 0 .5rem">If <b>{esc(auth.mask(ss.get("login_to", "")))}</b> is on our list, a code is on its way. '
                 f'It works for {auth.CODE_MINUTES} minutes.</p>')
            email = _code_box("signin")
            if email:
                auth.sign_in(email)
                st.rerun()
            c1, c2 = st.columns(2)
            if c1.button("Send a new code", width="stretch"):
                ok, msg = auth.start(ss.get("login_to", ""))
                (st.success if ok else st.error)("New code sent." if ok else msg)
            if c2.button("Use a different email", width="stretch"):
                ss.login_step = "email"
                ss.pop("otp", None)
                st.rerun()
            st.caption("No email after a few minutes? Check your spam folder and the spelling of your email. "
                       "Still stuck? Reply to the official email you got about your arrival.")


# ---------------- profile ----------------
def profile():
    init_state()
    s = me()
    i, st_list = current_stage()
    html(f"""<h1 class="hs-h1">My profile</h1>
    <p class="hs-lede" style="margin-bottom:1rem">If anything here is wrong, reply to the official email you got about your arrival.</p>""")
    rows = [("Name", s.get("name")), ("Email", s.get("email")), ("Nationality", s.get("nationality")),
            ("Level", s.get("school_level")), ("School", s.get("school")), ("Hostel", s.get("hostel")),
            ("Stage", st_list[i]["name"])]
    with st.container(key="card_profile"):
        html('<div class="help">' + "".join(f'<div><span>{k}</span><b style="font-size:1rem">{esc(v) or "–"}</b></div>' for k, v in rows) + "</div>")

    with st.container(key="card_email"):
        label("Change my email")
        ss = st.session_state
        if ss.get("email_step") == "code":
            html(f'<p style="margin:0 0 .5rem">We sent a code to <b>{esc(ss.get("new_email", ""))}</b>. Type it here to confirm your new email.</p>')
            got = _code_box("change")
            if got and got == ss.get("new_email"):
                _change_email(got)
            if st.button("Cancel"):
                ss.email_step = None
                ss.pop("otp", None)
                st.rerun()
        else:
            st.caption("Got your school email? Change it here. We'll send a code to the new address to check it's yours.")
            with st.form("new_email_form"):
                new = st.text_input("New email address", key="new_email_input")
                go = st.form_submit_button("Send code to new email")
            if go:
                new = auth.clean(new)
                if new == my_email():
                    st.error("That's already your email.")
                elif new in set(storage.read("students")["email"].str.lower()):
                    st.error("That email is already used by another account. Please ask the staff team for help.")
                else:
                    ok, msg = auth.start(new, purpose="change")
                    if ok:
                        ss.email_step = "code"
                        ss.new_email = new
                        st.rerun()
                    else:
                        st.error(msg)

    st.write("")
    if st.button("Sign out", type="secondary"):
        auth.sign_out()
        st.rerun()


def _change_email(new):
    old = my_email()
    df = storage.read("students").copy()
    df.loc[df["email"].str.lower() == old, "email"] = new
    storage.replace("students", df)
    try:
        prog = storage.read("progress").copy()
        if (prog["email"] == old).any():
            prog.loc[prog["email"] == old, "email"] = new
            storage.replace("progress", prog)
    except Exception:
        pass
    st.session_state.email_step = None
    auth.sign_in(new)
    st.session_state.progress_loaded = new
    st.success("Your email has been changed.")
    st.rerun()
