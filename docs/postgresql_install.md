# Installation de PostgreSQL avec Docker

Ce document permet de mettre en place une configuration identique pour le projet : **PostgreSQL exécuté dans Docker et accessible depuis DBeaver**.

## 1. Docker Desktop

### Installation

1. Télécharger et installer **Docker Desktop pour Windows**.
2. Lancer **Docker Desktop**.
3. Vérifier que Docker Desktop est correctement démarré.

---

## 2. Création du conteneur PostgreSQL

### 2.1 Créer le dossier de configuration

Dans le dossier `Documents`, créer un répertoire :

```text
Docker_SQL/
```

Créer ensuite le fichier :

```text
Docker_SQL/docker-compose.yml
```

### 2.2 Configuration de Docker Compose

Ajouter le contenu suivant dans `docker-compose.yml` :

```yaml
services:
  postgres:
    image: postgres:17
    container_name: postgres
    restart: unless-stopped
 
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: postgres
 
    ports:
      - "5432:5432"
 
    volumes:
      - postgres_data:/var/lib/postgresql/data
 
volumes:
  postgres_data:
```

### Explication rapide

* `postgres:17` : utilise l'image officielle PostgreSQL 17.
* `container_name: postgres-dev` : donne au conteneur le nom `postgres-dev`.
* `POSTGRES_USER` : utilisateur PostgreSQL créé au premier démarrage.
* `POSTGRES_PASSWORD` : mot de passe de cet utilisateur.
* `POSTGRES_DB` : base de données créée automatiquement au premier démarrage.
* `5432:5432` : rend PostgreSQL accessible depuis Windows sur le port `5432`.
* `postgres_data` : volume Docker permettant de conserver les données PostgreSQL lors de la recréation du conteneur.

> **Important :** le volume est initialisé uniquement lors de la première création de la base. Modifier ensuite `POSTGRES_USER`, `POSTGRES_PASSWORD` ou `POSTGRES_DB` dans le fichier YAML ne modifie pas une base déjà initialisée.

---

## 3. Démarrer PostgreSQL

Ouvrir un terminal dans le dossier contenant le fichier `docker-compose.yml` :

```text
Documents/Docker_SQL/
```

Puis exécuter :

```bash
docker compose up -d
```

Docker va télécharger l'image PostgreSQL si elle n'est pas déjà présente, puis créer et démarrer le conteneur.

### Vérification

Dans **Docker Desktop**, vérifier que le conteneur :

```text
postgres-dev
```

est présent et possède le statut **Running**.

On peut également vérifier depuis le terminal avec :

```bash
docker ps
```

Le conteneur `postgres-dev` doit apparaître dans la liste.

---

# 4. Installation et configuration de DBeaver

### Installation

Installer **DBeaver Community**.

### Création de la connexion PostgreSQL

Dans DBeaver :

1. Créer une nouvelle connexion.
2. Sélectionner **PostgreSQL**.
3. Utiliser les paramètres suivants :

| Paramètre | Valeur      |
| --------- | ----------- |
| Host      | `localhost` |
| Port      | `5432`      |
| Database  | `formation` |
| Username  | `postgres`  |
| Password  | `postgres`  |

Tester la connexion avec **Test Connection**.

Si la connexion est correctement configurée, DBeaver doit pouvoir accéder à la base PostgreSQL exécutée dans le conteneur Docker.

---

# 5. Résultat attendu

L'environnement doit être organisé de la manière suivante :

```text
Windows
│
├── Docker Desktop
│   │
│   └── Conteneur : postgres-dev
│       │
│       └── PostgreSQL 17
│           └── Base : formation
│
└── DBeaver
    │
    └── Connexion PostgreSQL
        └── localhost:5432
            └── formation
```

Une fois cette configuration terminée, nous disposons tous les deux du même environnement PostgreSQL pour travailler sur NutriScope.
