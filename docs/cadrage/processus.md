# Processus — du scan à la décision d'achat

## Objectif

Ce document cartographie, en BPMN simplifié, le parcours « du scan à la décision d'achat » : la carte **as-is** (sans NutriScope, avec les outils réels — étiquette, Yuka, web, ou rien) et la carte **to-be** (avec NutriScope, en couloirs *utilisateur / application / moteur IA / base*). La décision finale a trois issues, pas deux : garder le produit, choisir une alternative, ou ne pas acheter — renoncer à un produit inadapté faute de mieux est un résultat aussi légitime qu'un achat.

Le tableau qui suit l'as-is numérote et qualifie (fréquence, temps perdu, conséquence) ses points de friction ; la dernière section précise les trois activités où l'IA intervient dans le to-be (percevoir, classer, prédire, générer).

## Carte as-is — sans NutriScope

Le même déclencheur (« produit repéré en rayon, doute sur sa qualité ») débouche sur quatre comportements réels observés chez nos personas (TP 5) : lecture d'étiquette, scan Yuka, recherche web, ou aucune vérification. Léa (famille pressée) utilise surtout Yuka en rayon ; Inès (étudiante) et Sophie (diabétique) basculent plus souvent vers la lecture d'étiquette ou le renoncement, faute de réponse adaptée à leur contrainte (budget, pathologie) ; la recherche web intervient rarement en rayon et plutôt après coup, à la maison. Quel que soit le chemin pris, l'utilisatrice finit par une même décision à deux issues : acheter, ou reposer le produit. Le détail de chaque friction (fréquence, temps perdu, conséquence) est dans le tableau qui suit le schéma — la carte elle-même ne porte que leur numéro.

```mermaid
flowchart TD
    subgraph LaneUser["Couloir : Utilisateur"]
        Start(("Produit repéré en rayon,<br/>doute sur sa qualité"))
        Decide{"Que fait-elle ?"}
        ReadLabel["Lire l'étiquette<br/>nutritionnelle"]
        Interpret{"Valeurs et jargon<br/>compréhensibles ?"}
        GiveUp["Renoncer à comprendre,<br/>décider au feeling"]
        NoCheck["Acheter sans vérifier"]
        FinalGw{"Achète-t-elle<br/>le produit ?"}
        EndBuy(("Produit dans<br/>le chariot"))
        EndNoBuy(("Produit reposé,<br/>achat abandonné"))
    end

    subgraph LaneYuka["Couloir : Application tierce (Yuka)"]
        ScanYuka["Scanner avec Yuka"]
        FoundGw{"Produit trouvé<br/>dans Yuka ?"}
        ShowScore["Afficher le score et l'explication<br/>— sans alternative"]
        ScoreGw{"Score jugé<br/>satisfaisant ?"}
        AltMethodGw{"Cherche une alternative<br/>elle-même : où ?"}
    end

    subgraph LaneWeb["Couloir : Web / entourage"]
        WebSearch["Chercher avis,<br/>composition, forums"]
        MultiTab["Comparer plusieurs<br/>sources"]
    end

    Start --> Decide
    Decide -- "étiquette" --> ReadLabel --> Interpret
    Interpret -- "non" --> GiveUp --> FinalGw
    Interpret -- "oui" --> FinalGw

    Decide -- "Yuka" --> ScanYuka --> FoundGw
    FoundGw -- "non" --> ReadLabel
    FoundGw -- "trouvé" --> ShowScore --> ScoreGw
    ScoreGw -- "oui" --> FinalGw
    ScoreGw -- "non" --> AltMethodGw
    AltMethodGw -- "rescanne d'autres<br/>produits du rayon" --> ScanYuka
    AltMethodGw -- "cherche sur le web" --> WebSearch

    Decide -- "web" --> WebSearch --> MultiTab --> FinalGw

    Decide -- "rien" --> NoCheck --> EndBuy

    FinalGw -- "oui" --> EndBuy
    FinalGw -- "non" --> EndNoBuy

    classDef evt fill:#e8f5e9,stroke:#43a047,stroke-width:2px,color:#1b5e20
    classDef act fill:#ffffff,stroke:#1976d2,stroke-width:2px,color:#0d47a1
    classDef gw fill:#fff3e0,stroke:#fb8c00,stroke-width:2px,color:#e65100
    class Start,EndBuy,EndNoBuy evt
    class Decide,FoundGw,FinalGw,Interpret,ScoreGw,AltMethodGw gw
    class ReadLabel,GiveUp,WebSearch,MultiTab,NoCheck,ScanYuka,ShowScore act
    style LaneUser fill:#ffffff,stroke:#cfd8dc,stroke-width:1px
    style LaneYuka fill:#ffffff,stroke:#cfd8dc,stroke-width:1px
    style LaneWeb fill:#ffffff,stroke:#cfd8dc,stroke-width:1px
```

