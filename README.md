# sse_asyncio

A full stack project to demo how to use Server-Sent Events.

### How to run

```bash
# Configure Python environment
python3 --version
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Start redis in background
docker-compose up redis -d
# Start database in background
docker-compose up database -d
# Start server
export DEBUG=1
export DATABASE_URL=postgres://sse_asyncio:mysecretpassword@127.0.0.1:5432/sse_asyncio
python -m uvicorn sse_asyncio.main:app --reload
# Open browser, hit http://127.0.0.1:8000, keep refreshing until page is ready
# To load demo/test data:
curl --location --request POST 'http://localhost:8000/load-test-data'
```
