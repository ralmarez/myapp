import streamlit as st
import pandas as pd

st.set_page_config(page_title="myapp", layout="centered")

st.title("Flash")

import pandas as pd




import streamlit as st
import pandas as pd

# --- Load original deck once ---
if "original_deck" not in st.session_state:
    st.session_state["original_deck"] = pd.read_csv(r"C:\Users\ralmarez\Downloads\flash.csv") # columns: front, back, Tense, Person

# --- Manual shuffle function ---
def reshuffle_deck():
    st.session_state["shuffled_deck"] = st.session_state["original_deck"].sample(frac=1).reset_index(drop=True)
    st.session_state["index"] = 0
    st.session_state["show_back"] = False

# --- Initialize shuffled deck ---
if "shuffled_deck" not in st.session_state:
    reshuffle_deck()

df = st.session_state["shuffled_deck"]

# --- Filters ---
st.sidebar.header("🧠 Filter Deck")
selected_tense = st.sidebar.selectbox("Tense", ["All"] + sorted(df["Tense"].dropna().unique()))
selected_person = st.sidebar.selectbox("Person", ["All"] + sorted(df["Person"].dropna().unique()))

filtered_df = df.copy()
if selected_tense != "All":
    filtered_df = filtered_df[filtered_df["Tense"] == selected_tense]
if selected_person != "All":
    filtered_df = filtered_df[filtered_df["Person"] == selected_person]

# --- Reset index if needed ---
st.session_state.setdefault("index", 0)
st.session_state.setdefault("show_back", False)
if st.session_state["index"] >= len(filtered_df):
    st.session_state["index"] = 0
    st.session_state["show_back"] = False

# --- Navigation ---
col1, flip_col, col2 = st.columns([1, 2, 1])
with col1:
    if st.button("⬅️ Prev") and st.session_state["index"] > 0:
        st.session_state["index"] -= 1
        st.session_state["show_back"] = False
with col2:
    if st.button("Next ➡️") and st.session_state["index"] < len(filtered_df) - 1:
        st.session_state["index"] += 1
        st.session_state["show_back"] = False
with flip_col:
    if st.button("🔄 Flip Card"):
        st.session_state["show_back"] = not st.session_state["show_back"]

# --- Shuffle Again Button ---
if st.button("🔀 Shuffle Again"):
    reshuffle_deck()

# --- Styling ---
st.markdown("""
    <style>
    .card {
        background-color: #fff;
        padding: 2rem;
        text-align: center;
        font-size: 1.4rem;
        border-radius: 12px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        margin-top: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- Card Display ---
if not filtered_df.empty:
    card = filtered_df.iloc[st.session_state["index"]]
    content = card["back"] if st.session_state["show_back"] else card["front"]
    st.markdown(f"<div class='card'>{content}</div>", unsafe_allow_html=True)
else:
    st.warning("No matching cards. Try selecting a different Tense or Person.")