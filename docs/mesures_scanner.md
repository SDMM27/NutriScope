# Mesures du scanner — 16/11/2026

## État du noyau du bloc 1

| Attendu du README | Réalisation | Limite |
|---|---|---|
| `pytest outils` | 53 tests passent dans l'environnement autonome : contrat, Parquets et géométrie OCR | Tests du formateur non fournis |
| Palier 3 : aiguillage | Mesure réelle OCR + `qwen3:8b` : 3 statuts corrects / 3 ; catalogue complet branché | Trois images synthétiques seulement pour couvrir les trois statuts |
| Palier 6 : assistant branché | `repondre_photo`, CLI ; 3/3 sur images contrôlées ; jeu réel local passé de 2/3 à 3/3 avec la géométrie OCR | Le cas public Charal échoue encore ; aucun exemple réel vérifié disponible |
| Photo sans tableau | Photo réelle existante du jeu local : `illisible`, résultat attendu | Ne valide pas la lecture d'un vrai tableau |
| Historique et compte rendu | JSON, CSV et historique conservés dans `resultats/scanner/` | Aucune ancienne mesure du jeudi n'a été inventée |

**Bilan : prototype du noyau implémenté et démontré. La validation sur les trois
photos de l'atelier et contre son contrat officiel reste à faire.** Le sujet du
12/11, ses paliers détaillés, ses tests et ses photos sont absents du dépôt.

## Protocole

