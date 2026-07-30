FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système (ffmpeg pour la génération audio des contes)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Exposer le port
EXPOSE 8080

# Variables d'environnement
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Démarrer le serveur HTTP Firebase Backoffice
CMD ["python", "firebase_web_backoffice.py"]
