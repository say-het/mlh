"""Readable, polished Streamlit command center for Agentic Explorer.

The dashboard is intentionally read-only. The agent writes telemetry to
``.agent_state.json`` and the dashboard refreshes itself while a mission runs.
"""

from __future__ import annotations

import html
import json
import os
import time
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from agentic_explorer.ui.swarm_diagram import generate_swarm_diagram

STATE_FILE = ".agent_state.json"
SCREENSHOT_FILE = ".latest_vision.jpg"
POLL_INTERVAL = 1.0


st.set_page_config(
    layout="wide",
    page_title="Agentic Explorer | Command Center",
    page_icon="🧭",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
    :root { --ink:#edf4ff; --muted:#8fa5c2; --panel:rgba(16,28,52,.82); --line:rgba(148,181,226,.16); --cyan:#62e7ff; --violet:#9d8cff; --green:#5ce1a7; --amber:#ffc56b; }
    html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
    .stApp { color:var(--ink); background:radial-gradient(circle at 8% 0%,rgba(86,116,255,.22),transparent 31rem),radial-gradient(circle at 92% 3%,rgba(42,216,205,.12),transparent 28rem),#07101f; }
    .block-container { max-width:1600px !important; padding:2.3rem 2.4rem 2.5rem !important; }
    header[data-testid="stHeader"] { background:transparent; }
    [data-testid="stSidebar"] { background:linear-gradient(180deg,#0b172c 0%,#091426 100%); border-right:1px solid var(--line); }
    [data-testid="stSidebar"] > div:first-child { padding:1.4rem 1rem; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label { color:var(--muted); }
    [data-testid="stSidebar"] hr { border-color:var(--line); margin:1.1rem 0; }
    h1, h2, h3, h4 { font-family:'Space Grotesk',sans-serif !important; color:var(--ink) !important; letter-spacing:-.02em; }
    h1 { font-size:clamp(2rem,4vw,3.6rem) !important; line-height:1.02 !important; }
    h2 { font-size:1.35rem !important; } h3 { font-size:1rem !important; margin:0 0 .65rem !important; }
    p, li, .stMarkdown { color:var(--muted); } code { color:var(--cyan) !important; background:rgba(98,231,255,.08) !important; border:1px solid rgba(98,231,255,.12); }
    .hero { position:relative; overflow:hidden; padding:2.1rem 2.2rem 1.8rem; border:1px solid var(--line); border-radius:24px; background:linear-gradient(120deg,rgba(26,45,82,.92),rgba(16,28,54,.74)); box-shadow:0 22px 60px rgba(0,0,0,.24); margin-bottom:1.1rem; }
    .hero:after { content:''; position:absolute; width:260px; height:260px; right:-80px; top:-100px; border-radius:50%; background:rgba(98,231,255,.12); filter:blur(4px); }
    .eyebrow { position:relative; z-index:1; color:var(--cyan); text-transform:uppercase; letter-spacing:.16em; font-size:.68rem; font-weight:700; }
    .hero h1 { position:relative; z-index:1; margin:.65rem 0 .7rem; }
    .hero-copy { position:relative; z-index:1; max-width:760px; font-size:1rem; line-height:1.65; color:#b6c7df; }
    .hero-meta { position:relative; z-index:1; display:flex; flex-wrap:wrap; gap:.55rem; margin-top:1.25rem; }
    .chip, .status-pill { display:inline-flex; align-items:center; gap:.4rem; border:1px solid var(--line); border-radius:999px; padding:.42rem .7rem; background:rgba(7,16,31,.35); color:#bed1e9; font-size:.76rem; }
    .status-pill.live { color:var(--green); border-color:rgba(92,225,167,.35); background:rgba(92,225,167,.08); }
    .status-dot { width:7px; height:7px; border-radius:50%; background:currentColor; box-shadow:0 0 12px currentColor; }
    .section-kicker { color:var(--violet); font-size:.68rem; text-transform:uppercase; letter-spacing:.14em; font-weight:700; margin:1.2rem 0 .35rem; }
    .section-title { color:var(--ink); font-family:'Space Grotesk',sans-serif; font-size:1.15rem; font-weight:700; margin-bottom:.8rem; }
    .metric-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:.75rem; margin:.9rem 0 1.15rem; }
    .metric-card { padding:1rem 1.05rem; border:1px solid var(--line); border-radius:16px; background:linear-gradient(145deg,rgba(21,38,70,.92),rgba(12,24,45,.9)); min-height:92px; }
    .metric-label { color:var(--muted); font-size:.72rem; text-transform:uppercase; letter-spacing:.1em; font-weight:700; }
    .metric-value { color:var(--ink); font:700 1.8rem 'Space Grotesk',sans-serif; margin-top:.35rem; }
    .metric-note { color:#7790b1; font-size:.72rem; margin-top:.15rem; }
    .coverage-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:.65rem; margin:.7rem 0 1rem; }
    .coverage-item { padding:.75rem .85rem; border:1px solid var(--line); border-radius:12px; background:rgba(13,27,49,.72); }
    .coverage-item strong { display:block; color:var(--ink); font:600 .88rem 'Space Grotesk',sans-serif; margin-bottom:.18rem; }
    .coverage-item span { color:var(--muted); font-size:.72rem; }
    .path-chip { display:inline-block; margin:.2rem .25rem .2rem 0; padding:.35rem .55rem; border:1px solid rgba(98,231,255,.2); border-radius:999px; color:#b9d9e8; background:rgba(98,231,255,.06); font-size:.72rem; }
    .timeline { display:flex; flex-direction:column; gap:.6rem; max-height:380px; overflow:auto; padding-right:.2rem; }
    .timeline-item { display:grid; grid-template-columns:9px 1fr; gap:.65rem; padding:.65rem .7rem; border:1px solid var(--line); border-radius:12px; background:rgba(13,27,49,.62); }
    .timeline-dot { width:9px; height:9px; margin-top:.35rem; border-radius:50%; background:var(--cyan); box-shadow:0 0 12px rgba(98,231,255,.6); }
    .timeline-dot.warn { background:var(--amber); box-shadow:0 0 12px rgba(255,197,107,.55); }
    .timeline-title { color:var(--ink); font-size:.78rem; font-weight:700; }
    .timeline-detail { color:var(--muted); font-size:.72rem; line-height:1.45; margin-top:.12rem; }
    .report-preview { max-height:300px; overflow:auto; padding:.9rem; border:1px solid var(--line); border-radius:12px; background:#091426; color:#bcd0ea; font-size:.78rem; line-height:1.6; white-space:pre-wrap; }
    .evidence-label { color:var(--muted); font-size:.72rem; margin:.35rem 0 .65rem; }
    .panel { border:1px solid var(--line); border-radius:18px; padding:1rem 1.1rem; background:var(--panel); box-shadow:0 16px 40px rgba(0,0,0,.14); }
    .panel-title { color:var(--ink); font:600 1rem 'Space Grotesk',sans-serif; } .panel-subtitle { color:var(--muted); font-size:.74rem; }
    .empty-card { text-align:center; padding:4.5rem 2rem; border:1px dashed rgba(98,231,255,.28); border-radius:20px; background:rgba(14,30,55,.62); }
    .empty-icon { font-size:3.2rem; margin-bottom:.7rem; } .empty-title { color:var(--ink); font:700 1.45rem 'Space Grotesk',sans-serif; }
    .empty-copy { max-width:560px; margin:.55rem auto 0; line-height:1.6; color:var(--muted); }
    .stTabs [data-baseweb="tab-list"] { gap:.25rem; border-bottom:1px solid var(--line); }
    .stTabs [data-baseweb="tab"] { color:var(--muted); padding:.55rem .7rem; font-size:.76rem; }
    .stTabs [aria-selected="true"] { color:var(--cyan) !important; }
    .stAlert { border-radius:13px !important; } [data-testid="stImage"] img { border-radius:14px; border:1px solid var(--line); }
    [data-testid="stExpander"] { background:rgba(13,27,49,.72); border:1px solid var(--line); border-radius:12px; }
    @media (max-width:900px) { .metric-grid { grid-template-columns:repeat(2,minmax(0,1fr)); } .block-container { padding:1.2rem !important; } }
</style>
""",
    unsafe_allow_html=True,
)


def _load_state() -> dict:
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, PermissionError, OSError):
        return {}


def _safe(value: object, limit: int | None = None) -> str:
    text = html.escape(str(value if value is not None else ""))
    return text if limit is None else text[:limit]


def _age(timestamp: float) -> tuple[str, bool]:
    seconds = max(0, time.time() - timestamp) if timestamp else 0
    return (f"{seconds:.0f}s ago", seconds > 30)


def _metric_grid(items: list[tuple[str, object, str]]) -> None:
    cards = []
    for label, value, note in items:
        cards.append(f'<div class="metric-card"><div class="metric-label">{_safe(label)}</div><div class="metric-value">{_safe(value)}</div><div class="metric-note">{_safe(note)}</div></div>')
    st.markdown(f'<div class="metric-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


def _hero(state: dict, *, completed: bool = False) -> None:
    app_url = _safe(state.get("app_url", "Local application"))
    provider = _safe(state.get("provider", "Gemini"))
    model = _safe(state.get("model_name", "model"))
    mission = _safe(state.get("mission_id", "Waiting for mission"))
    if completed:
        pill = '<span class="status-pill live"><span class="status-dot"></span>Mission complete</span>'
        title = "Exploration complete. Evidence captured."
        copy = "The swarm finished its pass across the target application. Review the findings, action tape, and generated reproduction artifacts below."
    else:
        pill = '<span class="status-pill live"><span class="status-dot"></span>Live command center</span>'
        title = "See your application through an AI tester’s eyes."
        copy = "A focused QA swarm is exploring the browser, recording every action, and turning confirmed issues into reproducible evidence."
    st.markdown(f'<div class="hero"><div class="eyebrow">Agentic Explorer · Visual QA</div><h1>{title}</h1><div class="hero-copy">{copy}</div><div class="hero-meta">{pill}<span class="chip">Target · {app_url}</span><span class="chip">Mission · {mission}</span><span class="chip">{provider} · {model}</span></div></div>', unsafe_allow_html=True)


def _empty_state() -> None:
    st.markdown('<div class="empty-card"><div class="empty-icon">🛰️</div><div class="empty-title">Command center standing by</div><div class="empty-copy">Start an Agentic Explorer mission and this space will fill with live browser vision, swarm routing, thought traces, action telemetry, and confirmed bugs.</div></div>', unsafe_allow_html=True)
    _metric_grid([("Browser vision", "Ready", "waiting for first frame"), ("Swarm graph", "Standby", "supervisor is idle"), ("Evidence", "0", "screenshots captured"), ("Telemetry", "Live", "polling every second")])
    time.sleep(POLL_INTERVAL)
    st.rerun()


def _sidebar(state: dict) -> None:
    with st.sidebar:
        st.markdown("## 🧭 Explorer")
        st.caption("Autonomous browser intelligence")
        st.divider()
        st.markdown("#### Mission context")
        st.markdown(f"**Target**  \n`{_safe(state.get('app_url', 'N/A'))}`")
        st.markdown(f"**Mission**  \n`{_safe(state.get('mission_id', 'N/A'))}`")
        st.markdown(f"**Graph**  \n`{_safe(state.get('mission_type', state.get('graph_type', 'N/A')))}`")
        st.divider()
        st.markdown("#### Run health")
        active = state.get("active_node") or "Idle"
        age_text, stale = _age(state.get("timestamp", 0))
        st.markdown(f"Active node  \n**{_safe(active)}**")
        st.markdown(f"Last telemetry  \n**{_safe(age_text)}**")
        if stale:
            st.warning("Telemetry is stale. The agent may be paused or finished.")
        else:
            st.success("Telemetry stream is healthy.")
        st.divider()
        st.caption("Artifacts are written to the report_* folders in the project directory.")


def _render_tabs(state: dict) -> None:
    missions_tab, thought_tab, tape_tab, bugs_tab, paths_tab = st.tabs(["Missions", "Thought stream", "Action tape", "Bugs", "Paths"])
    with missions_tab:
        history = state.get("mission_history", [])
        if not history:
            st.info("No mission history yet.")
        for mission in reversed(history):
            status = mission.get("status", "unknown")
            icon = "✅" if status == "completed" else "◉"
            duration = (mission.get("end_time") or time.time()) - (mission.get("start_time") or time.time())
            label = f"{icon} {mission.get('id', 'mission')} · {duration:.0f}s · {mission.get('bugs_count', 0)} bugs"
            with st.expander(label, expanded=status == "running"):
                st.caption(f"Status: {status} · Type: {mission.get('type', 'N/A')}")
                st.write(mission.get("description", ""))
    with thought_tab:
        stream = state.get("thought_stream", [])
        if not stream:
            st.info("The swarm’s reasoning will appear here.")
        for entry in reversed(stream[-40:]):
            st.markdown(f"**{_safe(entry.get('node', '?'))}**  {_safe(entry.get('text', ''))}")
    with tape_tab:
        tape = state.get("action_tape_recent", [])
        if not tape:
            st.info("Browser actions will appear here as they are recorded.")
        for entry in reversed(tape[-25:]):
            ok = "✅" if entry.get("ok") else "⚠️"
            st.markdown(f"{ok} **{_safe(entry.get('action', '?'))}** · {entry.get('duration_ms', 0)} ms · `{_safe(entry.get('page_url', ''))}`")
    with bugs_tab:
        bugs = state.get("bugs_found", [])
        if not bugs:
            st.success("No confirmed issues yet. Keep exploring.")
        else:
            st.markdown(f"**{len(bugs)} confirmed issue(s)**")
            for index, bug in enumerate(bugs, 1):
                with st.expander(f"Issue {index}", expanded=index == len(bugs)):
                    st.markdown(bug)
    with paths_tab:
        paths = state.get("explored_paths", [])
        if not paths:
            st.info("Explored routes will appear here.")
        for path in paths:
            st.markdown(f"• `{_safe(path)}`")


def _quality_snapshot(state: dict) -> None:
    tape = state.get("action_tape_recent", [])
    failed = [entry for entry in tape if not entry.get("ok", True)]
    durations = [entry.get("duration_ms", 0) for entry in tape if entry.get("duration_ms")]
    mission_id = state.get("mission_id", "")
    screenshot_dir = Path(f"report_{mission_id}") / "screenshots"
    screenshot_count = len(list(screenshot_dir.glob("*.png"))) if mission_id else 0
    report_exists = bool(mission_id and (Path(f"report_{mission_id}") / "test_report.md").exists())
    avg_latency = f"{sum(durations) / len(durations):.0f} ms" if durations else "—"
    _metric_grid([
        ("Browser actions", len(tape), "recent recorded actions"),
        ("Action errors", len(failed), "recoverable browser failures"),
        ("Avg latency", avg_latency, "engine response time"),
        ("Evidence", screenshot_count, "bug screenshots captured"),
    ])
    st.markdown(
        f'<div class="coverage-grid"><div class="coverage-item"><strong>Report artifact</strong><span>{"Ready to review" if report_exists else "Building during mission"}</span></div><div class="coverage-item"><strong>Current focus</strong><span>{_safe(state.get("active_node") or "Starting")}</span></div><div class="coverage-item"><strong>Last action</strong><span>{_safe(state.get("last_action") or "No browser action yet", 120)}</span></div></div>',
        unsafe_allow_html=True,
    )


def _coverage_panel(state: dict) -> None:
    paths = list(dict.fromkeys(state.get("explored_paths", [])))
    bugs = state.get("bugs_found", [])
    st.markdown('<div class="section-kicker">Coverage map</div><div class="section-title">What the swarm has touched</div>', unsafe_allow_html=True)
    if paths:
        chips = "".join(f'<span class="path-chip">{_safe(path)}</span>' for path in paths[:24])
        st.markdown(f'<div class="panel"><div class="panel-title">Explored routes</div><div class="evidence-label">{len(paths)} unique route(s) recorded</div>{chips}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="panel"><div class="panel-title">No routes recorded yet</div><div class="evidence-label">The route map will fill in as the browser moves beyond authentication.</div></div>', unsafe_allow_html=True)


def _evidence_panel(state: dict) -> None:
    mission_id = state.get("mission_id", "")
    report_path = Path(f"report_{mission_id}") / "test_report.md" if mission_id else None
    screenshot_dir = Path(f"report_{mission_id}") / "screenshots" if mission_id else None
    st.markdown('<div class="section-kicker">Evidence vault</div><div class="section-title">Presentation-ready artifacts</div>', unsafe_allow_html=True)
    report_col, shots_col = st.columns([1.2, .8], gap="large")
    with report_col:
        st.markdown('<div class="panel"><div class="panel-title">Executive report</div><div class="evidence-label">Generated Markdown summary</div>', unsafe_allow_html=True)
        if report_path and report_path.exists():
            st.markdown(f'<div class="report-preview">{_safe(report_path.read_text(encoding="utf-8", errors="replace")[:4500])}</div>', unsafe_allow_html=True)
        else:
            st.info("The report will appear here after the mission completes.")
        st.markdown('</div>', unsafe_allow_html=True)
    with shots_col:
        st.markdown('<div class="panel"><div class="panel-title">Screenshot evidence</div><div class="evidence-label">Captured browser states</div>', unsafe_allow_html=True)
        shots = sorted(screenshot_dir.glob("*.png"), key=lambda path: path.stat().st_mtime, reverse=True)[:4] if screenshot_dir and screenshot_dir.exists() else []
        if shots:
            for shot in shots:
                st.image(str(shot), use_container_width=True, caption=shot.name)
        else:
            st.info("No screenshot evidence captured yet.")
        st.markdown('</div>', unsafe_allow_html=True)


def _timeline_panel(state: dict) -> None:
    tape = state.get("action_tape_recent", [])
    thoughts = state.get("thought_stream", [])
    items = []
    for entry in tape[-12:]:
        ok = entry.get("ok", True)
        items.append(("warn" if not ok else "ok", f"Browser · {entry.get('action', 'action')}", f"{entry.get('duration_ms', 0)} ms · {entry.get('page_url', '')}"))
    for entry in thoughts[-8:]:
        items.append(("ok", f"{entry.get('node', 'Agent')} · reasoning", entry.get("text", "")))
    st.markdown('<div class="section-kicker">Live investigation</div><div class="section-title">Readable event timeline</div>', unsafe_allow_html=True)
    if not items:
        st.info("The timeline will populate as agents reason and act.")
        return
    cards = []
    for tone, title, detail in reversed(items[-18:]):
        cards.append(f'<div class="timeline-item"><span class="timeline-dot {"warn" if tone == "warn" else ""}"></span><div><div class="timeline-title">{_safe(title)}</div><div class="timeline-detail">{_safe(detail, 500)}</div></div></div>')
    st.markdown(f'<div class="timeline">{"".join(cards)}</div>', unsafe_allow_html=True)


def _main() -> None:
    state = _load_state()
    if not state:
        _hero({}, completed=False)
        _empty_state()
        return
    if state.get("completed", False):
        _hero(state, completed=True)
        _metric_grid([("Missions", state.get("total_missions", 0), "run total"), ("Final step", state.get("step_count", 0), "agent steps"), ("Bugs found", state.get("bugs_count", 0), "confirmed issues"), ("Paths explored", len(state.get("explored_paths", [])), "unique routes")])
        st.markdown('<div class="section-kicker">Executive view</div><div class="section-title">What the swarm discovered</div>', unsafe_allow_html=True)
        _quality_snapshot(state)
        _coverage_panel(state)
        _evidence_panel(state)
        _render_tabs(state)
        return
    _sidebar(state)
    _hero(state)
    _metric_grid([("Current step", state.get("step_count", 0), "of the active mission"), ("Bugs found", state.get("bugs_count", 0), "confirmed issues"), ("Paths explored", len(state.get("explored_paths", [])), "unique routes"), ("Active node", state.get("active_node") or "Starting", "swarm focus")])
    _quality_snapshot(state)
    browser_col, swarm_col = st.columns([1.35, 1], gap="large")
    with browser_col:
        st.markdown('<div class="section-kicker">Browser vision</div><div class="section-title">Live target viewport</div>', unsafe_allow_html=True)
        if os.path.exists(SCREENSHOT_FILE):
            mtime = os.path.getmtime(SCREENSHOT_FILE)
            st.image(SCREENSHOT_FILE, use_container_width=True, caption=f"Latest frame · updated {time.time() - mtime:.0f}s ago")
        else:
            st.markdown('<div class="panel"><div class="panel-title">Waiting for first browser frame</div><div class="panel-subtitle">The screenshot will appear after the agent opens the target.</div></div>', unsafe_allow_html=True)
    with swarm_col:
        st.markdown('<div class="section-kicker">Swarm telemetry</div><div class="section-title">Who is driving the run?</div>', unsafe_allow_html=True)
        mermaid_code = generate_swarm_diagram(state.get("active_node", ""), state.get("graph_type", "standard"))
        mermaid_html = f'''<div style="height:425px;overflow:auto;border:1px solid rgba(148,181,226,.16);border-radius:16px;background:#0b172c;padding:12px;"><pre class="mermaid">{mermaid_code}</pre></div><script type="module">import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs'; mermaid.initialize({{startOnLoad:true,theme:'dark',themeVariables:{{primaryColor:'#243a6b',primaryTextColor:'#edf4ff',lineColor:'#62e7ff',fontFamily:'DM Sans'}}}});</script>'''
        components.html(mermaid_html, height=455, scrolling=True)
    _coverage_panel(state)
    _timeline_panel(state)
    _evidence_panel(state)
    st.markdown('<div class="section-kicker">Investigation log</div><div class="section-title">Every signal, in one place</div>', unsafe_allow_html=True)
    _render_tabs(state)
    time.sleep(POLL_INTERVAL)
    st.rerun()


_main()
