# Processus — du scan à la décision d'achat

## Objectif

Ce document cartographie, en BPMN simplifié, le parcours « du scan à la décision d'achat » : la carte **as-is** (sans NutriScope, avec les outils réels — étiquette, Yuka, web, ou rien) et la carte **to-be** (avec NutriScope, en couloirs *utilisateur / application / moteur IA / base*). La décision finale a trois issues, pas deux : garder le produit, choisir une alternative, ou ne pas acheter — renoncer à un produit inadapté faute de mieux est un résultat aussi légitime qu'un achat.

Le tableau qui suit l'as-is numérote et qualifie (fréquence, temps perdu, conséquence) ses points de friction ; la dernière section précise les trois activités où l'IA intervient dans le to-be (percevoir, classer, prédire, générer).

## Carte as-is — sans NutriScope

Le même déclencheur (« produit repéré en rayon, doute sur sa qualité ») débouche sur quatre comportements réels observés chez nos personas : Léa (famille pressée) et Thomas (restaurateur) utilisent surtout Yuka en rayon ; Inès (étudiante) et Sophie (diabétique) basculent plus souvent vers la lecture d'étiquette ou le renoncement faute de réponse adaptée à leur contrainte (budget, pathologie) ; la recherche web intervient rarement en rayon et plutôt après coup, à la maison. Quel que soit le chemin pris, l'utilisatrice finit par une même décision à deux issues : acheter, ou reposer le produit. Le détail de chaque friction (fréquence, temps perdu, conséquence) est dans le tableau qui suit le schéma — la carte elle-même ne porte que leur numéro.

```mermaid
flowchart TD
    subgraph LaneUser["Couloir : Utilisateur"]
        Start(("Produit repéré<br/>en rayon"))
        Decide{"Que fait-elle ?"}
        ReadLabel["Lire l'étiquette<br/>— F2"]
        WebSearch["Chercher sur le web<br/>— F3"]
        NoCheck["Acheter sans vérifier<br/>— F6"]
        FinalGw{"Achète-t-elle<br/>le produit ?"}
        EndBuy(("Produit dans<br/>le chariot"))
        EndNoBuy(("Produit reposé,<br/>achat abandonné"))
    end

    subgraph LaneYuka["Couloir : Application tierce (Yuka)"]
        ScanYuka["Scanner avec Yuka"]
        FoundGw{"Produit trouvé ?"}
        ShowScore["Afficher score<br/>et alternative — F4"]
    end

    Start --> Decide
    Decide -- "étiquette" --> ReadLabel --> FinalGw
    Decide -- "Yuka" --> ScanYuka --> FoundGw
    FoundGw -- "non — F1" --> ReadLabel
    FoundGw -- "trouvé" --> ShowScore --> FinalGw
    Decide -- "web" --> WebSearch --> FinalGw
    Decide -- "rien" --> NoCheck --> EndBuy
    FinalGw -- "oui" --> EndBuy
    FinalGw -- "non" --> EndNoBuy

    classDef evt fill:#e8f5e9,stroke:#43a047,stroke-width:2px,color:#1b5e20
    classDef act fill:#ffffff,stroke:#1976d2,stroke-width:2px,color:#0d47a1
    classDef gw fill:#fff3e0,stroke:#fb8c00,stroke-width:2px,color:#e65100
    class Start,EndBuy,EndNoBuy evt
    class Decide,FoundGw,FinalGw gw
    class ReadLabel,WebSearch,NoCheck,ScanYuka,ShowScore act
    style LaneUser fill:#ffffff,stroke:#cfd8dc,stroke-width:1px
    style LaneYuka fill:#ffffff,stroke:#cfd8dc,stroke-width:1px
```

*F5 (Thomas, achats professionnels) n'apparaît pas comme une case du schéma : c'est cette boucle entière qui est rejouée à l'identique, produit par produit, sans vue d'ensemble sur un rayon — une friction sur la répétition, pas sur une étape précise.*

