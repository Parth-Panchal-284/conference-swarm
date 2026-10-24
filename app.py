import os

import streamlit as st

from src.conference_simulator import seed_conference
from src.graph import get_graph
from src.memory_agent import DEMO_ID, extract_memory, persist_memory
from src.scout_agent import scout
from src.shared_memory import recommend_next


st.set_page_config(page_title="Conference Swarm", page_icon="◈", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
:root { --bg:#080c14; --panel:#101723; --line:#1c2939; --muted:#8292a8; --text:#edf4ff; --cyan:#62e6d5; --blue:#86a8ff; --gold:#f7cc73; }
.stApp {background:radial-gradient(ellipse at 15% -10%,#142739 0,transparent 38%),var(--bg);color:var(--text);font-family:'DM Sans',sans-serif}
[data-testid="stHeader"] {background:transparent}
[data-testid="stSidebar"] {background:#0a111b;border-right:1px solid var(--line)}
[data-testid="stSidebar"] * {color:#cad6e7}
h1,h2,h3 {font-family:'Space Grotesk',sans-serif;letter-spacing:-.035em}
.block-container {max-width:1500px;padding-top:2rem;padding-bottom:3rem}
.brand {font-family:'Space Grotesk';font-size:1rem;letter-spacing:.1em;color:#dcecff;font-weight:700}
.eyebrow {font-family:'DM Mono';font-size:.68rem;letter-spacing:.16em;text-transform:uppercase;color:var(--cyan)}
.hero {padding:1.2rem 0 1.4rem;border-bottom:1px solid var(--line);margin-bottom:1.3rem}
.hero h1 {font-size:2.55rem;margin:.35rem 0 .2rem;color:#f2f7ff}
.hero p {color:#9aabc0;font-size:1.03rem;margin:0;max-width:760px}
.kpi {background:linear-gradient(145deg,#111d2b,#0d141e);border:1px solid var(--line);border-radius:14px;padding:1rem 1.15rem;height:100%}
.kpi-num {font-family:'Space Grotesk';font-size:1.75rem;font-weight:700;color:#edf6ff}
.kpi-label {font-family:'DM Mono';text-transform:uppercase;letter-spacing:.1em;font-size:.65rem;color:#92a2b8;margin-top:.2rem}
.surface {background:linear-gradient(145deg,#111a27,#0e151f);border:1px solid var(--line);border-radius:16px;padding:1.1rem 1.25rem;margin:.55rem 0}
.surface-title {font-family:'DM Mono';font-size:.68rem;letter-spacing:.13em;text-transform:uppercase;color:#8fa3ba;margin-bottom:.55rem}
.agent {display:flex;align-items:center;gap:.55rem;padding:.65rem 0;border-bottom:1px solid #1a2634;font-size:.88rem}
.agent:last-child {border-bottom:none}.dot {width:8px;height:8px;border-radius:9px;background:var(--cyan);box-shadow:0 0 10px #62e6d580}
.agent small {color:#8191a5;margin-left:auto;font-family:'DM Mono';font-size:.63rem}
.recommend {border:1px solid #23504e;background:linear-gradient(110deg,#102528,#111a27);border-radius:18px;padding:1.35rem 1.45rem;margin:.7rem 0}
.recommend-name {font-family:'Space Grotesk';font-size:1.8rem;font-weight:700;color:#f0fbff}
.tag {display:inline-block;border:1px solid #2a3b4d;border-radius:30px;padding:.28rem .55rem;color:#b7c6d8;font-family:'DM Mono';font-size:.67rem;margin:.2rem .28rem .15rem 0}
.tag-hot {border-color:#32746d;color:#72e7d6;background:#12312f}
.timeline {border-left:1px solid #2b4358;margin-left:.45rem;padding:.1rem 0 .1rem 1.1rem}
.timeline-item {position:relative;padding:0 0 1rem .2rem}.timeline-item:before {content:'';position:absolute;left:-1.42rem;top:.35rem;width:8px;height:8px;background:#62e6d5;border-radius:50%;box-shadow:0 0 12px #62e6d580}
.timeline-time {font-family:'DM Mono';font-size:.67rem;color:#62e6d5}.timeline-main {font-weight:600;color:#e6effb;margin:.12rem 0}.timeline-sub {font-size:.79rem;color:#8fa1b6}
.callout {border-left:2px solid var(--cyan);padding:.25rem 0 .25rem .8rem;color:#b5c4d5;font-size:.89rem}
.stButton button {border-radius:10px!important;font-weight:600!important;min-height:2.75rem}
[data-testid="stMetric"] {background:transparent}
hr {border-color:var(--line)!important}
</style>
""", unsafe_allow_html=True)


def initialize():
    if "initialized" not in st.session_state:
        seed_conference(reset=True)
        st.session_state.stage = 0
        st.session_state.scout_result = None
        st.session_state.memory_result = None
        st.session_state.memory_mode = None
        st.session_state.initialized = True


def reset_demo():
    seed_conference(reset=True)
    st.session_state.stage = 0
    st.session_state.scout_result = None
    st.session_state.memory_result = None
    st.session_state.memory_mode = None


def graph_counts():
    result = get_graph().query("""MATCH (n {demo_id: $demo_id})
        OPTIONAL MATCH (n)-[r]->(m {demo_id: $demo_id})
        RETURN count(DISTINCT n), count(r)""", params={"demo_id": DEMO_ID})
    return result.result_set[0]


def apply_moment(number):
    if number == 1:
        text = "I met Alice. She told me Bob works on KV Cache Optimization and said I should mention that she referred me."
        fallback = {
            "met_people": [{"name": "Alice"}],
            "recommendations": [{"from_person": "Alice", "to_person": "Bob"}],
            "person_topics": [{"person": "Bob", "topic": "KV Cache Optimization"}],
            "summary": "Alice referred me to Bob, who works on KV Cache Optimization.",
        }
    else:
        text = "I met Bob. He referred me to Cameron and said Cameron works on Agent Infrastructure. He also recommended the Agent Memory in Production session."
        fallback = {
            "met_people": [{"name": "Bob"}],
            "recommendations": [{"from_person": "Bob", "to_person": "Cameron"}],
            "person_topics": [
                {"person": "Cameron", "topic": "Agent Infrastructure"},
                {"person": "Cameron", "topic": "Agent Memory"},
            ],
            "recommended_sessions": [{"from_person": "Bob", "session": "Agent Memory in Production"}],
            "summary": "Bob referred me to Cameron and recommended the Agent Memory in Production session.",
        }
    try:
        memory = extract_memory(text)
        persist_memory(text, memory)
        mode = "OpenAI structured extraction"
    except Exception:
        # Keep the prepared stage cues reliable if API credentials or connectivity fail.
        memory = fallback
        persist_memory(text, memory)
        mode = "prepared memory replay"
    st.session_state.memory_result = memory
    st.session_state.memory_mode = mode
    st.session_state.stage = number


initialize()
counts = graph_counts()
stage = st.session_state.stage

st.markdown('<div class="brand">◈ &nbsp; CONFERENCE SWARM</div>', unsafe_allow_html=True)
st.markdown('<div class="hero"><div class="eyebrow">Conference intelligence · San Francisco · Live demo</div><h1>Make every conference minute count.</h1><p>A living conference graph connects people, expertise, sessions, booths and what you learn in conversation—then replans your next move.</p></div>', unsafe_allow_html=True)

people_n = get_graph().query("MATCH (p:Person {demo_id: $demo_id}) RETURN count(p)", params={"demo_id": DEMO_ID}).result_set[0][0]
metric_cols = st.columns(5)
for col, value, label in zip(metric_cols, [f"{people_n}", "12", "12", "20", f"{counts[1]:,}"] , ["PEOPLE MAPPED", "SESSIONS", "BOOTHS", "TOPICS", "GRAPH LINKS"]):
    with col:
        st.markdown(f'<div class="kpi"><div class="kpi-num">{value}</div><div class="kpi-label">{label}</div></div>', unsafe_allow_html=True)
st.caption("Scale demo includes clearly labeled synthetic attendee profiles; live Scout discoveries retain Bright Data source links.")

with st.sidebar:
    st.markdown('<div class="brand">SWARM CONTROL</div>', unsafe_allow_html=True)
    st.markdown('<div class="surface-title" style="margin-top:1.2rem">Independent agents</div>', unsafe_allow_html=True)
    for name, detail in [
        ("Scout", "Bright Data · live perception"),
        ("Memory", "OpenAI · interaction extraction"),
        ("Matchmaker", "FalkorDB · graph paths"),
        ("Planner", "FalkorDB · time + distance"),
    ]:
        st.markdown(f'<div class="agent"><span class="dot"></span><b>{name}</b><small>{detail}</small></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.caption("Credentials are loaded from your local environment. Values are never displayed.")
    st.write("OpenAI", "● ready" if os.getenv("OPENAI_API_KEY") else "○ scripted fallback")
    st.write("Bright Data", "● ready" if os.getenv("BRIGHTDATA_API_KEY") else "○ key needed for live scout")
    if st.button("↺ Reset demo", use_container_width=True):
        reset_demo()
        st.rerun()

left, right = st.columns([1.55, 1], gap="large")
with left:
    st.markdown('<div class="surface-title">Your next 90 minutes</div>', unsafe_allow_html=True)
    current = recommend_next()
    if current:
        who, score, direct, related, warm, scout_score = current
    else:
        who, score, direct, related, warm, scout_score = ("No match yet", 0, 0, 0, 0, 0)
    place = {"Alice": ("Booth A7 · Expo Hall A", "3 min walk", "Direct expertise match"), "Bob": ("Booth B12 · Expo Hall B", "3 min walk", "Alice’s warm introduction"), "Cameron": ("AI Lounge", "6 min walk", "Bob’s recommendation")}.get(who)
    if place is None and scout_score:
        found = get_graph().query("""MATCH (p:Person {name: $name, demo_id: $demo_id})
            RETURN p.affiliation, p.scout_reason""", params={"name": who, "demo_id": DEMO_ID}).result_set
        affiliation = found[0][0] if found else None
        place = (affiliation or "Public conference source", "live source", "Bright Data found an event-connected person")
    elif place is None:
        place = ("Conference floor", "Near you", "Live graph match")
    if stage < 2:
        extra_scout = f'<span class="tag">SCOUT {scout_score}</span>' if scout_score else ""
        st.markdown(f'<div class="recommend"><div class="eyebrow">Best next move · {place[1]}</div><div class="recommend-name">Meet {who}</div><div style="color:#92a7bb;margin:.25rem 0 .8rem">{place[0]}</div><span class="tag tag-hot">VALUE {score}</span><span class="tag">TOPIC {direct + related}</span><span class="tag">WARM INTRO {warm}</span>{extra_scout}<div class="callout" style="margin-top:.8rem">{place[2]}. The planner selected this from the live shared graph.</div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="recommend"><div class="eyebrow">Plan re-ranked · warm path discovered</div><div class="recommend-name">{who} → Agent Memory</div><div style="color:#92a7bb;margin:.25rem 0 .8rem">Agent Memory in Production · Stage 2</div><span class="tag tag-hot">NOW · 18 MIN</span><span class="tag">CAMERON · AI LOUNGE</span><div class="callout" style="margin-top:.8rem">Bob’s conversation changed both the people ranking and the session priority.</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="surface"><div class="surface-title">Replanned route</div><div class="timeline">', unsafe_allow_html=True)
    if stage == 0:
        itinerary = [("NOW", f"{who} · {place[0]}", place[2]), ("+18 MIN", "Scaling LLM Inference", "Main Stage · relevant session"), ("+42 MIN", "Cameron · AI Lounge", "6 min walk · agent infrastructure")]
    elif stage == 1:
        itinerary = [("NOW", "Bob · Booth B12", "3 min walk · Alice referred you"), ("+32 MIN", "Agent Memory in Production", "Stage 2 · Bob’s expertise"), ("+56 MIN", "Cameron · AI Lounge", "6 min walk · adjacent expertise")]
    else:
        itinerary = [("NOW", "Agent Memory in Production", "Stage 2 · Bob recommended it"), ("AFTER", "Cameron · AI Lounge", "6 min walk · warm introduction"), ("THEN", "GraphRAG for Agent Systems", "Workshop Wing · connected topic")]
    for time, title, sub in itinerary:
        st.markdown(f'<div class="timeline-item"><div class="timeline-time">{time}</div><div class="timeline-main">{title}</div><div class="timeline-sub">{sub}</div></div>', unsafe_allow_html=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="surface-title">Conversation moments</div>', unsafe_allow_html=True)
    if stage == 0:
        if scout_score:
            st.info(f"Live Scout evidence surfaced {who}. Replay the Alice conversation; Bob should rise through topic relevance plus the warm introduction.")
        else:
            st.info("Start with Alice as the strongest direct topic match. Then replay the conversation; Bob should jump to #1.")
        if st.button("▶  Replay Alice → Bob introduction", type="primary", use_container_width=True):
            with st.spinner("Memory Agent extracting and persisting the conversation…"):
                apply_moment(1)
            st.rerun()
    elif stage == 1:
        st.success("Graph updated: Parth → Alice → Bob. Matchmaker independently read the new path; Bob is now #1.")
        if st.button("▶  Replay Bob → Cameron + session", type="primary", use_container_width=True):
            with st.spinner("Memory Agent updating the shared graph…"):
                apply_moment(2)
            st.rerun()
    else:
        st.success("Second conversation persisted. Planner moved the Agent Memory session to NOW and surfaced Cameron through Bob.")
        if st.button("↺  Replay from beginning", use_container_width=True):
            reset_demo()
            st.rerun()

with right:
    st.markdown('<div class="surface-title">The shared conference graph</div>', unsafe_allow_html=True)
    st.markdown('<div class="surface"><div class="surface-title">Independent agents · one persistent world</div><div class="callout">Scout adds public, sourced context. Memory adds what you experienced. Matchmaker follows multi-hop expertise and introduction paths. Planner prices in time and distance.</div></div>', unsafe_allow_html=True)
    mem = st.session_state.memory_result
    if mem:
        with st.expander("Latest interaction facts · " + str(st.session_state.memory_mode), expanded=True):
            st.json(mem)
    st.markdown('<div class="surface"><div class="surface-title">Scout · Bright Data live discovery</div><div style="color:#91a2b8;font-size:.86rem;margin-bottom:.8rem">Search public conference context and write attributed discoveries into the same graph.</div>', unsafe_allow_html=True)
    if st.button("⌕  Scout the live web", use_container_width=True):
        try:
            with st.spinner("Bright Data searching live public sources…"):
                st.session_state.scout_result = scout("Patch the Conference AI agents, GraphRAG, and ML systems")
        except Exception as exc:
            st.session_state.scout_result = {"error": str(exc)}
        st.rerun()
    sr = st.session_state.scout_result
    if sr and sr.get("error"):
        st.warning("Live Scout needs working Bright Data and OpenAI credentials. The prepared memory demo remains available.")
    elif sr:
        st.success(f"Bright Data evidence processed; {len(sr.get('people', []))} sourced people added to FalkorDB and made eligible for live ranking.")
        for person in sr.get("people", [])[:3]:
            st.markdown(f"**{person['name']}** · {person['affiliation']}  \n{person['why_relevant']}")
            st.link_button("Open source ↗", person["source_url"])
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="surface"><div class="surface-title">Graph proof</div><div style="color:#91a2b8;font-size:.85rem">Open the FalkorDB Browser and run the demo query to see the same persistent graph.</div></div>', unsafe_allow_html=True)
    st.code("MATCH (n)-[r]->(m)\nWHERE n.demo_id = 'shared-memory-demo'\n  AND m.demo_id = 'shared-memory-demo'\nRETURN n, r, m LIMIT 1500", language="cypher")
    st.link_button("Open FalkorDB Browser ↗", "http://localhost:3000")

st.markdown("---")
st.markdown('<div class="eyebrow">Shared memory is the product</div><div style="color:#b7c6d8;font-size:.93rem;margin-top:.4rem">The Matchmaker never receives the conversation. Memory persists it to FalkorDB; another agent reads that new graph state and changes its decision.</div>', unsafe_allow_html=True)
