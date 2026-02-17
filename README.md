# Gemini Web Proxy

A lightweight proxy that turns the Google Gemini Web into an OpenAI-compatible API.

This project uses `playwright` to run a real browser instance (Chrome/Chromium) in the background. It acts as a bridge:
1. Receives an API request (OpenAI format).
2. Automates the browser to type the prompt into `gemini.google.com`.
3. Streams the response text back to the API client in real-time.
4. Manages authentication cookies to keep the session alive.

## Installation

```bash
pip install -r requirements.txt
playwright install chromium
```

## Configuration

Copy the example config and adjust if needed:

```bash
cp .env.example .env
```

* HEADLESS: Set to `False` to see the browser
* MAX_REQUESTS_PER_MIN: Adjust rate limits.

## First Run & Login

```bash
python main.py
```

A browser window will open. Log in to your Google Account manually. Once logged in, the session cookies are saved to `auth/gemini_state.json`. The proxy will automatically enable **Temporary Chat** to keep your history clean.

## API Usage

The server runs at `http://localhost:8000`. It supports the standard OpenAI chat completion format.

**API Key**: You can leave it as `sk-any` or any non-empty string.

## Examples

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-1.5-pro",
    "messages": [{"role": "user", "content": "Hello, how are you?"}],
    "stream": true
  }'
```

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="sk-any" # Required but unused
)

response = client.chat.completions.create(
    model="gemini-1.5-pro",
    messages=[{"role": "user", "content": "Explain quantum physics"}],
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

## Disclaimer

**PLEASE READ CAREFULLY BEFORE USE:**

**Account Ban Risk: This tool automates a personal Google account. There is a significant risk that your Google account could be suspended, banned, or disabled for using this tool. DO NOT use your primary Google account. Use a burner account.**

**Headless Mode Detection: Running the browser in "Headless Mode" (invisible window) significantly increases the chance of being detected as a bot by Google's anti-fraud systems. Use HEADLESS=False (visible mode) for a safer (though not risk-free) experience.**

**No Liability: This software is provided "AS IS", without warranty of any kind. The author/maintainer is NOT responsible for any damages, data loss, or account bans resulting from the use of this tool. You use this software entirely at your own risk.**

**Unofficial Tool: This project is not affiliated with, endorsed by, or connected to Google or Gemini.**
