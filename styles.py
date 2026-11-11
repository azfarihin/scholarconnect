"""Look and feel: the yellow-file / exercise-book style, adapted to Streamlit."""
import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&family=Baloo+2:wght@600;700;800&family=Caveat:wght@600&display=swap');
:root{
  --bg:#EEF2F6; --paper:#FFFFFF; --ink:#1E2B45; --ink-soft:#56617A; --line:#DCE3EC; --rule:#C3D6EC;
  --margin:#EE8C8C; --file:#F7C548; --file-soft:#FCEBB0; --file-ink:#3B2E06; --tab-ink:#5A4507;
  --tick:#2F9E6E; --tick-wash:#E6F5EC; --stamp:#C8423B; --blue:#2F63C8; --shadow:rgba(30,43,69,.14);
  --tape:rgba(247,197,72,.6); --note1:#FFF0B3; --note2:#DCEBFC; --note3:#FCDDE3; --note4:#DDF3E5;
  --f-display:'Baloo 2','Trebuchet MS',system-ui,sans-serif;
  --f-body:'Atkinson Hyperlegible',system-ui,-apple-system,'Segoe UI',sans-serif;
  --f-hand:'Caveat','Segoe Print','Comic Sans MS',cursive;
}
html, body, .stApp, [data-testid="stMarkdownContainer"], .stApp p, .stApp li, .stApp label, .stApp input, .stApp textarea, .stApp button{font-family:var(--f-body)}
.stApp h1, .stApp h2, .stApp h3, .stApp h4{font-family:var(--f-display) !important;color:var(--ink);letter-spacing:0}
.block-container{max-width:40rem;padding-top:4.5rem;padding-bottom:4rem}
footer{visibility:hidden}
a{color:var(--blue)}
mark{background:var(--file-soft);color:inherit;border-radius:3px;padding:0 2px}

/* keep the Staff page out of the student menu (staff go to /staff directly) */
header a[href$="/staff"], [data-testid="stSidebar"] a[href$="/staff"], [data-testid="stSidebarNav"] li:has(a[href$="/staff"]){display:none !important}

/* brand */
.hs-brand{display:flex;align-items:center;gap:.5rem;font-family:var(--f-display);font-weight:800;font-size:1.2rem;color:var(--ink);margin-bottom:.25rem}
.hs-brand svg{width:1.9rem;height:1.9rem;flex:none}

/* plain html helpers */
.hs-hand{font-family:var(--f-hand);font-size:1.3rem;line-height:1.2;color:var(--ink-soft);margin:0 0 .25rem}
.hs-h1{font-family:var(--f-display);font-weight:800;font-size:clamp(1.9rem,7vw,2.4rem);line-height:1.12;margin:.2rem 0 .5rem;color:var(--ink)}
.hs-lede{color:var(--ink-soft);margin:0}
.hs-lede b{color:var(--ink)}
.hs-label{display:flex;align-items:baseline;justify-content:space-between;gap:.5rem;margin:0 0 .5rem}
.hs-label b{font-family:var(--f-display);font-size:1.2rem;color:var(--ink)}
.hs-sample{font-family:var(--f-hand);font-size:1.05rem;color:var(--stamp);white-space:nowrap}
.hs-stepper{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:.3rem;margin-top:.9rem}
.hs-step{display:flex;flex-direction:column;gap:.35rem;font-size:.7rem;line-height:1.2;color:var(--ink-soft);text-align:center}
.hs-step i{display:block;height:.5rem;border-radius:999px;background:var(--line)}
.hs-step.done i{background:var(--tick)}
.hs-step.now i{background:var(--file);box-shadow:0 0 0 2px var(--ink)}
.hs-step.now{color:var(--ink);font-weight:700}

/* cards: any container with a key starting "card" */
[class*="st-key-card"]{background:var(--paper) !important;border:1px solid var(--line) !important;border-radius:1rem !important;padding:1rem 1.1rem !important}

