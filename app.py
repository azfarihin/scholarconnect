"""ScholarConnect: companion site for new students arriving in Singapore.

Run locally with:  streamlit run app.py
"""
import streamlit as st

import auth
import content
import nav
import styles
import views

st.set_page_config(page_title=content.SITE_NAME, page_icon=":material/folder:", layout="centered")
styles.inject()
st.markdown(
    '<div class="hs-brand"><svg viewBox="0 0 32 32" aria-hidden="true"><path d="M3 9a3 3 0 0 1 3-3h6l3 3h11a3 3 0 0 1 3 3v12a3 3 0 0 1-3 3H6a3 3 0 0 1-3-3z" fill="#F7C548" stroke="#1E2B45" stroke-width="2"/><path d="M3 13h26" stroke="#1E2B45" stroke-width="2"/><circle cx="22" cy="20" r="2.2" fill="#C8423B"/></svg>'
    f'<span>{content.SITE_NAME}</span></div>',
    unsafe_allow_html=True,
)

# Who is signed in (also keeps them signed in with a cookie)
student = auth.current_user()
st.session_state.student = student

staff_page = st.Page(views.staff, title="Staff", icon=":material/lock:", url_path="staff")

if student is None:
    # Not signed in: only the sign-in page (and the staff page at /staff) are reachable.
    login_page = st.Page(views.login, title="Sign in", icon=":material/login:", default=True)
    st.navigation([login_page, staff_page], position="hidden").run()
else:
    nav.PAGES.update({
        "home": st.Page(views.home, title="Home", icon=":material/home:", default=True),
        "guide": st.Page(views.guide, title="Guide", icon=":material/folder:", url_path="guide"),
        "checklist": st.Page(views.checklist, title="Checklist", icon=":material/edit:", url_path="checklist"),
        "wellbeing": st.Page(views.wellbeing, title="Well-being", icon=":material/favorite:", url_path="wellbeing"),
        "feedback": st.Page(views.feedback, title="Feedback", icon=":material/chat:", url_path="feedback"),
        "thanks": st.Page(views.thanks, title="Thank-you wall", icon=":material/volunteer_activism:", url_path="thanks"),
        "profile": st.Page(views.profile, title="Profile", icon=":material/person:", url_path="profile"),
        "staff": staff_page,
    })
    st.navigation(list(nav.PAGES.values()), position="top").run()
