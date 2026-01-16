import requests
import streamlit as st

API_URL = "https://6x6d6t9bwj.execute-api.us-east-1.amazonaws.com/prod/nba/chat"


def call_chatbot(message: str) -> dict:
    try:
        payload = {"message": message}
        resp = requests.post(API_URL, json=payload, timeout=20)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {
            "answer": f"Error talking to chatbot API: {e}",
            "intent": "error",
            "debug": {},
        }


st.set_page_config(page_title="NBA Chatbot", page_icon="🏀", layout="centered")

st.title("🏀 NBA Chatbot ")
st.write(
    "Ask about **players, teams, standings, games, rosters**.\n\n"
    "Examples:\n"
    "- `Give me Stephen Curry's stats for this season`\n"
    "- `Show me Oklahoma City Thunder team stats`\n"
    "- `What are the NBA standings this season?`\n"
    "- `Who is on the OKC roster?`"
)

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Type your NBA question here...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            data = call_chatbot(user_input)

        answer = data.get("answer", "No answer returned.")
        intent = data.get("intent", "unknown")
        debug = data.get("debug", {})

        st.markdown(answer)

        with st.expander("🔍 Debug info"):
            st.write("**Intent:**", intent)
            st.json(debug)

        st.session_state.messages.append({"role": "assistant", "content": answer})