.next{display:grid;grid-template-columns:auto minmax(0,1fr);gap:1rem;align-items:center}
.cal{width:4.75rem;border-radius:.8rem;overflow:hidden;text-align:center;background:var(--paper);border:2px solid var(--ink);box-shadow:3px 3px 0 var(--ink)}
.cal-m{background:var(--stamp);color:#fff;font-family:var(--f-display);font-weight:700;font-size:.78rem;letter-spacing:.1em;padding:.1rem 0}
.cal-d{font-family:var(--f-display);font-weight:800;font-size:2rem;line-height:1.1;padding-top:.2rem;color:var(--ink)}
.cal-w{font-size:.7rem;color:var(--ink-soft);padding-bottom:.3rem}
.next h3{font-size:1.25rem;margin:0;padding:0}
.next p{margin:.15rem 0 0;color:var(--ink-soft);font-size:.92rem}
.count{font-family:var(--f-hand);font-size:1.3rem;color:var(--stamp);line-height:1}
.after{border-top:1px dashed var(--line);margin-top:1rem;padding-top:.75rem;display:flex;flex-direction:column;gap:.4rem;font-size:.92rem}
.after div{display:grid;grid-template-columns:4rem minmax(0,1fr);gap:.5rem}
.after time{color:var(--ink-soft)}

.todo{list-style:none;margin:0;padding:0}
.todo li{display:grid;grid-template-columns:1.6rem minmax(0,1fr);gap:.5rem;padding:.5rem 0;border-bottom:1px solid var(--rule);margin:0}
.todo li:last-child{border-bottom:0}
.todo small{display:block;color:var(--ink-soft);font-size:.82rem}
.prog{height:.6rem;background:var(--bg);border-radius:999px;overflow:hidden;margin:.6rem 0 .25rem}
.prog i{display:block;height:100%;background:var(--file);border-radius:999px}
.prog-txt{font-size:.85rem;font-weight:700;color:var(--ink-soft)}

.anns{display:flex;flex-direction:column;gap:.75rem}
.ann{position:relative;background:var(--paper);border:1px solid var(--line);border-radius:1rem;padding:.9rem 1rem}
.ann.pinned{background:var(--file-soft);border-color:var(--file)}
.ann h3{font-size:1.05rem;margin:.1rem 0 .3rem;padding:0 5.5rem 0 0}
.ann p{margin:0 0 .4rem;font-size:.95rem}
.ann time{font-size:.78rem;color:var(--ink-soft)}
.stamp{position:absolute;top:.75rem;right:.75rem;font-family:var(--f-display);font-weight:800;font-size:.7rem;letter-spacing:.12em;color:var(--stamp);border:2px solid var(--stamp);border-radius:.35rem;padding:.05rem .45rem;transform:rotate(-7deg);outline:1px solid var(--stamp);outline-offset:2px}

.tl-wrap{overflow-x:auto;padding:.25rem .1rem .75rem}
.tl{list-style:none;margin:0;padding:0;display:flex;gap:.75rem;width:max-content}
.tl li{width:9.5rem;background:var(--paper);border:1px solid var(--line);border-radius:.9rem;padding:.75rem .8rem;display:flex;flex-direction:column;gap:.25rem;margin:0}
.tl time{font-family:var(--f-display);font-weight:700;font-size:.95rem}
.tl span{font-size:.88rem;line-height:1.35}
.tl li.done{opacity:.55}
.tl li.is-next{border:2px solid var(--ink);box-shadow:3px 3px 0 var(--file)}

.photos{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.75rem;padding:.6rem .2rem .2rem}
.polaroid{position:relative;margin:0;background:var(--paper);padding:.4rem .4rem 0;border-radius:3px;box-shadow:0 2px 6px var(--shadow);transform:rotate(-2deg)}
.polaroid:nth-child(2){transform:rotate(1.5deg)}
.polaroid:nth-child(3){transform:rotate(-1deg)}
.polaroid::before{content:"";position:absolute;top:-.45rem;left:50%;width:2.6rem;height:.9rem;margin-left:-1.3rem;background:var(--tape);transform:rotate(-4deg)}
.ph{aspect-ratio:1;max-width:100%;display:grid;place-items:center;background:repeating-linear-gradient(135deg,var(--file-soft) 0 8px,var(--paper) 8px 16px);color:var(--tab-ink);font-size:.75rem}
.polaroid figcaption{font-family:var(--f-hand);font-size:1rem;line-height:1.1;text-align:center;padding:.3rem 0 .45rem}

.edms{display:flex;flex-direction:column;gap:.6rem}
.edm{display:block;background:var(--paper);border:1px solid var(--line);border-left:5px solid var(--note2);border-radius:.9rem;padding:.65rem .9rem;color:var(--ink) !important;text-decoration:none !important}
.edm b{font-family:var(--f-display);display:block;line-height:1.25}
.edm small{color:var(--ink-soft)}

/* guide */
.welcome{background:var(--file);color:var(--file-ink);border-radius:1rem;padding:1.1rem 1.2rem}
.welcome b{font-family:var(--f-display);font-size:1.35rem;display:block;margin-bottom:.3rem}
.welcome p{margin:0;color:var(--file-ink)}
.st-key-chtabs [data-testid="stButtonGroup"]{gap:.3rem}
.st-key-chtabs button{border-radius:.7rem .7rem 0 0 !important;background:var(--file-soft) !important;color:var(--tab-ink) !important;border:0 !important;font-family:var(--f-display) !important;font-weight:600}
.st-key-chtabs button[kind="pillsActive"], .st-key-chtabs button[data-testid="stBaseButton-pillsActive"]{background:var(--file) !important;color:var(--file-ink) !important;font-weight:800}
.st-key-sheet{position:relative !important;background:var(--paper) !important;border-top:6px solid var(--file) !important;border-radius:0 1rem 1rem 1rem !important;padding:1.2rem 1.1rem 1.4rem 2.2rem !important;box-shadow:0 1px 3px var(--shadow) !important}
.st-key-sheet::before{content:"";position:absolute;top:0;bottom:0;left:1.15rem;width:2px;background:var(--margin);opacity:.75}
.st-key-sheet h2{font-size:1.6rem;margin:0 0 .6rem;padding:0}
.blk{margin-top:1.3rem}
.blk h3{font-size:1.12rem;margin:0 0 .4rem;padding:0}
.callout{background:var(--file-soft);border-radius:.75rem;padding:.75rem .9rem}
.note-hand{font-family:var(--f-hand);font-size:1.25rem;color:var(--stamp);line-height:1.2;margin:.25rem 0 .75rem}
.cards .blk{border:1px solid var(--line);border-radius:.8rem;padding:.8rem .9rem;margin-top:.75rem}
.cards .blk h3{display:inline-block;font-size:.95rem;background:var(--file-soft);color:var(--tab-ink);padding:.05rem .65rem;border-radius:999px;margin-bottom:.5rem}
.chat{display:flex;flex-direction:column;gap:.5rem;margin:.25rem 0 .9rem}
.bub{max-width:88%;padding:.5rem .8rem;border-radius:1rem;font-size:.95rem;line-height:1.45;margin:0}
.bub small{display:block;font-family:var(--f-display);font-weight:700;font-size:.7rem;letter-spacing:.08em;text-transform:uppercase;color:var(--ink-soft)}
.bub.q{align-self:flex-start;background:var(--bg);border-bottom-left-radius:.25rem}
.bub.a{align-self:flex-end;background:var(--file-soft);border-bottom-right-radius:.25rem}
.docs{list-style:none;padding:0 !important;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.4rem}
.docs li{background:var(--bg);border-radius:.6rem;padding:.45rem .6rem;margin:0;font-size:.9rem;line-height:1.35}
.help{display:flex;flex-direction:column;gap:.45rem;margin-bottom:.5rem}
.help div{display:flex;justify-content:space-between;align-items:baseline;gap:.75rem;border-bottom:1px dashed var(--line);padding-bottom:.4rem;flex-wrap:wrap}
.help b{font-family:var(--f-display);font-size:1.15rem;white-space:nowrap}
.video{display:grid;grid-template-columns:2.6rem minmax(0,1fr);gap:.75rem;align-items:center;border:2px solid var(--ink);border-radius:.9rem;padding:.7rem .9rem;text-decoration:none !important;color:var(--ink) !important;box-shadow:3px 3px 0 var(--file);margin-top:.25rem}
.video .play{width:2.6rem;height:2.6rem;border-radius:50%;background:var(--stamp);color:#fff;display:grid;place-items:center}
.video .play svg{width:1.1rem;height:1.1rem}
.video b{font-family:var(--f-display);display:block}
.video small{color:var(--ink-soft)}
.copy code{font-weight:700;background:var(--bg);border-radius:.4rem;padding:.05rem .4rem;color:var(--ink)}
.st-key-sheet [data-testid="stExpander"] details{border:0;border-bottom:1px solid var(--rule);border-radius:0;background:transparent}
.st-key-sheet [data-testid="stExpander"] summary p{font-weight:700;line-height:1.4}

/* checklist: exercise-book rows */
[class*="st-key-book"]{position:relative !important;background:var(--paper) !important;border-top:6px solid var(--file) !important;border-radius:0 0 1rem 1rem !important;box-shadow:0 1px 3px var(--shadow) !important;padding:.6rem 1rem .6rem 0 !important;gap:0 !important}
[class*="st-key-book"]::before{content:"";position:absolute;top:0;bottom:0;left:2.9rem;width:2px;background:var(--margin);opacity:.75;z-index:1;pointer-events:none}
[class*="st-key-ckrow"]{border-bottom:1px solid var(--rule) !important;padding:.55rem 0 .55rem 3.6rem !important;gap:0 !important}
[class*="st-key-ckrow"]:last-child{border-bottom:0 !important}
[class*="st-key-ckrow"]:has(input:checked){background:var(--tick-wash) !important}
[class*="st-key-ckrow"]:has(input:checked) [data-testid="stCheckbox"] p{text-decoration:line-through;text-decoration-color:var(--tick);text-decoration-thickness:2px;color:var(--ink-soft)}
[class*="st-key-ckrow"] [data-testid="stCheckbox"] p{font-weight:700}
[class*="st-key-ckrow"] .d{font-size:.87rem;color:var(--ink-soft);line-height:1.45;margin:.1rem 0 0 1.75rem}
.book-head{padding:.4rem 0 .6rem 3.6rem;border-bottom:1px solid var(--rule)}

/* well-being */
.calm{background:var(--tick-wash);border-radius:1rem;padding:1.1rem 1.2rem}
.calm b.t{font-family:var(--f-display);font-size:1.45rem;display:block;margin-bottom:.4rem}
.calm p:last-child{margin:0}
.tips{list-style:none;margin:0;padding:0;background:var(--paper);border-top:6px solid var(--file);border-radius:0 0 1rem 1rem;position:relative;box-shadow:0 1px 3px var(--shadow)}
.tips::before{content:"";position:absolute;top:0;bottom:0;left:2.9rem;width:2px;background:var(--margin);opacity:.75}
.tips li{display:grid;grid-template-columns:2.9rem minmax(0,1fr);padding:.7rem 1rem .7rem 0;border-bottom:1px solid var(--rule);line-height:1.45;margin:0}
.tips li:last-child{border-bottom:0}
.tips .h{color:var(--stamp);text-align:center}

/* polls */
.bars{display:flex;flex-direction:column;gap:.45rem;margin:.25rem 0 .5rem}
.bar{position:relative;overflow:hidden;display:flex;justify-content:space-between;gap:.5rem;padding:.55rem .9rem;border:2px solid var(--line);border-radius:.8rem;background:var(--paper)}
.bar.mine{border-color:var(--ink)}
.bar i{position:absolute;inset:0 auto 0 0;background:var(--file-soft)}
.bar span{position:relative}
.bar .pct{font-weight:700}

/* feedback */
.big-stamp{display:inline-block;font-family:var(--f-display);font-weight:800;letter-spacing:.14em;color:var(--tick);border:3px solid var(--tick);border-radius:.5rem;padding:.1rem .8rem;transform:rotate(-6deg);outline:1px solid var(--tick);outline-offset:3px;margin:.5rem 0 .75rem}

/* thank-you wall */
.notes{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.9rem;padding:.3rem .2rem}
.note{padding:.8rem .85rem .9rem;border-radius:.25rem;box-shadow:0 2px 5px var(--shadow);transform:rotate(-1.5deg);font-size:.92rem;line-height:1.45;color:var(--ink);word-break:break-word}
.note:nth-child(even){transform:rotate(1.2deg)}
.note:nth-child(4n+1){background:var(--note1)}
.note:nth-child(4n+2){background:var(--note2)}
.note:nth-child(4n+3){background:var(--note3)}
.note:nth-child(4n+4){background:var(--note4)}
.note .to{display:block;font-family:var(--f-hand);font-size:1.2rem;line-height:1.1;margin-bottom:.3rem}
.note .from{display:block;font-family:var(--f-hand);font-size:1.05rem;text-align:right;margin-top:.4rem;color:var(--ink-soft)}
.teaser{background:var(--note3);border-radius:1rem;padding:1rem 1.1rem}
.teaser b{font-family:var(--f-display);font-size:1.15rem;display:block}
.teaser p{margin:.2rem 0 0;font-size:.92rem}

/* search box */
.st-key-q [data-baseweb="input"]{border:2px solid var(--ink) !important;border-radius:999px !important;box-shadow:3px 3px 0 var(--file);background:var(--paper) !important}
.st-key-q input{background:transparent !important}

/* buttons */
.stButton button, [data-testid="stFormSubmitButton"] button{border-radius:999px;font-family:var(--f-display);font-weight:700}
[data-testid="stFormSubmitButton"] button{background:var(--ink);color:#fff;border:0}
[data-testid="stPageLink"] a{border-radius:999px}
[data-testid="stPageLink"] p{font-family:var(--f-display);font-weight:700}
</style>
"""


def inject():
    st.markdown(CSS, unsafe_allow_html=True)