- Modèle réellement appelé : `qwen3:8b`, Ollama local, `think=false`, température 0
  (modèle de l'ADR 0001). Pas de modèle vision ajouté.
- OCR réel : `Windows.Media.Ocr`, langue française disponible sur le poste.
- Statut décidé par le code, réponse photo formulée sans second appel LLM.
- Catalogue des premières démonstrations (v1) : snapshot d'une ligne réelle des Parquets TP18,
  produit `3017620422003`. Source : Open Food Facts, licence ODbL.
- Images synthétiques reproductibles via `outils/generer_demo_scanner.ps1`.
  La photo réelle sans tableau est la face avant de Heritage Flakes déjà
  présente dans `data/images/cereales/0058449770206.jpg` ; absence de tableau
  vérifiée visuellement avant la mesure.
- Les valeurs/statuts attendus ne sont pas transmis au modèle. Chaque image
  fait l'objet d'un appel indépendant, sans historique de conversation.
- Latences de bout en bout, OCR et éventuel chargement du modèle compris.
  Aucun appel de chauffe exclu : les chiffres ci-dessous ne sont pas un benchmark.
- Les traces contiennent le texte OCR, la sortie LLM, les valeurs retenues et
  les réponses ; les mesures récentes conservent aussi les empreintes du code,
  du catalogue, du manifest et des images.

## Observations exécutées

| Exécution | Entrée | Attendu | Obtenu | Latence |
|---|---|---|---|---:|
| Palier 3, première mesure | Étiquette synthétique Nutella | `verifie` | `verifie` | 13,448 s |
| Palier 3, première mesure | Étiquette synthétique sans identité confirmable | `non_verifie` | `non_verifie` | 5,134 s |
| Palier 3, première mesure | Image synthétique sans tableau | `illisible` | `illisible` | 3,138 s |
| Palier 6, entrée assistant | Étiquette synthétique Nutella | `verifie` | `verifie` | 5,906 s |
| Palier 6, entrée assistant | Étiquette synthétique sans identité confirmable | `non_verifie` | `non_verifie` | 5,318 s |
| Palier 6, entrée assistant | Image synthétique sans tableau | `illisible` | `illisible` | 3,176 s |
| Palier 6, photo réelle | Face avant Heritage Flakes sans tableau | `illisible` | `illisible` | 3,204 s |

Aucun mauvais rattachement, aucune erreur technique sur ces mesures.
Les détails sont respectivement dans :

- `resultats/scanner/20261116T133824474908Z_palier3.json` et son CSV ;
- `resultats/scanner/20261116T133920016745Z_palier6.json` et son CSV ;
- `resultats/scanner/20261116T134035999427Z_palier6.json` et son CSV.

L'historique conserve également les remesures. Une répétition du même jeu
ne constitue pas de nouveaux exemples indépendants.

## Ce que la trace montre

Sur Nutella, le modèle a extrait les valeurs réellement lisibles : 539 kcal,
30,9 g de lipides, 56,3 g de sucres et 0,107 g de sel pour 100 g. Le code a
confirmé le code-barres, le nom, la marque et leur concordance nutritionnelle.
Le Nutri-Score E est issu de la fiche catalogue, pas de l'image ni du LLM.
Saturés, fibres et protéines restent inconnus dans la lecture même si la fiche
catalogue les contient : les deux provenances ne sont pas confondues.

Sur l'image non vérifiée, Windows OCR a lu `Sel g` au lieu de `Sel 0,5 g`.
Le modèle n'a pas inventé le chiffre manquant et le champ sel est resté `null`.
Le statut correct ne signifie donc pas que tous les nutriments sont lus : il
faudra mesurer séparément la précision par champ sur de vraies photos annotées.

## Vérifications et environnement — première version

39 tests passent : vérification EAN, identité absente/ambiguë, divergence,
preuves inventées, valeurs impossibles, unités, tableaux par portion, valeurs
nulles, vrai zéro, JSON invalide, panne OCR et réponse de l'assistant.
Les doubles de modèle sont uniquement dans ces tests, jamais dans les mesures.

L'environnement `.venv` référence un Python 3.12 absent. L'installation de
dépendances a échoué à cause de l'accès réseau restreint. Il n'a pas été réparé.
Les tests ont été exécutés avec le Python 3.13.14 déjà disponible sur le poste,
en chargeant les dépendances Python pures de `.venv/Lib/site-packages` :

```powershell
& 'C:\Program Files\PostgreSQL\18\pgAdmin 4\python\python.exe' -c "import sys,runpy; sys.path.insert(0,'.venv/Lib/site-packages'); sys.path.insert(0,'.'); sys.argv=['pytest','outils','-q','-p','no:cacheprovider']; runpy.run_module('pytest',run_name='__main__')"
```

Les premières mesures utilisent ce même Python 3.13 ; la photo réelle et les
remesures fonctionnent aussi avec le `python` 3.8 disponible, sans pandas grâce
au snapshot JSON. Le chargement du catalogue complet et les tests existants du
TP18 demandent un environnement pandas/pyarrow fonctionnel et n'ont pas été
validés ici. L'assistant texte et ses garde-fous n'ont pas été modifiés pour ce bloc.

## Suite à présenter au formateur

1. Montrer `python outils/mesurer_scanner.py --historique` et les trois réponses
   de l'assistant avec les images de contrôle.
2. Dire explicitement que les tests et le contrat ont été reconstitués.
3. Obtenir/remplacer les photos de l'atelier par trois vraies photos annotées,
   puis remesurer avec le catalogue complet et un environnement réparé.
4. Ne pas annoncer « 100 % de précision du scanner » à partir de ces contrôles.

Pour les commandes, le contrat et les notions à retenir : [scanner.md](scanner.md).

## Version 2 — environnement opérationnel et catalogue complet

L'environnement `.venv-scanner/python.exe` fonctionne hors ligne avec Python
3.13.14 et pytest 9.1.1. Il est préparé depuis le runtime installé avec pgAdmin
et les dépendances Python pures de pytest présentes localement. Le `.venv`
historique du TP18 reste cassé ; il n'a pas été écrasé. Les téléchargements du
runtime Python 3.12 et d'images externes sont bloqués dans cette session.

`src/scanner/catalogue.py::CatalogueParquet` interroge maintenant les deux
Parquets complets avec le CLI DuckDB installé : **1 247 336 lignes produits,
1 247 309 codes distincts**. La recherche exacte ne dédoublonne pas silencieusement
les fiches et ne convertit jamais une valeur absente en zéro. Les CLI du scanner
utilisent ce backend par défaut ; le snapshot n'est plus nécessaire.

**Tests : 45 réussis**, dont six tests d'intégration sur de vrais Parquets
(recherche, identité, nulls, doublons, chemins contenant une apostrophe et
rejet d'arguments pouvant contenir du SQL).

```powershell
powershell.exe -NoProfile -File outils/preparer_env_scanner.ps1
powershell.exe -NoProfile -File outils/tester_scanner.ps1
& .venv-scanner/python.exe outils/mesurer_scanner.py --historique
```

### Nouvelles mesures avec le vrai modèle et le catalogue complet

| Jeu | Palier | Résultats attendus | Mauvais rattachements | Détail |
|---|---:|---:|---:|---|
| Trois images synthétiques, première mesure v2 | 6 | 3/3 | 0 | `20261116T140517599618Z_palier6.json` |
| Trois photos réelles locales, diagnostic | 6 | **2/3** | 0 | `20261116T140600776944Z_palier6.json` |
| Trois images synthétiques, backend numérique final | 3 | 3/3 | 0 | `20261116T140749038626Z_palier3.json` |

Les fichiers JSON et CSV correspondants sont dans `resultats/scanner/` ; leurs
empreintes permettent d'identifier précisément la variante de code mesurée.
Les attentes du jeu réel n'ont pas été adaptées après l'exécution.

### Détail des photos réelles

L'OCR de repérage a parcouru les **3 500 images locales** ; trois candidates
contenaient plusieurs termes nutritionnels. Les deux véritables tableaux
ci-dessous ont été inspectés visuellement ; la troisième candidate ne fournissait
que des mentions d'énergie sur une face avant. Le jeu diagnostique est versionné
sous `outils/fixtures_scanner/manifest_photos_locales.json`.

| Photo réelle | Attendu selon notre contrat | Obtenu | Temps |
|---|---|---|---:|
| Fromage, tableau espagnol sans identité (`5760466815635.jpg`) | `non_verifie` : tableau lisible à l'œil, pas de code/nom/marque visibles | **`illisible` — échec conservé** | 6,556 s |
| Avoine Kölln, tableau 100 g / portion (`4000540040104.jpg`) | `illisible` : multicolonne refusée dans le contrat local | `illisible` | 4,274 s |
| Heritage Flakes, face avant sans tableau (`0058449770206.jpg`) | `illisible` | `illisible` | 3,216 s |

Pour le fromage, l'OCR a notamment lu `1 oog` au lieu de `100 g`, perdu des unités
et séparé les libellés des valeurs. Le modèle a ensuite proposé 189 g de lipides
et 15 g de sucres avec des preuves incorrectes. Le validateur a rejeté ces sorties :
**la lecture échoue, mais aucune fausse valeur ni mauvaise fiche n'est publiée**.
Un agrandissement temporaire de l'image a été essayé : il ne suffit pas à rétablir
la lecture complète. La gestion de l'alignement et des langues est à améliorer.

### Ce qui reste effectivement non validé

- Une vraie photo produisant `verifie` : aucune image locale examinée ne montre
  simultanément un tableau exploitable, le code, le nom et la marque requis.
- La réussite sur une vraie étiquette non vérifiée : le tableau trouvé révèle
  un échec OCR/extraction. Les 3/3 synthétiques ne le compensent pas.
- Le contrat officiel de l'atelier, toujours absent.

Pour continuer utilement, il faut des photos nettes de tableaux nutritionnels en
français, dont une avec l'identité et le code imprimé visibles dans la même image.
La validation réelle complète du bloc 1 n'est pas annoncée comme acquise.

## Recherche publique — photo française trouvée et testée

Une photo réelle française du dos Charal L'Américain a été téléchargée depuis
[Houra, photo produit](https://media.houra.fr/ART-IMG-XL/25/16/3181239101625-2.jpg).
[Fiche source](https://www.houra.fr/charal-l-americain-frites-ketchup-et-sauce-cheddar-220g/1439198/).
Elle montre un tableau pour 100 g, la marque Charal et le code imprimé
`3 181239 101625`. Le nom catalogue complet `Americain Frites` n'est pas confirmé
par le cadrage : l'attente annotée est donc `non_verifie`, pas `verifie`.

Image locale non modifiée : `data/scanner_public/charal_3181239101625.jpg` ;
SHA-256 `e54d0f7837b3bc69a2df85512327317ca67c0a9503c013bee5d922c91f87da0d`.
L'image est réservée au test local, hors Git. Aucun droit de redistribution
n'est présumé. Pour la récupérer à nouveau, enregistrer l'image source à ce
chemin, puis exécuter :

```powershell
& .venv-scanner/python.exe outils/mesurer_scanner.py --manifest outils/fixtures_scanner/manifest_photo_publique.json --palier 6
```

Mesure réelle `qwen3:8b` + catalogue complet : **`illisible`, attendu
`non_verifie`, 6,920 s, aucun mauvais rattachement**. L'OCR lit très mal les
petits caractères sur le tableau en blanc sur fond noir. Un agrandissement x3
essayé séparément ne suffit pas. Ce test est conservé comme un échec de lecture
sous `resultats/scanner/20261116T155703417740Z_palier6.json` et son CSV.

La recherche a également ramené deux liens intitulés « back » et « nutrition »
chez Barcodepedia. L'inspection des fichiers a montré la même face avant
Nutella (empreintes identiques) : ces images ne sont pas utilisées comme
preuve de lecture d'un tableau. Le lien nutrition anglais OFF consulté montrait
également une face avant ; son nom de fichier ne suffit pas à valider son contenu.

Conclusion de cette étape : une photo publique française peut bien être trouvée
sans demander une image à l'utilisateur. Elle révèle une limite réelle du
scanner. La priorité est maintenant le prétraitement OCR et la préservation de
la disposition des valeurs, puis un cas vérifié réunissant aussi le nom complet.

## Version 3 — reconstruction géométrique et comparaison sur les mêmes cas

### Modification livrée

- Les petites photos (grand côté au plus 800 pixels) sont agrandies en mémoire
  vers un grand côté de 1 600 pixels, facteur maximal 4. La photo source reste intacte.
- Windows OCR renvoie les mots et leurs rectangles. `src/scanner/ocr.py`
  reconstruit les lignes selon leurs coordonnées, au lieu de concaténer les
  colonnes dans l'ordre de reconnaissance. Aucun recadrage propre à Charal
  n'est fixé dans le code livré.
- Le texte avant normalisation et les corrections restent dans la trace. La
  confusion O/0 n'est corrigée que dans la base d'un en-tête explicite :
  `por 1 OOg` devient `por 100 g`. Les nombres nutritionnels ne sont pas réparés.
- Le validateur reconnaît les libellés français et espagnols courants, rejette
  les écritures ambiguës comme `05 g`, les preuves traversant plusieurs lignes
  et les lignes portant plusieurs valeurs de la même unité, même si le modèle
  tronque sa preuve pour cacher une colonne.
- Les codes EAN-13 imprimés en groupes 1+6+6 sont acceptés dans une même ligne,
  après contrôle de la clé. L'exigence d'identité et la concordance catalogue
  restent identiques.

**53 tests passent**, avec huit nouveaux tests couvrant la géométrie, les
colonnes multiples, les normalisations, les codes groupés et les preuves ambiguës.

### Résultats exécutés

Même `qwen3:8b`, température 0, même catalogue complet et mêmes attentes qu'en v2.
La vérité terrain n'est pas fournie au modèle. Les jeux existants ne sont pas
modifiés pour obtenir un meilleur résultat.

| Jeu et palier | Version 2 | Version 3 | Mauvais rattachements v3 |
|---|---:|---:|---:|
| Trois images synthétiques, palier 3 | 3/3 | 3/3 | 0 |
| Trois photos locales, palier 6 | 2/3 | 3/3 | 0 |
| Photo publique Charal, palier 6 | 0/1 | 0/1 | 0 |
| Ensemble des quatre photos réelles, palier 6 | 2/4, en réunissant les premières mesures | **3/4** | **0** |

Le manifest `outils/fixtures_scanner/manifest_photos_reelles.json` réunit les quatre
cas déjà utilisés avec leurs attentes inchangées. La dernière exécution complète,
avec le code final de v3, se trouve dans
`resultats/scanner/20261116T162032180051Z_palier6.json` et son CSV.

| Photo | Attendu | Obtenu v3 | Latence finale |
|---|---|---|---:|
| Fromage espagnol sans identité | `non_verifie` | `non_verifie` | 6,822 s |
| Avoine, tableau multicolonne | `illisible` selon notre contrat local | `illisible` | 5,212 s |
| Face avant sans tableau | `illisible` | `illisible` | 3,191 s |
| Charal, caractères trop petits | `non_verifie` | `illisible` — échec | 3,219 s |

Ces latences sont des observations sur ces images, pas un benchmark de vitesse.
La mesure termine volontairement avec le code 1 : **un cas réel échoue encore**.
Les trois premières remesures v3 sont également conservées :
`20261116T161715368263Z_palier6.json`, `20261116T161740256098Z_palier3.json` et
`20261116T161836994701Z_palier6.json`. Leurs empreintes distinguent l'ajout du
contrôle final sur toute la ligne source.

### Vérification des champs sur le cas amélioré

Sur le fromage, les coordonnées replacent `18g` avec `Grasas`, `12g` avec
`saturadas` et `228 kcal` avec `Energia`. Les valeurs retenues correspondent à la
photo inspectée : 228 kcal, 18 g de lipides et 12 g de saturés pour 100 g.
L'identité n'est pas présente : aucune fiche ni aucun Nutri-Score ne sont associés.

Le modèle propose aussi 5 g de sucres depuis `05 g` et 15 g de protéines sans
unité lisible. Le code rejette ces deux propositions et conserve `null`. La
reconstruction géométrique améliore donc la lecture de ce tableau sans faire
passer ses chiffres ambigus pour des valeurs confirmées.

### Essais exploratoires non retenus sur Charal

Un recadrage manuel de diagnostic, inversion, seuillage, retrait des lignes de
grille et plusieurs facteurs d'agrandissement n'ont pas fourni une transcription
fiable avec Windows OCR. Ils ne sont pas utilisés dans la mesure officielle.
Tesseract 5.5.3.20260724 et le modèle français `tessdata_fast` ont aussi été
essayés localement, sans gain suffisant sur cette photo. Le parcours livré
reste Windows OCR ; il ne dépend pas de cette installation expérimentale.

Sources de l'essai Tesseract :
[distribution UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki),
[version Windows](https://github.com/tesseract-ocr/tesseract/releases/download/5.5.3/tesseract-ocr-w64-setup-5.5.3.20260724.exe),
[modèle français](https://github.com/tesseract-ocr/tessdata_fast/blob/main/fra.traineddata).
Empreintes des fichiers téléchargés :
`bee9e3434bd94fd65387d9be28cd467a41f61b1275383b55b0f59a1331270ae4` (distribution),
`ced037562e8c80c13122dece28dd477d399af80911a28791a66a63ac1e3445ca` (modèle).

### Limites restantes

La photo Charal reste trop difficile pour ces essais OCR. Un vrai cas `verifie`
avec tableau et identité complète n'est toujours pas présent dans le jeu : le
bloc 1 n'est donc pas déclaré entièrement validé sur photos réelles.
La normalisation d'un en-tête OCR et la reconstruction des lignes doivent aussi
être évaluées sur davantage de photos, notamment des tableaux inclinés et des
variantes proches. Les 3/4 actuels mesurent des statuts sur un petit jeu de travail,
pas un taux de précision nutritionnelle généralisable.
