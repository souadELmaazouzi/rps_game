import asyncio
import os
import json

import spade
from spade.behaviour import CyclicBehaviour
from spade.message import Message


MOVES = ["rock", "paper", "scissors"]


def result_pair(m1, m2):
    """
    Compare deux coups et renvoie :
    - 1 si m1 gagne
    - -1 si m1 perd
    - 0 si égalité
    """
    if m1 == m2:
        return 0

    if (m1 == "rock" and m2 == "scissors") \
       or (m1 == "paper" and m2 == "rock") \
       or (m1 == "scissors" and m2 == "paper"):
        return 1

    return -1


class RefereeAgent(spade.agent.Agent):

    class RefereeBehaviour(CyclicBehaviour):
        async def on_start(self):
            # Numéro du round et nombre max de rounds
            self.round = 0
            self.max_rounds = 10

            # JID des joueurs (bare JID, sans /resource)
            self.players = [
                "proactive@xmpp",
                "sequential@xmpp",
                "reactive@xmpp",
            ]

            # Scores initiaux
            self.scores = {p: 0 for p in self.players}

            # Historique pour l'interface
            self.history = []
            self.data_path = os.path.join("data", "game_state.json")

            print("Arbitre : démarré. Scores initiaux :", self.scores)

        def save_state(self, finished: bool):
            """
            Sauvegarde l'état du jeu dans data/game_state.json
            (utile pour une interface Streamlit, par exemple).
            """
            state = {
                "scores": self.scores,
                "history": self.history,
                "finished": finished,
            }
            os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
            with open(self.data_path, "w") as f:
                json.dump(state, f, indent=2)

        async def run(self):
            # Si on a déjà joué tous les rounds : fin de partie
            if self.round >= self.max_rounds:
                print("\n===== PARTIE TERMINÉE =====")
                print("Scores finaux :", self.scores)
                winner = max(self.scores, key=self.scores.get)
                print(f"🏆 Gagnant : {winner} avec {self.scores[winner]} points")

                # Sauvegarder l'état final
                self.save_state(finished=True)

                await self.agent.stop()
                return

            # Nouveau round
            self.round += 1
            print(f"\n=== ROUND {self.round} ===")

            # 1) Envoyer une requête "play" à chaque joueur
            for jid in self.players:
                msg = Message(
                    to=jid,
                    body="play",
                    metadata={
                        "performative": "request",
                        "round": str(self.round),
                    },
                )
                await self.send(msg)

            # 2) Recevoir les réponses
            moves = {}

            for _ in self.players:
                response = await self.receive(timeout=10)

                if response:
                    move = response.body.strip().lower()
                    # Ne garder que le bare JID (avant le /resource)
                    sender_bare = str(response.sender).split("/")[0]

                    # Ne prendre en compte que les joueurs connus
                    if sender_bare in self.players:
                        moves[sender_bare] = move
                        print(f"[Arbitre] {sender_bare} joue {move}")
                    else:
                        print(f"[Arbitre] Message ignoré de {sender_bare}")
                else:
                    print("[Arbitre] Temps dépassé : réponse manquante.")
                    # On arrête ce round si toutes les réponses ne sont pas arrivées
                    return

            # Vérifier qu'on a bien les 3 coups
            if len(moves) < len(self.players):
                print("[Arbitre] Round incomplet, moves reçus :", moves)
                # Sauvegarde quand même l'état courant
                self.history.append(
                    {
                        "round": self.round,
                        "moves": moves,
                        "scores": dict(self.scores),
                    }
                )
                self.save_state(finished=False)
                return

            # 3) Comparer les coups et mettre à jour les scores
            p1, p2, p3 = self.players
            m1, m2, m3 = moves[p1], moves[p2], moves[p3]

            # p1 vs p2
            r12 = result_pair(m1, m2)
            if r12 == 1:
                self.scores[p1] += 1
            elif r12 == -1:
                self.scores[p2] += 1

            # p1 vs p3
            r13 = result_pair(m1, m3)
            if r13 == 1:
                self.scores[p1] += 1
            elif r13 == -1:
                self.scores[p3] += 1

            # p2 vs p3
            r23 = result_pair(m2, m3)
            if r23 == 1:
                self.scores[p2] += 1
            elif r23 == -1:
                self.scores[p3] += 1

            print("Scores après ce round :", self.scores)

            # 4) Mémoriser ce round dans l'historique + sauvegarder
            self.history.append(
                {
                    "round": self.round,
                    "moves": moves,            # ex: {"proactive@xmpp": "rock", ...}
                    "scores": dict(self.scores),
                }
            )
            self.save_state(finished=False)

    async def setup(self):
        print("Arbitre : setup OK")
        behaviour = self.RefereeBehaviour()
        self.add_behaviour(behaviour)


async def main():
    # ⚠️ Le compte referee@xmpp doit exister dans Prosody
    agent = RefereeAgent("referee@xmpp", "refpass")
    await agent.start()
    print("Arbitre lancé.")

    while agent.is_alive():
        await asyncio.sleep(1)


if __name__ == "__main__":
    spade.run(main())