### Tableau des frictions (as-is)

| # | Friction | Type | Fréquence | Temps perdu | Conséquence |
|---|---|---|---|---|---|
| F1 | Produit non reconnu par Yuka (marques distributeur) | Rupture d'information | Occasionnelle, surtout sur les marques distributeur | 30 à 60 s de blocage en rayon avant de basculer vers l'étiquette | Abandon du contrôle nutritionnel, achat « par défaut » |
| F2 | Étiquette trop complexe à interpréter (tableau, jargon, %AJR) | Variabilité | Quasi systématique sans appli, ou en repli après un F1 | 1 à 2 min par produit, enfants qui attendent (Léa) | Décision « au feeling », perte de temps |
| F3 | Recherche web dispersée, rarement faite en rayon | Attente | Rare en magasin ; plus fréquente le soir, après achat (Sophie) | 5 à 15 min, hors du parcours d'achat | Apprentissage a posteriori seulement, risque de reproduire le même achat |
| F4 | Yuka ne propose aucune alternative : score et explication seulement, même si le produit ne convient pas (budget, diabète) | Rupture d'information | Systématique dès que le score est mauvais, plus pénalisant pour les profils à contrainte | 2 à 3 min pour chercher soi-même une alternative, en rescannant d'autres produits du rayon ou sur le web | Comparaison manuelle non systématique, perte de confiance dans l'outil |
| F5 | Aucune vérification faute de temps | Erreur et retour arrière | Fréquente en forte contrainte de temps | 0 en rayon, reporté (regret a posteriori) | Pas d'amélioration du choix dans la durée |

## Carte to-be — avec NutriScope

