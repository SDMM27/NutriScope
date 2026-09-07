# Carte des parties prenantes — NutriScope

## Objectif

Ce document identifie les parties prenantes du projet NutriScope et les positionne sur une matrice pouvoir/intérêt, afin de définir comment chacune doit être engagée pendant le cadrage puis tout au long du projet. Il sert de base à la note de cadrage (TP8) et à la trame d'entretien avec la direction.

## Méthode : la matrice pouvoir — intérêt

La matrice pouvoir/intérêt (matrice de Mendelow) positionne chaque partie prenante selon deux axes :

- **Pouvoir** : sa capacité à influencer les décisions, le périmètre ou l'avenir du projet.
- **Intérêt** : le niveau d'attention et d'implication qu'elle porte au projet et à ses résultats.

Quatre quadrants en découlent, avec une stratégie d'engagement propre à chacun :

| Quadrant | Pouvoir / Intérêt | Stratégie d'engagement |
|---|---|---|
| À gérer étroitement | Fort / Fort | Impliquer activement, consulter en continu, satisfaire pleinement |
| À satisfaire en permanence | Fort / Faible | Tenir satisfaite sans sur-solliciter, respecter strictement ses contraintes |
| À tenir informées | Faible / Fort | Informer régulièrement, consulter, ne pas négliger ses préoccupations |
| À surveiller | Faible / Faible | Effort de communication minimal, surveillance passive |

**Précision de périmètre.** Le cadre réglementaire (RGPD, AI Act) est une **contrainte** que le projet doit respecter, pas une partie prenante : il n'a ni intérêt propre ni pouvoir d'influence au sens de la matrice, mais s'impose à toutes les parties prenantes listées ci-dessous. Il est traité comme exigence transverse (registre RGPD, analyse de biais, positionnement AI Act, accessibilité RGAA — livrés en même temps que le reste, cf. cahier des TP) et suivi via le DPO.

## Les parties prenantes

### Direction (sponsor du projet)

- **Rôle** : commanditaire du chantier NutriScope, jouée par les formateurs. Confie la totalité du projet à l'équipe (cadrage, base de données, briques d'IA, mise en production) et valide chaque jalon (J1 à J7).
- **Pouvoir** : **Fort** — arbitre le budget et le périmètre, valide ou renvoie en correction chaque livrable, peut réorienter le projet.
- **Intérêt** : **Fort** — a explicitement commandé le projet et en mesure le retour sur investissement.
- **Quadrant : à gérer étroitement.**
- **Attentes principales** : des livrables démontrables à chaque jalon ("on montre ce qui tourne, pas des slides"), un chiffrage crédible (KPI, coûts, ROI), le respect du calendrier.
- **Engagement** : démonstrations courtes à chaque jalon, association aux décisions de périmètre, entretien de cadrage dédié (TP5).

### Équipe data

- **Rôle** : l'équipe projet elle-même — conception, développement et livraison du produit (base de données, modèles, assistant, industrialisation).
- **Pouvoir** : **Fort** — détient les choix techniques structurants (architecture, périmètre de données, modèles) qui conditionnent tout ce que les autres parties prenantes pourront constater.
- **Intérêt** : **Fort** — porte la responsabilité de la livraison, de la soutenance et de la certification.
- **Quadrant : à gérer étroitement.**
- **Attentes principales** : un cadrage clair du besoin pour limiter les retours en arrière, des arbitrages rapides de la direction, un accès stable aux données Open Food Facts.
- **Engagement** : rituels d'équipe réguliers (point de 10 min en début de séance, revue à chaque jalon), documentation continue des décisions (journal.md, ce document).

### Marketing

- **Rôle** : définit le positionnement, la proposition de valeur et le modèle économique (freemium, B2B, marque blanche…) de NutriScope face à la concurrence (Yuka, myLabel, ScanUp…).
- **Pouvoir** : **Moyen à fort** — oriente les priorités fonctionnelles côté mise sur le marché et le discours produit, mais ne tranche pas seul le budget technique (arbitré par la direction).
- **Intérêt** : **Fort** — le succès de son discours commercial dépend directement de ce que le produit sait réellement démontrer.
- **Quadrant : à gérer étroitement**, à la frontière de « à tenir informées » si son pouvoir réel s'avère plus limité en pratique.
- **Attentes principales** : une proposition de valeur différenciante et testable, des fonctionnalités démontrables, un benchmark concurrentiel fiable.
- **Engagement** : association aux ateliers de cadrage (benchmark, proposition de valeur — TP6), validation croisée du discours produit avant toute communication externe.

### Utilisateurs finaux

