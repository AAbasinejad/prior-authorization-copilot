# Prior Auth Copilot

A production-style Python starter for prior authorization automation.

## Capabilities
- intake via FastAPI
- clinical note signal extraction
- payer/procedure rule checking
- missing-document detection
- denial-risk scoring
- packet summary generation
- Streamlit operations dashboard

## Run
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.api.main:app --reload --port 8000
```

In another terminal:
```bash
source .venv/bin/activate
streamlit run streamlit_app.py
```

Optional demo seed:
```bash
python seed_demo.py
```