```mermaid
flowchart TD
    subgraph LaneUser["Couloir : Utilisateur"]
        Start(("Produit repéré<br/>en rayon"))
        Scan["Scanner le code-barres"]
        ReadResult["Lire le score, l'explication<br/>et les substituts"]
        ChooseGw{"Garder, alternative,<br/>ou ne pas acheter ?"}
        LocateAlt["Localiser l'alternative"]
        EndKeep(("Produit initial<br/>dans le chariot"))
        EndAlt(("Produit alternatif<br/>dans le chariot"))
        EndNoBuy(("Produit reposé,<br/>achat abandonné"))
    end

    subgraph LaneApp["Couloir : Application"]
        Search["Chercher le produit"]
        FoundGw{"Trouvé ?"}
        AskPhoto["Demander une photo"]
        NutriScoreGw{"Nutri-Score déjà<br/>renseigné dans la fiche ?"}
        Display["Afficher score,<br/>explication, substituts"]
    end

    subgraph LaneIA["Couloir : Moteur IA"]
        Classify["Percevoir/classer la photo<br/>— classifieur d'images (Keras)"]
        Predict["Prédire le Nutri-Score manquant<br/>— régression sur les nutriments"]
        FindSubs["Classer les produits proches<br/>par catégorie et profil nutritionnel"]
        FilterConstraint["Prédire la pertinence de chaque<br/>substitut selon la contrainte<br/>utilisateur"]
        Generate["Générer l'explication<br/>en langage clair — RAG"]
    end

    subgraph LaneData["Couloir : Base"]
        Base[("Base de données<br/>Open Food Facts (ODbL)<br/>+ images (CC-BY-SA)")]
    end

    Start --> Scan --> Search
    Search -.->|"requête fiche produit"| Base
    Search --> FoundGw
    FoundGw -- "non" --> AskPhoto --> Classify
    Base -.->|"images de référence"| Classify
    Classify --> Predict
    FoundGw -- "oui" --> NutriScoreGw
    Base -.->|"fiche produit, nutriments"| NutriScoreGw
    NutriScoreGw -- "non, à prédire" --> Predict
    NutriScoreGw -- "oui, déjà connu" --> FindSubs
    Predict --> FindSubs
    Base -.->|"catalogue, 6 rayons"| FindSubs
    FindSubs --> FilterConstraint
    Base -.->|"profil utilisateur, si renseigné"| FilterConstraint
    FilterConstraint --> Generate --> Display --> ReadResult
    ReadResult --> ChooseGw
    ChooseGw -- "garder" --> EndKeep
    ChooseGw -- "alternative" --> LocateAlt --> EndAlt
    ChooseGw -- "ne pas acheter" --> EndNoBuy

    classDef evt fill:#e8f5e9,stroke:#43a047,stroke-width:2px,color:#1b5e20
    classDef act fill:#ffffff,stroke:#1976d2,stroke-width:2px,color:#0d47a1
    classDef gw fill:#fff3e0,stroke:#fb8c00,stroke-width:2px,color:#e65100
    classDef ia fill:#e8f5e9,stroke:#43a047,stroke-width:2px,color:#1b5e20
    classDef data fill:#f5f5f5,stroke:#9e9e9e,stroke-width:1.5px,color:#424242
    class Start,EndKeep,EndAlt,EndNoBuy evt
    class ChooseGw,FoundGw,NutriScoreGw gw
    class Scan,Search,AskPhoto,Display,LocateAlt,ReadResult act
    class Classify,Predict,FindSubs,FilterConstraint,Generate ia
    class Base data
    style LaneUser fill:#ffffff,stroke:#cfd8dc,stroke-width:1px
    style LaneApp fill:#ffffff,stroke:#cfd8dc,stroke-width:1px
    style LaneIA fill:#ffffff,stroke:#cfd8dc,stroke-width:1px
    style LaneData fill:#ffffff,stroke:#cfd8dc,stroke-width:1px
```

Le to-be ferme les cinq frictions de l'as-is : F1 et F3 disparaissent derrière une recherche fiable et un contrôle fait désormais en rayon, F2 derrière une explication générée en langage clair, F5 devient possible parce que la vérification est enfin assez rapide pour tenir dans les quelques secondes disponibles. F4 (Yuka n'offre aucune alternative) est traité à la racine : l'application cherche elle-même un substitut, filtré par le profil (budget, diabète) si connu, là où Yuka s'arrête au score. Ne pas acheter devient une issue nommée : un produit reposé faute de bonne alternative est un succès du parcours, pas un échec — une donnée à mesurer au même titre qu'un achat.

## Les trois activités où l'IA intervient

| Activité (to-be) | Ce qu'elle fait | Verbe(s) |
|---|---|---|
| Prédire le Nutri-Score manquant | À partir des nutriments essentiels, quand l'information officielle est absente de la fiche Open Food Facts | **Prédire** |
| Chercher des substituts proches | Regroupe les produits par catégorie/profil nutritionnel, puis évalue leur pertinence selon le produit scanné et la contrainte de l'utilisateur si connue | **Classer** puis **Prédire** |
| Générer l'explication | Rédige, en langage clair, l'explication du score et des substituts affichés | **Générer** |

Une quatrième capacité, la perception d'image (photo envoyée quand le produit est absent de la base), n'intervient qu'en repli — elle alimente la prédiction du score sans faire partie du chemin principal.

## Sources

- Personas (TP 5) : [docs/cadrage/personas.md](personas.md)
- Périmètre fonctionnel et données : [docs/perimetre.md](../perimetre.md)
- Notation et méthode : Module 2.3 — Analyse des processus, étude d'opportunité & de faisabilité (Utopios)
