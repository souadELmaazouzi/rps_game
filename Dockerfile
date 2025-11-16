FROM python:3.11-slim

WORKDIR /app

# Copier tout le projet dans l'image
COPY . .

# Installer SPADE + slixmpp compatible + Streamlit
RUN pip install --no-cache-dir \
    "spade==4.0.3" \
    "slixmpp>=1.8.0,<1.10" \
    streamlit

# Par défaut : l'arbitre
CMD ["python", "referee.py"]
