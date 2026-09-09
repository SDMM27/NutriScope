# Installation PostgreSQL

## Docker Desktop
### installation et paramétrage
1. Instalation de l'application windows "Docker Desktop".
2. Lancer docker.desktop
 
### création d'un docker PostgreSQL
#### Créer un fichier de configuration

Dans "Document/", créer un répertoire:

    "Docker_SQL/"

Créer un fichier :

      Docker_SQL\docker-compose.yml

Le remplir :

    version: "3.9"
    
    services:
      postgres:
        image: postgres:17
        container_name: postgres-dev
    
        restart: unless-stopped
    
        environment:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: formation
    
        ports:
          - "5432:5432"
    
        volumes:
          - postgres_data:/var/lib/postgresql/data
    
    volumes:
      postgres_data:


#### Compose
Ouvrir un terminal dans ce répertoire et lancer la commande :
    docker compose up -d

#### Vérification
Dans docket.desktop, vérifier que le docker est créé et lancé

## DBeaver
Installer DBeaver