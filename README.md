# Gawa — Backend (API)

API REST du **système de gestion scolaire Gawa**, pensée pour les écoles des Comores : centrée sur l'enseignant, **offline-first** et résiliente aux connexions instables.

Propulsée par **Django 6 / Django REST Framework** avec authentification **JWT** et un routage **multi-bases de données** (académique + archive immuable).

---

## Stack technique

| Composant        | Technologie                          |
|------------------|--------------------------------------|
| Framework        | Django 6.0                           |
| API              | Django REST Framework 3.16           |
| Authentification | SimpleJWT (tokens access / refresh)  |
| Base de données  | PostgreSQL (pilotes `pg8000` + `psycopg2`) |
| CORS             | `django-cors-headers`                |

---

## Architecture modulaire

Le projet est découpé en *apps* Django qui reflètent les modules métier :

| App         | Rôle                                                                 |
|-------------|----------------------------------------------------------------------|
| `users`     | Gestion des utilisateurs, RBAC, authentification JWT (rôles `ADMIN`, `TEACHER`, `PARENT`…) |
| `sis`       | *Student Information System* : élèves, classes, emplois du temps, présences |
| `pcs`       | *Progressive Course System* : cours, chapitres, ressources, déverrouillage progressif |
| `exam`      | Tests, quiz et évaluations                                           |
| `finance`   | Suivi des paiements et facturation                                   |
| `vault`     | Archivage immuable et chiffré (*Sealed Archive* + journal d'accès)   |
| `gawa_core` | Configuration centrale : settings, routers DB, permissions, audit, tenancy |

### Multi-database routing
Deux bases PostgreSQL sont utilisées :
- **`default`** (`academic_db`) — données opérationnelles courantes.
- **`archive_db`** — archives scellées de l'app `vault`.

Le routage est assuré par `gawa_core.routers.ArchiveRouter`.

### Offline-first
Toutes les entités synchronisables exposent `updated_at` et `deleted_at` (soft delete).
La synchronisation suit la règle **« Last Write Wins with Timestamps »** via un endpoint de batch (`POST /api/v1/sync/push`). Voir [`architecture-backend.md`](../architecture-backend.md) pour le détail.

---

## Démarrage

### Prérequis
- Python 3.13+
- PostgreSQL avec deux bases : `academic_db` et `archive_db`

### Installation

```bash
# 1. Environnement virtuel
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# 2. Dépendances
pip install -r requirements.txt

# 3. Variables d'environnement
copy .env.example .env       # Windows  (cp sous Unix)
#   puis éditer .env avec vos valeurs

# 4. Migrations (les deux bases)
python manage.py migrate
python manage.py migrate --database=archive_db

# 5. Lancer le serveur
python manage.py runserver
```

L'API est disponible sur `http://localhost:8000`.

---

## Configuration (`.env`)

Le fichier `.env` **n'est pas versionné** (voir `.gitignore`). Copiez `.env.example` et adaptez :

| Variable                | Description                                  |
|-------------------------|----------------------------------------------|
| `DJANGO_SECRET_KEY`     | Clé secrète Django (à régénérer en prod)     |
| `DJANGO_DEBUG`          | `True` en dev, `False` en prod               |
| `DJANGO_ALLOWED_HOSTS`  | Hôtes autorisés (séparés par des virgules)   |
| `CORS_ALLOWED_ORIGINS`  | Origines front autorisées                    |
| `JWT_ACCESS_MINUTES` / `JWT_REFRESH_DAYS` | Durée de vie des tokens    |
| `DB_*`                  | Connexion à la base académique               |
| `ARCHIVE_DB_*`          | Connexion à la base d'archive                |

> ⚠️ En production : régénérez `DJANGO_SECRET_KEY`, passez `DJANGO_DEBUG=False` et utilisez un mot de passe DB fort.

---

## Scripts utilitaires (locaux)

Les scripts de seed/debug (`seed_*.py`, `create_dbs.py`, `check_db.py`…) sont **ignorés par git** : ce sont des outils de développement local, pas du code applicatif.

---

## Sécurité

- Authentification JWT sans état (mobile-friendly).
- Permissions par rôle (RBAC) — voir `gawa_core/permissions.py`.
- Journalisation d'audit — voir `gawa_core/audit.py`.
- Archives `vault` scellées et journalisées (accès tracé).

---

## Projet Gawa

Ce backend fait partie de l'écosystème Gawa :
- **Backend** (ce repo) — API Django.
- **Frontend web** — tableau de bord Next.js (admin, enseignant, parent, élève).
- **Landing** — site vitrine Next.js.