### Tableau des frictions (as-is)

| # | Friction | Type | Fréquence | Temps perdu | Conséquence |
|---|---|---|---|---|---|
| F1 | Produit non reconnu par Yuka (marques distributeur, produits food-service) | Rupture d'information | Fréquente pour Thomas (produits pro peu référencés) ; occasionnelle pour Léa/Inès/Sophie sur les marques de distributeur | 30 à 60 s de blocage en rayon avant de basculer vers l'étiquette | Abandon du contrôle nutritionnel, achat « par défaut » |
| F2 | Étiquette trop complexe à interpréter (tableau, jargon, %AJR) | Variabilité | Quasi systématique sans appli, ou en repli après un F1 | 1 à 2 min par produit, enfants qui attendent (Léa) ou file pro (Thomas) | Décision « au feeling », perte de temps |
| F3 | Recherche web dispersée, rarement faite en rayon | Attente | Rare en magasin ; plus fréquente le soir, après achat (Sophie) | 5 à 15 min, hors du parcours d'achat | Apprentissage a posteriori seulement, risque de reproduire le même achat |
| F4 | Alternative Yuka non pertinente au regard d'une contrainte individuelle (budget, diabète) | Rupture d'information | Systématique pour les profils à contrainte | 2 à 3 min de plus pour revérifier soi-même | Perte de confiance dans l'outil, retour au choix par prix ou marque |
| F5 | Boucle rejouée à l'identique lors d'achats pro (Thomas), sans vue d'ensemble sur un rayon | Décision manuelle répétitive | Dizaines de fois par session chez METRO | Temps cumulé important sur une session | Comparaison abandonnée après quelques produits |
| F6 | Aucune vérification faute de temps | Erreur et retour arrière | Fréquente en forte contrainte de temps | 0 en rayon, reporté (regret a posteriori) | Pas d'amélioration du choix dans la durée |

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
        AskPhoto["Demander une photo<br/>— F1"]
        Display["Afficher score,<br/>explication, substituts"]
    end

    subgraph LaneIA["Couloir : Moteur IA"]
        Classify["Percevoir/classer<br/>la photo"]
        Predict["Prédire le score manquant"]
        FindSubs["Classer et prédire<br/>les substituts — F4"]
        Generate["Générer l'explication<br/>en langage clair — F2"]
    end

    subgraph LaneData["Couloir : Base"]
        Data[("Fiches produit, catalogue,<br/>profil utilisateur")]
    end

    Start --> Scan --> Search
    Search -.-> Data
    Search --> FoundGw
    FoundGw -- "non" --> AskPhoto --> Classify --> Predict
    FoundGw -- "oui" --> Predict
    Predict -.-> Data
    Predict --> FindSubs
    FindSubs -.-> Data
    FindSubs --> Generate --> Display --> ReadResult
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
    class ChooseGw,FoundGw gw
    class Scan,Search,AskPhoto,Display,LocateAlt,ReadResult act
    class Classify,Predict,FindSubs,Generate ia
    class Data data
    style LaneUser fill:#ffffff,stroke:#cfd8dc,stroke-width:1px
    style LaneApp fill:#ffffff,stroke:#cfd8dc,stroke-width:1px
    style LaneIA fill:#ffffff,stroke:#cfd8dc,stroke-width:1px
    style LaneData fill:#ffffff,stroke:#cfd8dc,stroke-width:1px
```

Le to-be ferme F1, F2, F3 (contrôle fait désormais en rayon) et F6 (vérification enfin assez rapide) ; F4 est traité en injectant le profil (budget, diabète) dans la recherche de substituts. Ne pas acheter devient une issue nommée : un produit reposé faute de bonne alternative est un succès du parcours, pas un échec — une donnée à mesurer au même titre qu'un achat. F5 (achats professionnels de Thomas, produit par produit) n'est pas résolu : c'est une limite assumée de ce périmètre.

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
