# Judge Runbook

Agentic Explorer is a Gemini-powered browser QA swarm with a live Streamlit
command center and a local BugGarden demo application.

## Quick start

1. Create a local `.env` from `.env.example`.
2. Add your own `GOOGLE_API_KEY` and keep the file uncommitted.
3. Install the project and browser runtime:

   ```powershell
   pip install -e ".[visual]"
   playwright install chromium
   ```

4. Start the demo application in one terminal:

   ```powershell
   python demo_app/server.py
   ```

5. Start a Gemini visual mission from a second terminal:

   ```powershell
   agent-explorer --missions missions/gemini_smoke.yaml --provider gemini --headed --visual --max-steps 4
   ```

6. Open the command center at <http://127.0.0.1:8501/>.

The demo application is available at <http://127.0.0.1:5601/>. Its safe demo
account is `demo` / `demo123`.

## What to show

The mission is intentionally presentation-oriented. After login it explores the
application map, search and risk filtering, discovery controls, the scan flow,
the report-a-signal form, and the recent-signals feed. The dashboard exposes:

- live browser vision and action latency;
- a readable thought and browser event timeline;
- coverage routes and current swarm node;
- confirmed bugs and screenshot evidence;
- the generated executive report and reproduction artifacts.

## Public repository safety

API keys, `.env`, browser authentication state, SQLite memory, screenshots, and
mission reports are runtime artifacts and are excluded by `.gitignore`. Never
commit a real API key. The included demo credentials are local-only credentials
for BugGarden and do not grant access to an external service.
