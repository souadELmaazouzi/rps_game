import os
import json
import random

import streamlit as st

# ------------------------
# CONFIG GLOBALE
# ------------------------
st.set_page_config(
    page_title="Jeu Pierre–Feuille–Ciseaux – Système multi-agent",
    layout="centered",
)

DATA_PATH = os.path.join("data", "game_state.json")

st.title("🎮 Pierre – Feuille – Ciseaux")
st.write(
    "Système **multi-agent distribué** avec 3 joueurs (proactif, séquentiel, réactif) "
    "et un arbitre sur XMPP + Docker. "
    "Tu peux soit observer les agents automatiques, soit jouer toi-même contre eux."
)

tab_auto, tab_interactif = st.tabs(
    ["🤖 Mode auto (agents SPADE)", "🧑‍💻 Mode interactif (toi vs agents)"]
)


# =========================================================
# UTILITAIRES COMMUNS
# =========================================================
def result_pair(m1, m2):
    """Compare deux coups et renvoie 1 si m1 gagne, -1 si m1 perd, 0 si égalité."""
    if m1 == m2:
        return 0
    if (m1 == "rock" and m2 == "scissors") or \
       (m1 == "paper" and m2 == "rock") or \
       (m1 == "scissors" and m2 == "paper"):
        return 1
    return -1


MOVE_LABELS = {
    "rock": "✊ Pierre",
    "paper": "✋ Feuille",
    "scissors": "✌️ Ciseaux",
}


# =========================================================
# 1) MODE AUTO : LECTURE DE data/game_state.json
# =========================================================
with tab_auto:
    st.subheader("🤖 Agents SPADE (arbitre + 3 joueurs)")

    st.caption(
        "Dans ce mode, l'arbitre tourne dans Docker, communique en XMPP avec les 3 agents "
        "et enregistre l'état du jeu dans `data/game_state.json`."
    )
# petit auto-refresh toutes les X secondes (optionnel)
    refresh_rate = st.slider("Fréquence de rafraîchissement (secondes)", 1, 10, 3)


    # On fait un petit refresh manuel via bouton plutôt que boucle infinie
    if st.button("🔄 Rafraîchir l'état du jeu (agents)"):
        pass  # le simple clic force un rerun

    if not os.path.exists(DATA_PATH):
        st.info(
            "Aucun fichier `data/game_state.json` trouvé.\n\n"
            "➡️ Lance le système avec : `docker compose up` pour générer une partie."
        )
    else:
        try:
            with open(DATA_PATH, "r") as f:
                state = json.load(f)
        except Exception as e:
            st.error(f"Erreur en lisant `game_state.json` : {e}")
            state = None

        if state:
            scores = state.get("scores", {})
            history = state.get("history", [])
            finished = state.get("finished", False)

            st.markdown("### 📊 Scores actuels des agents")
            if scores:
                st.table(
                    [
                        {"Agent": jid, "Score": score}
                        for jid, score in scores.items()
                    ]
                )
            else:
                st.write("Aucun score enregistré pour le moment.")

            st.markdown("### 📜 Historique des rounds")
            if history:
                rows = []
                for h in history:
                    moves = h.get("moves", {})
                    rows.append(
                        {
                            "Round": h.get("round", "?"),
                            "Proactif": MOVE_LABELS.get(moves.get("proactive@xmpp"), moves.get("proactive@xmpp")),
                            "Séquentiel": MOVE_LABELS.get(moves.get("sequential@xmpp"), moves.get("sequential@xmpp")),
                            "Réactif": MOVE_LABELS.get(moves.get("reactive@xmpp"), moves.get("reactive@xmpp")),
                            "Scores": h.get("scores", {}),
                        }
                    )
                st.dataframe(rows)
            else:
                st.write("Pas encore de rounds joués.")

            if finished:
                st.success("✅ Partie terminée (côté agents). Relance `docker compose up` pour rejouer.")
            else:
                st.warning("🕒 Partie en cours (ou en cours de génération côté arbitre).")


