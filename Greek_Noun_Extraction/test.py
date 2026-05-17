import requests

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "qwen2.5:14b",
        "prompt": "Test prompt",
        "stream": False,
        "options": {
            "temperature": 0,
            "top_p": 0.1,
            "repeat_penalty": 1.0
        }
    }
)

print(response.json()["response"])