import asyncio
import spade
from spade.behaviour import CyclicBehaviour
from spade.template import Template


class SequentialPlayer(spade.agent.Agent):

    class PlayBehaviour(CyclicBehaviour):
        async def on_start(self):
            self.seq = ["rock", "paper", "scissors"]
            self.index = 0

        async def run(self):
            msg = await self.receive(timeout=30)

            if msg:
                round_id = msg.metadata.get("round", "?")
                move = self.seq[self.index % len(self.seq)]
                self.index += 1

                print(f"[{self.agent.jid}] Round {round_id} → (séquentiel) je joue : {move}")

                reply = msg.make_reply()
                reply.body = move
                reply.metadata = {"performative": "inform"}
                await self.send(reply)

    async def setup(self):
        print(f"{self.jid} (séquentiel) démarré.")
        template = Template(metadata={"performative": "request"})
        self.add_behaviour(self.PlayBehaviour(), template)


async def main():
    agent = SequentialPlayer("sequential@xmpp", "seqpass")
    await agent.start()

    while agent.is_alive():
        await asyncio.sleep(1)


if __name__ == "__main__":
    spade.run(main())
