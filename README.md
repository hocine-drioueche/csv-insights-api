# CSV Insights API

API FastAPI qui permet à un utilisateur authentifié de **déposer un fichier CSV**, de le faire **analyser en arrière-plan** avec pandas, puis de **consulter le résultat** (statut, colonnes, statistiques) via des endpoints dédiés.

Projet d'apprentissage FastAPI : upload de fichiers (`UploadFile`), tâches de fond (`BackgroundTasks`), SQLAlchemy, authentification Bearer.

## Fonctionnalités

- Authentification par token Bearer
- Upload d'un fichier CSV (`multipart/form-data`) avec création d'une analyse au statut `pending`
- Traitement asynchrone : la réponse HTTP est immédiate, l'analyse se fait après
- Suivi du statut : `pending` → `running` → `completed` ou `failed`
- Résultat détaillé : nombre de lignes et de colonnes, liste des colonnes, type de chaque colonne, `describe()` pour les colonnes numériques
- Suppression réservée au propriétaire de l'analyse
- Statistiques globales sur l'ensemble des analyses

## Stack

| Brique | Rôle |
|---|---|
| FastAPI | Framework web, doc Swagger automatique |
| Uvicorn | Serveur ASGI |
| SQLAlchemy + SQLite | ORM et base de données |
| Pydantic | Validation et schémas de réponse |
| pandas | Analyse du CSV |
| python-multipart | Réception des fichiers |

## Architecture

```
csv-insights-api/
├── requirements.txt
├── samples/                 # CSV d'exemple pour les tests
└── app/
    ├── main.py              # création de l'app, tables, données de départ, routers
    ├── database.py          # engine, SessionLocal, Base
    ├── models.py            # UserDB, AnalysisDB, AnalysisStatus
    ├── schemas.py           # schémas Pydantic (liste, détail, stats...)
    ├── dependencies.py      # session DB, tokens, utilisateur courant
    ├── processing.py        # traitement de fond (pandas), isolé des routes
    └── routers/
        ├── auth.py          # POST /login
        ├── users.py         # GET /users
        └── analyses.py      # upload, liste, détail, suppression, stats
```

## Cycle de vie d'une analyse

```
POST /analyses/upload ──▶ pending ──▶ running ──▶ completed
        (202)                                └──▶ failed
```

- `finished_at` est renseigné à la fin, en succès comme en échec.
- `error_message` n'est renseigné qu'en cas d'échec.

## Endpoints

| Méthode | Route | Auth | Description | Codes |
|---|---|---|---|---|
| POST | `/login` | non | Obtenir un token (`{"username": "alice"}`) | 200, 401 |
| GET | `/users` | oui | Liste des utilisateurs | 200 |
| POST | `/analyses/upload` | oui | Dépose un CSV, crée l'analyse | 202, 400 (fichier vide), 415 (pas un CSV) |
| GET | `/analyses` | oui | Liste courte : `id`, `file_name`, `status`, `created_at` | 200 |
| GET | `/analyses/stats/summary` | oui | `total_files`, `total_rows_processed` | 200 |
| GET | `/analyses/{id}` | oui | Détail complet | 200, 404 |
| DELETE | `/analyses/{id}` | oui | Suppression, propriétaire uniquement | 204, 403, 404 |

Utilisateurs créés au premier démarrage : `alice` et `bob`.

## Installation et lancement

```bash
git clone https://github.com/<ton-user>/csv-insights-api.git
cd csv-insights-api

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload
```

Documentation interactive : http://127.0.0.1:8000/docs

## Exemple d'utilisation (curl)

```bash
# 1. Obtenir un token
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice"}' \
  | python -c 'import sys, json; print(json.load(sys.stdin)["access_token"])')

# 2. Déposer un CSV
curl -X POST http://127.0.0.1:8000/analyses/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@samples/clients.csv"

# 3. Lister les analyses
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8000/analyses

# 4. Détail d'une analyse
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8000/analyses/1

# 5. Statistiques globales
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8000/analyses/stats/summary

# 6. Supprimer (propriétaire uniquement)
curl -X DELETE -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8000/analyses/1
```

### Exemple de détail d'analyse

```json
{
  "id": 2,
  "file_name": "clients.csv",
  "status": "completed",
  "created_at": "2026-11-19T17:30:00",
  "file_size": 62,
  "rows_count": 3,
  "columns_count": 4,
  "columns": ["id", "name", "age", "city"],
  "stats_summary": {
    "id": {
      "type": "int64",
      "describe": {"count": 3.0, "mean": 2.0, "std": 1.0, "min": 1.0,
                   "25%": 1.5, "50%": 2.0, "75%": 2.5, "max": 3.0}
    },
    "name": {"type": "object"}
  },
  "finished_at": "2026-11-19T17:30:00",
  "error_message": null,
  "owner_id": 1
}
```

## Choix de conception

- **Traitement de fond** : `BackgroundTasks` avec une fonction synchrone, exécutée dans un thread pour ne pas bloquer le serveur pendant le calcul pandas.
- **Session dédiée** : la tâche de fond ouvre sa propre session de base de données, car celle de la requête est fermée une fois la réponse envoyée.
- **Données passées à la tâche** : l'identifiant de l'analyse et le contenu du fichier (octets), jamais un objet ORM ou `UploadFile`.
- **Validation du CSV** : contrôle de l'extension à l'upload, la vraie validation étant faite par pandas. Un fichier illisible passe en `failed` avec un message d'erreur.
- **Deux schémas de lecture** : `AnalysisListItem` (vue courte) et `AnalysisDetail` (vue complète).
- **Propriétaire** : `owner_id` vient du token, jamais du client.
- **Lecture ouverte, suppression restreinte** : tout utilisateur connecté voit toutes les analyses, seul le propriétaire peut supprimer.
- **Statistiques** : agrégats calculés en SQL (`COUNT`, `SUM` avec `COALESCE`).
- **JSON** : les `NaN` et types numpy issus de `describe()` sont convertis en valeurs JSON valides.

## Limites connues

- Authentification pédagogique : pas de mot de passe, tokens stockés en mémoire (perdus au redémarrage, sans expiration).
- Le contenu du fichier est gardé en mémoire pendant le traitement : adapté à des fichiers de taille raisonnable.
- Pas de migrations : si les modèles changent, supprimer `csv_insights.db` et relancer.
- Supprimer une analyse en cours de traitement provoque une erreur dans la tâche de fond (la suppression fonctionne).
- Pas de tests automatisés.

## Pistes d'amélioration

- Mots de passe hachés et JWT avec expiration
- Tests `pytest` avec `TestClient`
- Migrations avec Alembic
- Stockage des fichiers sur disque ou sur un stockage objet pour les gros volumes
- File de tâches dédiée (Celery, RQ) pour fiabiliser le traitement
- Pagination et filtres sur `GET /analyses`
- Statistiques enrichies (nombre d'analyses par statut)
