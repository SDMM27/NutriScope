# Benchmark de l'existant — NutriScope

> TP 6 — Opportunité & concurrence (points 1 et 2 : benchmark + matrice comparative, 2 pages max pour tout le TP6). Restent à ajouter : SWOT (point 3), proposition de valeur (point 4).

9 acteurs du scan de produits en grande distribution, proches du périmètre de NutriScope (scan en magasin, score, alternatives) : Yuka, Open Food Facts, myLabel, ScanUp, QuelProduit (UFC-Que Choisir), BiteWatch, YaQuoiDedans, BuyOrNot, Kwalito.

| Acteur | Fonctionnalités | Modèle économique | Points faibles visibles |
|---|---|---|---|
| **Yuka** | Scan → score /100 (60 % nutrition, 30 % additifs, 10 % bio), alimentaire + cosmétique, recommandations de produits mieux notés dans une section dédiée de la fiche produit. 6 M produits, ~80 M utilisateurs. | Freemium à prix libre : gratuit complet ; Premium (≈10–50 €/an, don libre) pour recherche texte, hors-ligne, alertes régime. Pas de vente de données. | Pondération 60/30/10 non validée scientifiquement (critiquée par S. Hercberg, créateur du Nutri-Score). Cosmétique évalué hors dosage/contexte (FEBEA). Score global sans détail (sucres, transformation) ni prise en compte du budget. Inutile sur vrac/frais/fait-maison. **Alternative moins immédiate qu'il n'y paraît** : non affichée sur l'écran de scan, il faut ouvrir la fiche produit puis la section recommandations ; et Yuka le dit elle-même dans sa doc officielle, elle n'apparaît que pour les produits mal notés *et* seulement quand l'équipe a identifié une meilleure option — donc absente sur une partie des produits mal notés. |
| **Open Food Facts** | Scan continu → Nutri-Score + NOVA en temps réel, comparaison de produits, listes/inventaire, hors-ligne (iOS). Base ouverte réutilisée par 150+ apps, dont Yuka à l'origine. | Association loi 1901, base et code open source. Financement par subventions publiques et dons ; aucune monétisation des données. | Qualité des fiches hétérogène (contributions bénévoles, champs manquants) — visible sur notre propre extrait (`donnees.md`). Ergonomie perfectible, asymétrie iOS/Android. N'informe pas vers une alternative : pas d'accompagnement à la décision. |
| **myLabel** | Score personnalisable sur 3 piliers (planète, santé, société), verdict simple (smiley), alternative suggérée, achat en ligne chez partenaires (Monoprix, Carrefour...). | Revente de données de consommation anonymisées aux marques/distributeurs ; scoring co-construit avec des tiers (Greenpeace, Open Food Facts). | Modèle en tension avec la promesse d'indépendance (vit de la donnée sur les utilisateurs qu'elle est censée émanciper). Couverture dépendante des partenariats data. Paramétrage à 3 piliers plus riche mais plus lent pour un usage "rapide en rayon". |
| **ScanUp** | Triple lecture Nutri-Score / NOVA / Eco-Score + additifs/labels, liste de courses, volet "co-construction" (vote sur cahier des charges de nouveaux produits). 450 000+ produits. | Gratuit, sans pub pour le consommateur ; financé en B2B (études de reformulation vendues aux marques, bornes de scan en magasin). | Même tension d'indépendance que myLabel (financée par les marques évaluées). Positionnement hybride jugé confus par les cofondateurs eux-mêmes. Peu de signaux publics récents depuis son lancement (2018). |
| **QuelProduit** (UFC-Que Choisir) | Une appli pour 3 univers : alimentaire (~190 000), cosmétique (~240 000), entretien (~13 000) — angle mort chez la plupart des concurrents. Détail cliquable de la méthode par catégorie. | Développée par l'association UFC-Que Choisir, financée par dons/adhésions. Après connexion, tout est gratuit (pas de palier premium). | Notation jugée plus sévère que Yuka sur un même produit (écarts rapportés par la presse). Dépend des données fabricants + contributions validées manuellement (croissance plus lente qu'un crowdsourcing pur). Compte obligatoire pour débloquer l'usage complet. |
| **BiteWatch** | Scan → visualisation du sucre en cuillères (repère OMS), sel, graisses saturées, additifs classés par risque (vert/orange/rouge), compatibilité régime (végé/végan), score NOVA. 4 M+ produits. Lancée fin 2025. | Portée par SAFE (Safe Food Advocacy Europe), organisation indépendante ; gratuite, revendique une indépendance totale vis-à-vis des marques. | Base encore jeune ("4 M de produits *pour le moment*"), rythme de mise à jour et couverture hors Europe de l'Ouest non documentés. Trop récente pour un historique d'avis utilisateurs. |
| **YaQuoiDedans** | Scan → composition, détection de substances controversées (aspartame...), additifs, allergènes. Alimentée par Open Food Facts, ~300 000 produits. | Développée et financée par Système U (distributeur), gratuite ; ambition de la proposer à d'autres enseignes. | Conflit d'intérêts structurel : un distributeur note (implicitement) les produits qu'il vend. Pas de note ni d'alternative suggérée, seulement descriptif. Couverture initialement limitée aux produits vendus chez U. |
| **BuyOrNot** | Scan → volet nutrition/NOVA (données Open Food Facts) + volet éthique (comportement social, environnemental, financier de l'entreprise) et mécanisme de boycott collectif avec droit de réponse de la marque. | Association loi 1901 (I-boycott.org), à but non lucratif. | Traçabilité de la source des données éthiques peu documentée publiquement → risque de score perçu comme arbitraire (relevé par des utilisateurs). Nécessite un smartphone et l'app dédiée, pas de mode web. |
| **Kwalito** | Scan → filtres par profil (femme enceinte, sans gluten, sans arachide, sans lactose, végé/végan, sans additif à risque, bio...). | Non documenté publiquement. | Signal de fraîcheur faible : les seules traces disponibles datent d'environ 2015, aucune actualité récente trouvée — statut actif/à l'arrêt à vérifier avant de la citer comme repère concurrentiel. |

## Sources

[Yuka Premium](https://help.yuka.io/l/en/article/dop80j54bb-paid-version-features) · [Avis Yuka — Kalivia](https://kalivia.fr/applications/scanner-produits/yuka/) · [Radio-Canada, méthodologie Yuka](https://ici.radio-canada.ca/nouvelle/1968607/application-yuka) · [Open Food Facts — blog appli](https://blog.openfoodfacts.org/en/news/the-new-open-food-facts-app-to-better-decipher-labels-and-participate-in-the-common-good) · [Open Food Facts — partenaires](https://ca-fr.openfoodfacts.org/partenaires) · [Usine Nouvelle — myLabel](https://www.usinenouvelle.com/article/mylabel-l-appli-qui-repond-aux-attentes-personnelles-des-consommateurs.N1612502) · [Novethic — myLabel](https://www.novethic.fr/actualite/social/consommation/isr-rse/la-video-des-solutions-my-label-l-appli-pour-consommer-responsable-qui-peut-detroner-yuka-147134.html) · [Maddyness — ScanUp](https://www.maddyness.com/2018/06/12/scanup-lappli-des-consommacteurs/) · [ScanUp — FAQ](https://scanup.fr/on-vous-dit-tout/) · [France Info — QuelProduit](https://www.franceinfo.fr/economie/consommation-l-association-ufc-que-choisir-lance-son-application-d-analyse-des-produits_7250043.html) · [Que Choisir Ensemble — QuelProduit](https://eureetloir.quechoisirensemble.fr/2025/06/02/quelproduit-une-application-pour-le-meilleur-choix-de-produit-et-une-vie-plus-saine/) · [Sud Isère — QuelProduit vs Yuka](https://sudisere.quechoisirensemble.fr/quelproduit-vs-yuka-quelles-differences-pour-les-consommateurs/) · [L'Avenir — BiteWatch](https://www.lavenir.net/lifestyle/2025/11/20/additifs-sucre-cache-graisses-bitewatch-la-nouvelle-appli-nutrition-gratuite-que-les-industriels-vont-detester-AVHIPG4X2FAB5FVAJVWNAGJ6IQ/) · [Food in Action — BiteWatch](https://www.foodinaction.com/bitewatch-nouvelle-app-decoder-aliments/) · [Linéaires — Yaquoidedans (Système U)](https://lineaires.com/LA-DISTRIBUTION/Les-actus/Yaquoidedans-la-future-appli-de-Systeme-U-pour-decrypter-la-composition-des-aliments-51887) · [UFC Nouvelle-Calédonie — comparatif apps dont Yaquoidedans](https://www.ufcnouvellecaledonie.nc/applications-pour-aider-les-consommateurs-a-mieux-manger) · [Consoglobe — BuyOrNot](https://www.consoglobe.com/buyornot-appli-achat-ethique-cg) · [BuyOrNot — qui sommes-nous](https://buyornot.org/qui-sommes-nous/) · [Kwalito — présentation (2015)](https://www.mescoursespourlaplanete.com/Actualites/Kwalito__Alkemics__Notaeo___ces_outils_digitaux_qui_simplifient_les_courses_et_assurent_un_choix_aeclairae__2269.html) · [Yuka Help — pourquoi certains produits n'ont pas de recommandation](https://help.yuka.io/l/en/article/dc4vmg886k-absence-of-recommendations) · [Yuka Help — comment sont sélectionnées les recommandations](https://help.yuka.io/l/en/article/s71arvkw6u-selection-recommendations)

## Matrice comparative (fonctionnalités × acteurs)

Légende : ✓ présent et direct · ◐ partiel (limité, indirect, ou à confirmer pour NutriScope) · ✗ absent · ? non documenté publiquement.

| Fonctionnalité | Yuka | OFF | myLabel | ScanUp | QuelProduit | BiteWatch | YaQuoi-Dedans | BuyOrNot | Kwalito | **NutriScope** |
|---|---|---|---|---|---|---|---|---|---|---|
| Score nutrition/qualité | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ | ✓ |
| NOVA affiché explicitement | ✗ | ✓ | ✗ | ✓ | ✗ | ✓ | ✗ | ✓ | ✗ | ◐ |
| Alternative suggérée  | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |
| Personnalisation profil (allergie/régime/grossesse) | ✓ (Premium) | ✗ | ✓ | ✗ | ✗ | ✓ | ✗ | ✗ | ✓ | ◐ |
| Volet éthique/social entreprise | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ |
| Autre univers (cosmétique/entretien) | ✓ cosm. | ✗ | ✗ | ✗ | ✓ les deux | ✗ | ✗ | ✗ | ✗ | ✗ |
| Indépendance vis-à-vis des marques | ✓ | ✓ | ✗ | ✗ | ✓ | ✓ | ✗ | ✓ | ? | ✓ |
| Prix produit / aide budget | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Assistant conversationnel (répond aux questions) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |

### Où sont les cases vides ?

**Colonnes quasi entièrement vides côté concurrence (= cases blanches du marché) :**
- **Assistant conversationnel** : 0/9 concurrent ne le propose. C'est l'une des seules lignes à 100 % vide. Différenciateur réel, mais dont le volume d'usage réel reste à chiffrer avant de le mettre au centre du pitch.
- **Prix / aide au budget** : 0/9 concurrent ne l'affiche, alors que c'est un besoin explicite du persona *Étudiant à petit budget* (`personas.md`) et une limite déjà connue d'Open Food Facts, qui ne fournit pas les prix. Case vide chez tout le monde et NutriScope ne la couvre pas non plus pour l'instant — vraie opportunité si elle est atteignable (données prix absentes d'Open Food Facts, donc à sourcer ailleurs).

**Colonnes fragmentées (personne ne les couvre toutes, dont le leader) :**
- **Alternative suggérée directement au scan** : un seul concurrent sur 9 (myLabel) l'affiche vraiment de façon immédiate et systématique. Yuka, souvent cité comme la référence sur ce point, est en réalité plus limité qu'il n'y paraît : l'alternative n'apparaît pas sur l'écran de scan mais dans une section séparée de la fiche produit, et seulement pour une partie des produits mal notés — Yuka le confirme elle-même dans sa documentation officielle ("nous n'avons malheureusement pas trouvé de bonne alternative" quand ce n'est pas le cas). Les 7 autres concurrents (Open Food Facts, QuelProduit, ScanUp, BiteWatch...) n'ont rien du tout. C'est la case la plus directement exploitable pour NutriScope, à condition de vraiment livrer l'alternative au même endroit que le score — pas dans un onglet à chercher — même si, comme Yuka, NutriScope ne pourra probablement pas la garantir sur 100 % des produits mal notés (couverture `categories_tags` incomplète, `faisabilite.md`).
- **NOVA affiché** : seulement 4/9 (OFF, ScanUp, BiteWatch, BuyOrNot) — Yuka, le leader du marché, ne l'affiche pas séparément (additifs intégrés à son propre score). Une case vide chez le n°1 est un angle d'attaque possible.
- **Volet éthique/social** : seulement 2/9 (myLabel, BuyOrNot) — case vide chez tous les acteurs "score nutritionnel pur", y compris Yuka.
- **Personnalisation profil santé** : couverte par 4/9 mais pas par les deux acteurs les plus utilisés/rigoureux (Open Food Facts, QuelProduit) — pertinent pour le persona *Personne diabétique*, aujourd'hui mal servi par le Nutri-Score seul.

**Case pleine partout (donc pas un facteur de différenciation)** : le score nutrition/qualité de base — 8/9 concurrents l'ont déjà. Ne pas construire la proposition de valeur uniquement dessus.

# SWOT de NutriScope

| **Forces** | **Faiblesses** |
|---|---|
| Assistant conversationnel intégré au parcours. | Dépendance aux données Open Food Facts. |
| Explication du score plutôt qu'un simple verdict. | Qualité et complétude variables des données disponibles. |
| Moteur de substitution : proposer un produit comparable mieux noté. | Pas de données de prix actuellement disponibles dans le périmètre. |
| Positionnement indépendant des marques. | Notoriété et base utilisateurs inexistantes au lancement. |
| Architecture data/ML/RAG permettant de faire évoluer le produit. | Personnalisation et NOVA encore à confirmer selon le périmètre final. |

| **Opportunités** | **Menaces** |
|---|---|
| Besoin d'informations nutritionnelles simples et rapides. | Forte notoriété de Yuka et présence d'acteurs établis. |
| Développement des usages conversationnels. | Évolution rapide des applications concurrentes et des assistants IA. |
| Personnalisation des recommandations. | Qualité variable des données Open Food Facts. |
| Accompagnement vers une décision plutôt que simple notation. | Risque de perte de confiance en cas de recommandation ou information incorrecte. |
| Possibilité d'évolution vers du B2B ou de la marque blanche. | Contraintes réglementaires et responsabilité liées aux recommandations nutritionnelles. |
