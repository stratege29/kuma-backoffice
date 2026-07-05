#!/usr/bin/env bash
#
# Migration des secrets du backoffice Kuma (Cloud Run) vers Secret Manager.
# =========================================================================
#
# Deplace les variables d'environnement SENSIBLES, aujourd'hui stockees EN CLAIR
# sur le service Cloud Run, vers Google Secret Manager, puis reconfigure le
# service pour les lire depuis les secrets.
#
#   - FIREBASE_CREDENTIALS_B64  (cle privee du compte de service Firebase)
#   - SMTP_PASSWORD             (mot de passe SMTP)
#
# Caracteristiques :
#   - NE REBUILD PAS l'image (gcloud run services update) -> rapide, pas besoin
#     de Cloud Build / cloudbuild.builds.create.
#   - NE CODE EN DUR AUCUNE valeur : les valeurs courantes sont lues depuis le
#     service en cours et injectees directement dans Secret Manager.
#   - Le code applicatif reste INCHANGE : Cloud Run reinjecte les secrets sous
#     les memes noms de variables d'env (FIREBASE_CREDENTIALS_B64, SMTP_PASSWORD).
#   - Idempotent : relancable sans risque.
#   - Compatible bash 3.2 (le bash par defaut de macOS) : pas de tableau associatif.
#
# Prerequis : un compte authentifie avec, sur le projet kumafire-7864b, les roles
#     roles/run.admin
#     roles/secretmanager.admin
#     roles/iam.serviceAccountUser
#   (typiquement kossea@ultimesgriots.com).  Lance d'abord, SANS commentaire :
#
#     gcloud auth login
#
# Usage :
#     bash migrate_secrets_to_secret_manager.sh
#
set -euo pipefail

PROJECT="kumafire-7864b"
REGION="us-central1"
SERVICE="kuma-backoffice"

# Paires "VARIABLE_ENV=nom-du-secret" (pas de tableau associatif -> bash 3.2 OK)
PAIRS="
FIREBASE_CREDENTIALS_B64=kuma-backoffice-firebase-credentials-b64
SMTP_PASSWORD=kuma-backoffice-smtp-password
"

echo "Projet=$PROJECT  Region=$REGION  Service=$SERVICE"
echo "Compte actif: $(gcloud config get-value account 2>/dev/null || echo '?')"
echo

gcloud services enable secretmanager.googleapis.com --project "$PROJECT"

# --- Service account d'execution du service (defaut = Compute Engine SA) ------
RUNTIME_SA=$(gcloud run services describe "$SERVICE" --region "$REGION" --project "$PROJECT" \
  --format='value(spec.template.spec.serviceAccountName)')
if [ -z "${RUNTIME_SA:-}" ]; then
  PNUM=$(gcloud projects describe "$PROJECT" --format='value(projectNumber)')
  RUNTIME_SA="${PNUM}-compute@developer.gserviceaccount.com"
fi
echo "Service account d'execution: $RUNTIME_SA"
echo

# --- Lecture de la valeur courante d'une variable d'env (jamais affichee) -----
read_env_value() {
  gcloud run services describe "$SERVICE" --region "$REGION" --project "$PROJECT" --format=json \
    | python3 -c "import sys,json
e=json.load(sys.stdin)['spec']['template']['spec']['containers'][0].get('env',[])
print(next((x.get('value','') for x in e if x.get('name')=='$1'), ''))"
}

UPDATE_SECRETS=""
REMOVE_ENV=""

for PAIR in $PAIRS; do
  ENV_VAR="${PAIR%%=*}"
  SECRET_NAME="${PAIR#*=}"
  echo "--- $ENV_VAR  ->  secret '$SECRET_NAME'"

  VALUE="$(read_env_value "$ENV_VAR")"
  if [ -z "$VALUE" ]; then
    echo "    deja absent des variables d'env (probablement deja migre) : pas de nouvelle version."
  else
    if gcloud secrets describe "$SECRET_NAME" --project "$PROJECT" >/dev/null 2>&1; then
      printf '%s' "$VALUE" | gcloud secrets versions add "$SECRET_NAME" --project "$PROJECT" --data-file=- >/dev/null
      echo "    nouvelle version ajoutee."
    else
      printf '%s' "$VALUE" | gcloud secrets create "$SECRET_NAME" --project "$PROJECT" \
        --replication-policy=automatic --data-file=- >/dev/null
      echo "    secret cree."
    fi
    gcloud secrets add-iam-policy-binding "$SECRET_NAME" --project "$PROJECT" \
      --member="serviceAccount:$RUNTIME_SA" --role="roles/secretmanager.secretAccessor" >/dev/null
    echo "    acces en lecture accorde a $RUNTIME_SA."
  fi

  UPDATE_SECRETS="${UPDATE_SECRETS}${ENV_VAR}=${SECRET_NAME}:latest,"
  REMOVE_ENV="${REMOVE_ENV}${ENV_VAR},"
done

UPDATE_SECRETS="${UPDATE_SECRETS%,}"
REMOVE_ENV="${REMOVE_ENV%,}"

echo
echo "Reconfiguration du service (sans rebuild)..."
gcloud run services update "$SERVICE" --region "$REGION" --project "$PROJECT" \
  --update-secrets="$UPDATE_SECRETS" \
  --remove-env-vars="$REMOVE_ENV"

echo
echo "Verification — ces variables doivent etre 'valueFrom: secretKeyRef', plus en clair :"
gcloud run services describe "$SERVICE" --region "$REGION" --project "$PROJECT" \
  --format='yaml(spec.template.spec.containers[0].env)'

echo
echo "Termine. Les futurs deploiements (gcloud run deploy --source) conservent ces mappings de secrets."
