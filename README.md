# 🎮 TP : Système Multi-Agent Distribué  
## Jeu Pierre – Feuille – Ciseaux (Rock–Paper–Scissors)  
### Docker + XMPP (Prosody) + SPADE + Streamlit

Ce projet implémente un **véritable système multi-agent distribué** basé sur :

- 🧠 **4 agents SPADE** :  
  - `referee` (arbitre)  
  - `proactive`  
  - `sequential`  
  - `reactive`
- 🛰️ **un serveur XMPP Prosody**  
- 🐳 **Docker & Docker Compose**  
- 🖥️ **Interface Streamlit** (UI)

Les agents communiquent exclusivement par **messages XMPP**, sont exécutés dans des **conteneurs indépendants** et orchestrés par un arbitre.

---