# =========================================================
# 2) MODE INTERACTIF : TOI VS 3 AGENTS SIMULÉS
# =========================================================
with tab_interactif:
    st.subheader("🧑‍💻 Tu joues contre 3 agents (simulation locale)")

    st.caption(
        "Dans ce mode, tu joues toi-même : tu choisis ton coup, et les trois stratégies "
        "sont simulées localement (proactif, séquentiel, réactif), pour une démo plus 'réelle'. "
        "Ce mode est indépendant de l'arbitre SPADE, mais illustre le comportement des stratégies."
    )

    # Initialisation des états en session
    if "round_user" not in st.session_state:
        st.session_state.round_user = 0
        st.session_state.scores_user = {
            "Toi (Humain)": 0,
            "Proactif": 0,
            "Séquentiel": 0,
            "Réactif": 0,
        }
        st.session_state.seq_index = 0
        st.session_state.reactive_move = "rock"
        st.session_state.reactive_last_result = "draw"
        st.session_state.history_user = []

    # Sélection du coup utilisateur
    st.markdown("### 🎯 Choisis ton coup")
    user_choice_label = st.radio(
        "Ton coup :",
        ["✊ Pierre", "✋ Feuille", "✌️ Ciseaux"],
        horizontal=True,
    )

    label_to_move = {
        "✊ Pierre": "rock",
        "✋ Feuille": "paper",
        "✌️ Ciseaux": "scissors",
    }
    user_move = label_to_move[user_choice_label]

    # Bouton pour jouer un round
    if st.button("▶️ Jouer un round"):
        st.session_state.round_user += 1
        r = st.session_state.round_user

        # Proactif : aléatoire
        pro_move = random.choice(["rock", "paper", "scissors"])

        # Séquentiel : rock -> paper -> scissors -> ...
        seq_moves = ["rock", "paper", "scissors"]
        seq_move = seq_moves[st.session_state.seq_index % len(seq_moves)]
        st.session_state.seq_index += 1

        # Réactif : change si dernier résultat = lose
        if st.session_state.reactive_last_result == "lose":
            idx = seq_moves.index(st.session_state.reactive_move)
            st.session_state.reactive_move = seq_moves[(idx + 1) % len(seq_moves)]
        re_move = st.session_state.reactive_move

        # Calcul résultats vs chaque agent
        # Tu joues contre chacun, et on attribue 1 point au gagnant du duel
        # (Tu peux adapter si tu veux un autre scoring)
        for agent_name, agent_move in [
            ("Proactif", pro_move),
            ("Séquentiel", seq_move),
            ("Réactif", re_move),
        ]:
            res = result_pair(user_move, agent_move)
            if res == 1:
                st.session_state.scores_user["Toi (Humain)"] += 1
            elif res == -1:
                st.session_state.scores_user[agent_name] += 1

            # pour la stratégie réactive, on met à jour last_result vs toi
            if agent_name == "Réactif":
                if res == 1:   # tu gagnes → agent a perdu
                    st.session_state.reactive_last_result = "lose"
                elif res == -1:
                    st.session_state.reactive_last_result = "win"
                else:
                    st.session_state.reactive_last_result = "draw"

        # Enregistrer l'historique
        st.session_state.history_user.append(
            {
                "round": r,
                "human": user_move,
                "proactif": pro_move,
                "sequentiel": seq_move,
                "reactif": re_move,
                "scores": dict(st.session_state.scores_user),
            }
        )

        st.success(f"Round {r} joué !")

    # Affichage des scores
    st.markdown("### 📊 Scores (mode interactif)")
    st.table(
        [
            {"Participant": name, "Score": score}
            for name, score in st.session_state.scores_user.items()
        ]
    )

    # Historique détaillé
    st.markdown("### 📜 Historique des rounds (mode interactif)")
    if st.session_state.history_user:
        rows = []
        for h in st.session_state.history_user:
            rows.append(
                {
                    "Round": h["round"],
                    "Toi (Humain)": MOVE_LABELS.get(h["human"], h["human"]),
                    "Proactif": MOVE_LABELS.get(h["proactif"], h["proactif"]),
                    "Séquentiel": MOVE_LABELS.get(h["sequentiel"], h["sequentiel"]),
                    "Réactif": MOVE_LABELS.get(h["reactif"], h["reactif"]),
                }
            )
        st.dataframe(rows)
    else:
        st.write("Aucun round interactif joué pour le moment.")

    # Bouton reset
    if st.button("🧹 Réinitialiser le mode interactif"):
        st.session_state.round_user = 0
        st.session_state.scores_user = {
            "Toi (Humain)": 0,
            "Proactif": 0,
            "Séquentiel": 0,
            "Réactif": 0,
        }
        st.session_state.seq_index = 0
        st.session_state.reactive_move = "rock"
        st.session_state.reactive_last_result = "draw"
        st.session_state.history_user = []
        st.info("Mode interactif réinitialisé.")
