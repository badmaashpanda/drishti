import os
from flask import Flask, render_template, request, jsonify, session
from chart import calculate_chart, chart_to_summary

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "drishti-secret-dev")

SYSTEM_PROMPT = """You are Drishti, a wise and knowledgeable Jyotish (Vedic astrology) guide.
You have deep expertise in classical Jyotish principles including:
- Graha (planetary) dignities: exaltation, debilitation, own sign, moolatrikona
- Bhava (house) analysis and bhava lords
- Yoga identification (Raj yoga, Dhana yoga, Kemadruma, Neecha Bhanga, etc.)
- Vimshottari dasha interpretation
- Nakshatra characteristics and their influence
- Graha aspects (full aspects, special aspects of Mars, Jupiter, Saturn)
- Natural and functional benefics/malefics based on lagna

The user's birth chart is provided below. Use it as the factual foundation for all your answers.
Interpret using classical Jyotish — reference Brihat Parashara Hora Shastra (BPHS) principles where relevant.
Be warm, thoughtful, and explain your reasoning in plain English.
When you don't know something with confidence, say so rather than guessing.
Keep responses focused and conversational — 2 to 4 paragraphs unless asked for more detail.

{chart_summary}"""

LLM_INFO = {
    "claude": {"name": "Claude",        "model": "claude-sonnet-4-6",   "needs_key": True},
    "groq":   {"name": "Groq",          "model": "llama3-70b-8192",     "needs_key": True},
    "gemini": {"name": "Gemini",        "model": "gemini-1.5-flash",    "needs_key": True},
    "ollama": {"name": "Ollama (local)","model": "llama3",              "needs_key": False},
}


def get_llm_response(provider, messages, system, api_key=None):
    info = LLM_INFO[provider]

    if provider == "claude":
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=info["model"],
            max_tokens=1024,
            system=system,
            messages=messages,
        )
        return response.content[0].text

    elif provider == "groq":
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        response = client.chat.completions.create(
            model=info["model"],
            messages=[{"role": "system", "content": system}] + messages,
            max_tokens=1024,
        )
        return response.choices[0].message.content

    elif provider == "gemini":
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name=info["model"], system_instruction=system)
        history = [
            {"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]}
            for m in messages[:-1]
        ]
        chat = model.start_chat(history=history)
        return chat.send_message(messages[-1]["content"]).text

    elif provider == "ollama":
        from openai import OpenAI
        client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        response = client.chat.completions.create(
            model=info["model"],
            messages=[{"role": "system", "content": system}] + messages,
            max_tokens=1024,
        )
        return response.choices[0].message.content

    else:
        raise ValueError(f"Unknown provider: {provider}")


@app.route("/")
def index():
    session.clear()
    return render_template("index.html")


@app.route("/calculate", methods=["POST"])
def calculate():
    data = request.json
    date_str = data.get("date")
    time_str = data.get("time")
    city = data.get("city")

    if not all([date_str, time_str, city]):
        return jsonify({"error": "Please provide date, time, and city."}), 400

    try:
        chart = calculate_chart(date_str, time_str, city)
        summary = chart_to_summary(chart)
        session["chart_summary"] = summary
        session["messages"] = []
        return jsonify({"success": True, "summary": summary})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/chat", methods=["POST"])
def chat():
    if "chart_summary" not in session:
        return jsonify({"error": "No chart loaded. Please enter your birth details first."}), 400

    data = request.json
    user_message = data.get("message", "").strip()
    provider = data.get("provider", "claude")
    api_key = data.get("api_key", "").strip() or None

    if provider not in LLM_INFO:
        return jsonify({"error": f"Unknown provider: {provider}"}), 400
    if not user_message:
        return jsonify({"error": "Empty message."}), 400
    if LLM_INFO[provider]["needs_key"] and not api_key:
        return jsonify({"error": f"An API key is required for {LLM_INFO[provider]['name']}. Open Settings to add it."}), 400

    messages = session.get("messages", [])
    messages.append({"role": "user", "content": user_message})
    system = SYSTEM_PROMPT.format(chart_summary=session["chart_summary"])

    try:
        reply = get_llm_response(provider, messages, system, api_key=api_key)
        messages.append({"role": "assistant", "content": reply})
        session["messages"] = messages
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5050)
