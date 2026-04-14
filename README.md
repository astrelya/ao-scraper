# AO Scraper - Veille Appels d'Offres Marchés Publics

Application de veille automatisée sur les appels d'offres des marchés publics français.

## Architecture

```
AOScraper/
├── backend/              # API FastAPI (Python)
│   ├── app/
│   │   ├── connectors/   # Connecteurs API (BOAMP, DECP)
│   │   ├── config.py     # Configuration
│   │   ├── database.py   # Connexion SQLite async
│   │   ├── main.py       # Point d'entrée FastAPI
│   │   ├── matcher.py    # Moteur de matching par mots-clés
│   │   ├── models.py     # Modèles SQLAlchemy
│   │   ├── routes.py     # Routes API REST
│   │   ├── schemas.py    # Schémas Pydantic
│   │   └── services.py   # Couche service (CRUD + logique métier)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/             # Interface React + Vite
│   ├── src/
│   │   ├── App.jsx       # Composant principal
│   │   ├── api.js        # Client API
│   │   ├── index.css     # Styles
│   │   └── main.jsx      # Point d'entrée
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
└── README.md
```

## Sources de données

| Source | Description | API |
|--------|------------|-----|
| **BOAMP** | Bulletin Officiel des Annonces de Marchés Publics | OpenDataSoft (DILA) |
| **DECP** | Données Essentielles de la Commande Publique | data.economie.gouv.fr |

## Fonctionnalités

- **Mots-clés** : Définir des mots-clés par catégorie (tech, domaine, compétence) pour filtrer les AOs pertinents
- **Recherche automatisée** : Interrogation des APIs BOAMP et DECP avec vos mots-clés
- **Matching intelligent** : Score de pertinence basé sur la fréquence et la position des mots-clés
- **Favoris & lecture** : Marquer les AOs intéressants et suivre ceux déjà consultés
- **Filtres avancés** : Par source, par statut (favoris, non lus), recherche textuelle
- **Dashboard** : Statistiques en temps réel

---

## Déploiement local - Étape par étape

### Prérequis

- **Python 3.11+** : `python3 --version`
- **Node.js 18+** : `node --version`
- **npm** : `npm --version`
- (Optionnel) **Docker & Docker Compose** pour le déploiement conteneurisé

---

### Option A : Déploiement sans Docker (recommandé pour le développement)

#### 1. Cloner/ouvrir le projet

```bash
cd /chemin/vers/AOScraper
```

#### 2. Configurer le backend

```bash
# Créer un environnement virtuel Python
cd backend
python3 -m venv venv
source venv/bin/activate    # macOS/Linux

# Installer les dépendances
pip install -r requirements.txt

# Copier la config
cp .env.example .env
```

#### 3. Lancer le backend

```bash
# Depuis le dossier backend/, avec le venv activé
uvicorn app.main:app --reload --port 8000
```

Le backend sera accessible sur **http://localhost:8000**
- Documentation API Swagger : **http://localhost:8000/docs**
- Documentation ReDoc : **http://localhost:8000/redoc**

#### 4. Configurer le frontend

```bash
# Dans un nouveau terminal
cd frontend
npm install
```

#### 5. Lancer le frontend

```bash
npm run dev
```

Le frontend sera accessible sur **http://localhost:5173**

---

### Option B : Déploiement avec Docker Compose

```bash
# Depuis la racine du projet
docker compose up --build
```

- Frontend : **http://localhost:3000**
- Backend API : **http://localhost:8000**

Pour arrêter :
```bash
docker compose down
```

---

## Utilisation

### 1. Ajouter des mots-clés

Dans la barre latérale gauche, ajoutez les mots-clés correspondant à votre activité ESN :

**Exemples de mots-clés pertinents :**
- **Tech** : `DevOps`, `Cloud`, `Java`, `Python`, `Cybersécurité`, `Infrastructure`, `Kubernetes`, `Microservices`
- **Domaine** : `SI`, `Transformation digitale`, `Dématérialisation`, `GED`, `ERP`, `CRM`
- **Compétence** : `TMA`, `Intégration`, `Développement`, `Migration`, `Architecture`, `Audit`

### 2. Lancer une recherche

Cliquez sur **"Lancer la recherche"** après avoir sélectionné les sources (BOAMP, DECP). L'application va :
1. Interroger les APIs sélectionnées avec vos mots-clés
2. Normaliser les résultats
3. Évaluer la pertinence de chaque AO par rapport à vos mots-clés
4. Stocker les nouveaux résultats en base

### 3. Consulter les résultats

- **Cliquer** sur un AO pour voir le détail complet
- **⭐ Favori** pour marquer un AO intéressant
- **Filtrer** par source, favoris, non lus, ou recherche textuelle
- **Lien externe** pour accéder à l'annonce sur le site source

---

## API REST

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/keywords` | Liste des mots-clés |
| `POST` | `/api/keywords` | Ajouter un mot-clé |
| `DELETE` | `/api/keywords/{id}` | Supprimer un mot-clé |
| `PATCH` | `/api/keywords/{id}/toggle` | Activer/désactiver un mot-clé |
| `GET` | `/api/aos` | Liste des AOs (paginée, filtrable) |
| `GET` | `/api/aos/{id}` | Détail d'un AO |
| `PATCH` | `/api/aos/{id}/favorite` | Mettre en favori |
| `PATCH` | `/api/aos/{id}/read` | Marquer comme lu |
| `POST` | `/api/fetch` | Lancer une récupération |
| `GET` | `/api/stats` | Statistiques dashboard |

---

## Stack technique

- **Backend** : Python 3.12, FastAPI, SQLAlchemy (async), SQLite, httpx
- **Frontend** : React 18, Vite 5, CSS pur (pas de framework UI)
- **Conteneurisation** : Docker, Docker Compose, Nginx
