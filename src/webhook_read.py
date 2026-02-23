from flask import Flask, request
import json
from pathlib import Path
from datetime import datetime

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent  # .../projeto1python
PASTA = BASE_DIR / "data" / "read_payloads"
PASTA.mkdir(parents=True, exist_ok=True)

@app.post("/read-webhook")
def read_webhook():
    data = request.get_json(force=True, silent=True) or {}

    session_id = data.get("session_id", "no_session")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = PASTA / f"read_{ts}_{session_id}.json"

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True}
@app.post("/")
def root_post():
    # fallback: se o Read IA mandar pra "/"
    return read_webhook()

@app.post("/read-webhook/")
def read_webhook_slash():
    # fallback: se vier com barra no final
    return read_webhook()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

