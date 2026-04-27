import os
import sys
from chart import calculate_chart, chart_to_summary

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

PROVIDERS = {
    "1": ("claude",  "Claude (Anthropic) — best quality, needs ANTHROPIC_API_KEY"),
    "2": ("groq",    "Groq (Llama 3)    — free tier, needs GROQ_API_KEY"),
    "3": ("gemini",  "Gemini (Google)   — free tier, needs GEMINI_API_KEY"),
    "4": ("ollama",  "Ollama (local)    — free, private, needs ollama running locally"),
}


def pick_provider():
    print("\nChoose your AI guide:")
    for num, (_, label) in PROVIDERS.items():
        print(f"  {num}. {label}")
    while True:
        choice = input("\nEnter 1-4: ").strip()
        if choice in PROVIDERS:
            return PROVIDERS[choice][0]
        print("Please enter a number between 1 and 4.")


def get_api_key(provider):
    env_map = {
        "claude": "ANTHROPIC_API_KEY",
        "groq":   "GROQ_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "ollama": None,
    }
    env_key = env_map[provider]
    if not env_key:
        return None

    key = os.environ.get(env_key, "").strip()
    if not key:
        key = input(f"Paste your {env_key}: ").strip()
    return key or None


def get_llm_response(provider, messages, system, api_key):
    if provider == "claude":
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system,
            messages=messages,
        )
        return response.content[0].text

    elif provider == "groq":
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "system", "content": system}] + messages,
            max_tokens=1024,
        )
        return response.choices[0].message.content

    elif provider == "gemini":
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction=system)
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
            model="llama3",
            messages=[{"role": "system", "content": system}] + messages,
            max_tokens=1024,
        )
        return response.choices[0].message.content


def main():
    print("\n✦ Welcome to Drishti — Vedic Astrology ✦")
    print("─" * 42)

    provider = pick_provider()
    api_key = get_api_key(provider)

    print("\nEnter your birth details:")
    date_str = input("  Date (YYYY-MM-DD): ").strip()
    time_str = input("  Time (HH:MM, 24h): ").strip()
    city     = input("  City: ").strip()

    print("\nCalculating your chart...")
    try:
        chart = calculate_chart(date_str, time_str, city)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    summary = chart_to_summary(chart)
    print("\n" + "─" * 42)
    print(summary)
    print("─" * 42)

    system = SYSTEM_PROMPT.format(chart_summary=summary)
    messages = []

    print("\nYour chart is ready. Ask me anything (or type 'quit' to exit).\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nNamaste. Until next time.")
            break

        if user_input.lower() in ("quit", "exit", "q"):
            print("Namaste. Until next time.")
            break
        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})

        try:
            reply = get_llm_response(provider, messages, system, api_key)
            messages.append({"role": "assistant", "content": reply})
            print(f"\nDrishti: {reply}\n")
        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()
