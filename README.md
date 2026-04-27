# Drishti ☀️

A Vedic astrology (Jyotish) chatbot powered by your choice of AI — Claude, Groq, Gemini, or a local Ollama model.

Enter your birth details and ask Drishti anything about your chart: lagna, planetary placements, nakshatras, dashas, yogas, and more.

---

## Setup

### 1. Clone the repo

```bash
git clone <your-repo-url>
cd drishti
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

> Every time you open a new terminal, re-activate with:
> ```bash
> source ~/Documents/drishti/venv/bin/activate
> ```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the server

```bash
python app.py
```

Open your browser at **http://localhost:5050**

---

## Getting API Keys

Drishti supports four AI backends. Keys are entered in the browser (⚙ Settings) and never stored on the server.

| Provider | Free? | Where to get a key |
|---|---|---|
| **Claude** (Anthropic) | Paid (free credits on signup) | [console.anthropic.com](https://console.anthropic.com) → API Keys |
| **Groq** | Free tier | [console.groq.com](https://console.groq.com) → API Keys |
| **Gemini** (Google) | Free tier (1500 req/day) | [aistudio.google.com](https://aistudio.google.com) → Get API Key |
| **Ollama** | Completely free | No key needed — install [Ollama](https://ollama.com) and run `ollama pull llama3` |

---

## Usage

1. Click **⚙ Settings** (top right) and paste your API key
2. Select your preferred AI model
3. Enter your birth date, time, and city
4. Click **Calculate My Chart**
5. Ask anything — or use the suggestion chips to get started

---

## Troubleshooting

**`pyswisseph` fails to install on Mac:**
```bash
pip install pyswisseph --no-binary pyswisseph
```

**City not found:**
Try a more specific name, e.g. `Mumbai, Maharashtra, India`

**`(venv)` not showing in terminal:**
You need to activate the virtual environment — see Step 2 above.
