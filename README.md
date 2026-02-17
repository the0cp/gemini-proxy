# Gemini Web Proxy

A lightweight proxy that turns the Google Gemini Web into an OpenAI-compatible API.

This project uses `playwright` to run a real browser instance (Chrome/Chromium) in the background. It acts as a bridge:
1. Receives an API request (OpenAI format).
2. Automates the browser to type the prompt into `gemini.google.com`.
3. Streams the response text back to the API client in real-time.
4. Manages authentication cookies to keep the session alive.

## Features

This project is more than just a wrapper; it implements advanced techniques to mimic a real human user.

*   **OpenAI API Compatible**: Drop-in replacement for OpenAI clients. Use it with existing tools like LangChain, TavernAI, or custom scripts.
*   **Stealth & Anti-Detect**:
    *   **Fingerprint Randomization**: Rotates between Windows, macOS, and Linux browser signatures.
    *   **Deep Consistency**: Synchronizes HTTP User-Agents with JavaScript `navigator` properties to pass rigid consistency checks.
    *   **Context Masking**: Uses `playwright-stealth` to hide WebDriver signals.
*   **Human-like Behavior Simulation**:
    *   **Natural Typing**: Abandoned instant text injection (`fill()`) in favor of character-by-character typing with variable speed (10ms-50ms jitter). Long prompts (e.g., 2000+ chars) will take a few seconds to "type" into the browser before sending.
    *   **Randomized Interactions**: Includes "hesitation" delays (0.5s-1.5s) before clicking buttons to simulate human thought processes and mouse movement.
    *   **Dynamic Waits**: Avoids fixed sleep timers, making the bot's behavior unpredictable to pattern-matching algorithms.
*   **Session Persistence**: Automatically saves and loads authentication cookies (`auth/gemini_state.json`) to maintain login state across restarts.

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
