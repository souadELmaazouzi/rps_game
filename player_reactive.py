import asyncio
import spade
from spade.behaviour import CyclicBehaviour
from spade.template import Template


class ReactivePlayer(spade.agent.Agent):

    class PlayBehaviour(CyclicBehaviour):
        async def on_start(self):
            self.moves = ["rock", "paper", "scissors"]
            self.current = "rock"      # premier coup
            self.last_result = "draw"  # "win" / "lose" / "draw" (simplifié ici)

        async def run(self):
            msg = await self.receive(timeout=30)

            if msg:
                round_id = msg.metadata.get("round", "?")

                # Stratégie réactive très simple :
                # si on considère que le coup précédent était "mauvais", on change
                if self.last_result == "lose":
                    idx = self.moves.index(self.current)
                    self.current = self.moves[(idx + 1) % len(self.moves)]
                    self.last_result = "draw"   # reset fictif

                print(f"[{self.agent.jid}] Round {round_id} → (réactif) je joue : {self.current}")

                reply = msg.make_reply()
                reply.body = self.current
                reply.metadata = {"performative": "inform"}
                await self.send(reply)

                # Ici on ne met pas à jour last_result car on n'a pas le vrai résultat
                # (pour le projet, ça suffit comme "réactif" basique)

    async def setup(self):
        print(f"{self.jid} (réactif) démarré.")
        template = Template(metadata={"performative": "request"})
        self.add_behaviour(self.PlayBehaviour(), template)


async def main():
    agent = ReactivePlayer("reactive@xmpp", "reactpass")
    await agent.start()

    while agent.is_alive():
        await asyncio.sleep(1)


if __name__ == "__main__":
    spade.run(main())
