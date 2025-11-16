import asyncio
import random
import spade
from spade.behaviour import CyclicBehaviour
from spade.template import Template


class ProactivePlayer(spade.agent.Agent):

    class PlayBehaviour(CyclicBehaviour):
        async def run(self):
            # Attendre une requête "play" de l'arbitre
            msg = await self.receive(timeout=30)

            if msg:
                round_id = msg.metadata.get("round", "?")
                move = random.choice(["rock", "paper", "scissors"])

                print(f"[{self.agent.jid}] Round {round_id} → (proactif) je joue : {move}")

                reply = msg.make_reply()
                reply.body = move
                reply.metadata = {"performative": "inform"}
                await self.send(reply)

    async def setup(self):
        print(f"{self.jid} (proactif) démarré.")
        template = Template(metadata={"performative": "request"})
        self.add_behaviour(self.PlayBehaviour(), template)


async def main():
    agent = ProactivePlayer("proactive@xmpp", "proapass")
    await agent.start()

    while agent.is_alive():
        await asyncio.sleep(1)


if __name__ == "__main__":
    spade.run(main())
