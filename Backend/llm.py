import os, json, requests

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "openai/gpt-oss-20b"

def call_llm_json(system: str, user: str) -> dict:
    r = requests.post(
        GROQ_URL,
        headers={"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}"},
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "response_format": {"type": "json_object"},
        },
        timeout=90,
    )
    r.raise_for_status()
    return json.loads(r.json()["choices"][0]["message"]["content"])