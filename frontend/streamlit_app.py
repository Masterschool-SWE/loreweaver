"""Loreweaver v0 — Streamlit frontend.

A thin client over the FastAPI backend: register/login, create/select a hero, and chat
with the Keeper (a stub in v0). Talks to the backend over HTTP with ``httpx``.
"""
import os

import httpx
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Loreweaver", page_icon="🐉", layout="centered")

ss = st.session_state
ss.setdefault("token", None)
ss.setdefault("username", None)
ss.setdefault("hero", None)
ss.setdefault("messages", [])
# Keeper settings (v1): let players experiment with model + config.
ss.setdefault("model", os.getenv("KEEPER_MODEL", "openai:gpt-4o-mini"))
ss.setdefault("temperature", 0.7)
ss.setdefault("reasoning_effort", "(default)")
ss.setdefault("encounter", None)


def api(method: str, path: str, **kwargs) -> httpx.Response:
    """Call the backend, attaching the bearer token if we have one."""
    headers = kwargs.pop("headers", {})
    if ss.token:
        headers["Authorization"] = f"Bearer {ss.token}"
    timeout = float(os.getenv("BACKEND_TIMEOUT", "180"))
    return httpx.request(method, f"{BACKEND_URL}{path}", headers=headers, timeout=timeout, **kwargs)


def logout():
    ss.token = ss.username = ss.hero = None
    ss.messages = []


# --------------------------------------------------------------------------- #
# Auth view
# --------------------------------------------------------------------------- #
def auth_view():
    st.title("🐉 Loreweaver")
    st.caption("Log in to enter the realm of Aethelgard.")
    tab_login, tab_register = st.tabs(["Log in", "Register"])

    with tab_login:
        u = st.text_input("Username", key="login_u")
        p = st.text_input("Password", type="password", key="login_p")
        st.caption("Demo account → username `demo`, password `demo1234`")
        if st.button("Enter Aethelgard", key="login_btn", type="primary"):
            # OAuth2 password flow expects form-encoded fields named username/password.
            r = api("POST", "/auth/login", data={"username": u, "password": p})
            if r.status_code == 200:
                ss.token = r.json()["access_token"]
                ss.username = u
                st.rerun()
            else:
                st.error("Incorrect username or password.")

    with tab_register:
        u = st.text_input("Choose a username", key="reg_u")
        p = st.text_input("Choose a password", type="password", key="reg_p")
        if st.button("Create account", key="reg_btn"):
            r = api("POST", "/auth/register", json={"username": u, "password": p})
            if r.status_code == 201:
                st.success("Account created — now log in.")
            else:
                st.error(r.json().get("detail", "Could not register."))


# --------------------------------------------------------------------------- #
# Hero picker (sidebar)
# --------------------------------------------------------------------------- #
def hero_sidebar():
    with st.sidebar:
        st.header(f"⚔️ {ss.username}")
        if st.button("Log out"):
            logout()
            st.rerun()

        st.divider()
        heroes = api("GET", "/heroes").json()
        names = {f"{h['name']} (Lv{h['level']} {h['char_class']})": h for h in heroes}

        if names:
            chosen = st.selectbox("Choose your hero", list(names.keys()))
            ss.hero = names[chosen]
        else:
            st.info("No heroes yet. Create one below.")

        with st.expander("➕ Create a new hero"):
            name = st.text_input("Name", key="hero_name")
            char_class = st.selectbox("Class", ["Warrior", "Mage", "Rogue", "Ranger"])
            race = st.selectbox("Race", ["Human", "Elf", "Dwarf", "Orc", "Halfling"])
            backstory = st.text_area("Backstory", key="hero_back")
            if st.button("Forge hero"):
                r = api("POST", "/heroes", json={
                    "name": name, "char_class": char_class, "race": race, "backstory": backstory,
                })
                if r.status_code == 201:
                    ss.messages = []
                    st.rerun()
                else:
                    st.error("Could not create hero.")

        st.divider()
        with st.expander("🎲 Keeper settings"):
            ss.model = st.text_input(
                "Model", value=ss.model,
                help="Anything init_chat_model understands: openai:gpt-4o-mini, "
                     "anthropic:claude-haiku-4-5, ollama:llama3.1, ...",
            )
            ss.temperature = st.slider("Temperature", 0.0, 1.5, ss.temperature, 0.1)
            ss.reasoning_effort = st.selectbox(
                "Reasoning effort", ["(default)", "minimal", "low", "medium", "high"],
                help="Only reasoning models use this; many models reject it.",
            )

        if ss.hero:
            with st.expander("⚔️ Forge an encounter (structured output)"):
                scene = st.text_input("Scene", value="a foggy bog at dusk", key="enc_scene")
                if st.button("Forge"):
                    with st.spinner("The Keeper forges an encounter..."):
                        r = api("POST", "/agent/encounter",
                                json={"hero_id": ss.hero["id"], "scene": scene, "model": ss.model})
                    ss.encounter = r.json() if r.status_code == 200 else {"error": r.json().get("detail")}
                    st.rerun()


# --------------------------------------------------------------------------- #
# Chat view
# --------------------------------------------------------------------------- #
def chat_view():
    hero = ss.hero
    st.title("🐉 Loreweaver")
    if not hero:
        st.info("Create or select a hero in the sidebar to begin.")
        return

    st.caption(f"Adventuring as **{hero['name']}** — Lv{hero['level']} {hero['race']} {hero['char_class']} · "
               f"{hero['hp']} HP · {hero['gold']} gold")

    if ss.encounter:
        enc = ss.encounter
        if "error" in enc:
            st.error(f"Could not forge an encounter: {enc['error']}")
        else:
            with st.container(border=True):
                st.subheader(f"⚔️ {enc['title']}")
                st.write(enc["narrative"])
                st.markdown(
                    f"**Foe:** {enc['monster_name']} (CR {enc['challenge_rating']})  \n"
                    f"**Tactics:** {enc['suggested_tactics']}  \n"
                    f"**Loot:** {', '.join(enc['loot']) or '—'}"
                )
        if st.button("Dismiss encounter"):
            ss.encounter = None
            st.rerun()

    for msg in ss.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Speak to the Keeper..."):
        ss.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("The Keeper considers..."):
                payload = {
                    "hero_id": hero["id"],
                    "message": prompt,
                    "model": ss.model,
                    "temperature": ss.temperature,
                }
                if ss.reasoning_effort != "(default)":
                    payload["reasoning_effort"] = ss.reasoning_effort
                r = api("POST", "/agent/invoke", json=payload)
            if r.status_code == 200:
                reply = r.json()["reply"]
            else:
                detail = r.json().get("detail", "an error occurred")
                reply = f"*(The Keeper is silent — {detail})*"
            st.markdown(reply)
        ss.messages.append({"role": "assistant", "content": reply})


# --------------------------------------------------------------------------- #
if ss.token is None:
    auth_view()
else:
    hero_sidebar()
    chat_view()