- **Rôle** : personnes qui scannent un produit en magasin pour connaître sa qualité nutritionnelle et obtenir des alternatives plus saines (ex. : parent pressé en hypermarché, personne diabétique, étudiant à petit budget).
- **Pouvoir** : **Faible** — aucun pouvoir de décision direct sur le projet ; leur influence est indirecte et différée (adoption ou rejet du produit une fois lancé).
- **Intérêt** : **Fort** — enjeu direct sur leur santé, leur budget et leurs choix alimentaires quotidiens.
- **Quadrant : à tenir informées** (et à consulter activement malgré leur faible pouvoir formel, via personas et entretiens).
- **Attentes principales** : fiabilité des scores et des explications, alternatives réellement accessibles (prix, disponibilité en magasin), simplicité d'usage en situation de scan rapide.
- **Engagement** : construction de personas différenciés, entretiens semi-directifs, tests utilisateurs avant et après mise en production.

### Open Food Facts (fournisseur de données)

- **Rôle** : base de données collaborative mondiale de produits alimentaires, matière première unique du projet (fiches produits, exports, images).
- **Pouvoir** : **Fort** — sans Open Food Facts, il n'y a pas de projet ; un changement de licence, de format d'export (CSV/JSONL/Parquet) ou de disponibilité de l'API ou du bucket d'images impacterait directement NutriScope.
- **Intérêt** : **Faible** — association à but non lucratif qui ne dépend pas de NutriScope et n'a probablement pas connaissance de son existence.
- **Quadrant : à satisfaire en permanence.**
- **Attentes principales (implicites, portées par la licence)** : respect des licences ODbL (base) et CC-BY-SA (images), attribution dans chaque livrable, usage raisonnable de l'infrastructure partagée (API, bucket S3).
- **Engagement** : conformité stricte aux licences dès le premier livrable, crédit visible dans l'application et la documentation, veille sur les évolutions du format d'export.

### Délégué à la protection des données (DPO)

- **Rôle** : garant de la conformité RGPD et, plus largement, réglementaire du projet (positionnement AI Act, accessibilité RGAA).
- **Pouvoir** : **Fort** — autorité de blocage sur toute fonctionnalité non conforme (ex. : traitement de données de santé implicites via les habitudes alimentaires), peut suspendre une mise en production.
- **Intérêt** : **Faible à moyen** — se préoccupe de la conformité du traitement, pas du produit en tant que tel ni de sa réussite commerciale.
- **Quadrant : à satisfaire en permanence.**
- **Attentes principales** : registre des traitements à jour, analyse de biais et d'explicabilité des modèles, minimisation des données personnelles collectées, dossier de conformité livré **en même temps que le reste** (et non en fin de projet).
- **Engagement** : point de vigilance conformité à chaque jalon, dossier de conformité (RGPD, AI Act, RGAA, licences) construit en continu plutôt qu'en rattrapage final.

## Positionnement sur la matrice

![Matrice pouvoir–intérêt des parties prenantes NutriScope](parties_prenantes_matrice.svg)

Version texte (repli sans rendu d'image) :

```
                                          INTÉRÊT
                    Faible                                    Fort
          ┌───────────────────────────────┬───────────────────────────────┐
          │   À SATISFAIRE EN PERMANENCE   │      À GÉRER ÉTROITEMENT      │
    Fort  │                                │                               │
          │   • Open Food Facts            │   • Direction                 │
P         │   • DPO                        │   • Équipe data                │
O         │                                │   • Marketing                  │
U         ├───────────────────────────────┼───────────────────────────────┤
V         │        À SURVEILLER            │      À TENIR INFORMÉES        │
O  Faible │                                │                               │
I         │   (aucune partie prenante      │   • Utilisateurs finaux        │
R         │   identifiée à ce stade)       │                               │
          └───────────────────────────────┴───────────────────────────────┘
```

## Synthèse et points de vigilance

- Les deux parties prenantes à **pouvoir fort et intérêt faible** (Open Food Facts, DPO) sont les plus risquées à négliger : leur faible intérêt apparent ne réduit pas leur capacité à bloquer ou remettre en cause le projet (rupture de licence côté OFF, blocage de mise en production côté DPO). Elles doivent être satisfaites *en continu*, pas seulement consultées en fin de projet.
- Le quadrant « à surveiller » (faible pouvoir, faible intérêt) est vide à ce stade : c'est cohérent pour un projet encore restreint à une équipe et un sponsor unique ; il pourra se peupler plus tard (fournisseurs annexes, régulateurs sectoriels non couverts par le RGPD/l'AI Act, partenaires distribution…).
- Le cadre réglementaire (RGPD, AI Act) reste une **contrainte transverse**, pas une case de la matrice : il façonne les attentes de la direction, du DPO et, indirectement, des utilisateurs finaux, mais n'a pas d'intérêt propre à arbitrer.

## Prochaines étapes

- Personas utilisateurs détaillés à partir des trois profils identifiés (parent pressé, personne diabétique, étudiant à petit budget).
- Trame d'entretien semi-directif pour valider ces hypothèses avec la direction.
- Mise à jour de cette carte après l'entretien réel avec la direction (ce qui est confirmé, infirmé, découvert).
