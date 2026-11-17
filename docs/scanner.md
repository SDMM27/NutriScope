# Scanner d'étiquettes — bloc 1 du 16/11/2026

## Périmètre

Le sujet du 12/11 et ses fichiers n'étant pas présents, ce module implémente un
**contrat local reconstitué à partir du README du 16/11**. Les tests ne sont pas
ceux du formateur. L'objectif est le noyau : contrat, aiguillage et entrée photo
de l'assistant. Les paliers optionnels vote / rédacteur-relecteur ne sont pas réalisés.

## Fonctionnement

1. `src/scanner/ocr_windows.ps1` lit les mots et leurs coordonnées avec Windows
   OCR ; les petites images sont agrandies jusqu'à un facteur 4 avant lecture.
   `src/scanner/ocr.py` reconstruit les lignes à partir de ces coordonnées.
2. `qwen3:8b`, modèle déjà retenu dans l'ADR, extrait un JSON depuis ce texte.
   Il ne voit pas directement la photo et ne reçoit pas le catalogue.
3. `src/scanner/scanner.py` contrôle les preuves textuelles, les unités, les
   bornes et la base. Les valeurs rejetées ou absentes restent `null`.
4. Le code détermine le statut et, seulement si les contrôles concordent,
   rattache une fiche. Le LLM ne choisit jamais cette fiche.
5. `src/assistant/scanner.py::repondre_photo` formule une réponse déterministe
   à partir du résultat contrôlé. Le modèle ne réécrit pas les chiffres.

L'entrée texte habituelle `repondre(...)` du TP18 et son prompt ne sont pas
modifiés. On dispose d'une entrée photo supplémentaire, indépendante de
l'historique texte : la mesure sans RAG du bloc 2 conserve son comportement.

## Contrat de sortie

| Champ | Contenu |
|---|---|
| `statut` | `verifie`, `non_verifie` ou `illisible` |
| `raison` | Explication machine de l'aiguillage |
| `base` | `100 g`, `100 ml` ou `null` |
| `nutriments` | `kcal`, `lipides`, `satures`, `sucres`, `sel`, `fibres`, `proteines` ; nombre ou `null` |
| `produit` | Identité et Nutri-Score du catalogue, uniquement si `verifie` ; sinon `null` |
| `source` | `etiquette_ocr` pour les valeurs lues |
| `trace` | Texte OCR, sortie brute du modèle, modèle, latence et tokens pour auditer la mesure |

Une erreur de fichier, d'OCR ou de connexion lève une exception. Le script de
mesure la compte comme `erreur_technique`, pas comme une bonne abstention.
Un JSON modèle invalide donne `illisible` avec `raison=sortie_modele_invalide`.

| Statut | Décision locale |
|---|---|
| `illisible` | Base non prouvée, tableau ambigu, ou moins de trois nutriments prouvés |
| `non_verifie` | Au moins trois valeurs prouvées, mais identité ou concordance insuffisante |
| `verifie` | Un seul code EAN-8/EAN-13 lisible et valide, une seule fiche à ce code, nom et marque visibles, base 100 g et au moins trois valeurs comparables concordantes |

Pour chaque nutriment comparable présent, la différence absolue doit être au
plus de **0,05** dans son unité. Une divergence suffit à refuser le rattachement.
Ce seuil est un choix conservateur du prototype, pas une règle du formateur.
La marque est comparée sans le préfixe de langue OFF (`xx:nutella` → `nutella`).
Il n'y a aucune recherche approximative par nom ou profil nutritionnel.

Une preuve doit être une copie exacte du texte OCR reconstruit, inclure le libellé
du nutriment et une seule valeur avec l'unité attendue. Toute la ligne source est
contrôlée, même si le modèle en copie seulement une partie. Les seuils (`<`), pourcentages,
conversions et tableaux par portion sont refusés. Le seuil de trois valeurs est
également une convention locale. Ce filtre privilégie l'abstention.

## Lancer la démonstration

Depuis la racine, avec Ollama lancé et `qwen3:8b` disponible :

```powershell
powershell.exe -NoProfile -File outils/generer_demo_scanner.ps1
powershell.exe -NoProfile -File outils/preparer_env_scanner.ps1
& .venv-scanner/python.exe outils/scanner_photo.py data/scanner_demo/verifie.png
& .venv-scanner/python.exe outils/scanner_photo.py data/scanner_demo/non_verifie.png
& .venv-scanner/python.exe outils/scanner_photo.py data/scanner_demo/illisible.png
```

Ces images sont **synthétiques**. Les commandes ci-dessus consultent maintenant
les Parquets complets avec DuckDB. Le snapshot optionnel de la première version
reste disponible avec `--catalogue-json outils/fixtures_scanner/catalogue.json`.
Source du catalogue : Open Food Facts, licence ODbL. Les attentes ne vont pas au modèle.

Pour lire une vraie photo avec le catalogue complet :

```powershell
& .venv-scanner/python.exe outils/scanner_photo.py chemin/etiquette.jpg --json
```

API Python correspondante :

```python
from src.scanner.catalogue import CatalogueParquet
from src.assistant.client_ollama import ClientOllama
from src.assistant.scanner import repondre_photo

resultat = repondre_photo("chemin/etiquette.jpg", CatalogueParquet(), ClientOllama())
print(resultat["reponse"])
print(resultat["scanner"]["statut"])
```

## Rejouer les contrôles

```powershell
powershell.exe -NoProfile -File outils/tester_scanner.ps1
& .venv-scanner/python.exe outils/mesurer_scanner.py --manifest data/scanner_demo/manifest.json --palier 3
& .venv-scanner/python.exe outils/mesurer_scanner.py --manifest data/scanner_demo/manifest.json --palier 6
& .venv-scanner/python.exe outils/mesurer_scanner.py --manifest outils/fixtures_scanner/manifest_photos_locales.json --palier 6
& .venv-scanner/python.exe outils/mesurer_scanner.py --historique
```

Chaque exécution ajoute un JSON détaillé, un CSV et une entrée d'historique dans
`resultats/scanner/`. Au palier 6, la réponse de l'assistant est aussi enregistrée.
Les mesures utilisent réellement OCR et modèle ; les doubles ne servent qu'aux
tests unitaires. Une mesure avec erreur ou mauvais statut termine avec le code 1.

Pour un jeu personnel, créer un manifest JSON avec `type_images`, `provenance`
et `cas`. Chaque cas contient `id`, `photo` (relative au manifest),
`statut_attendu` et `code_attendu` si le statut attendu est `verifie`.
Les attentes doivent être contrôlées sur la photo et dans le catalogue.
Le manifest réel sans tableau fourni est
`outils/fixtures_scanner/manifest_sans_tableau.json`.

## Environnement autonome et catalogue complet (version 2)

Le `.venv` historique pointe toujours vers un Python 3.12 absent. Son remplacement
ne peut pas être téléchargé depuis le terminal de cette session. Pour rendre le
scanner utilisable, `outils/preparer_env_scanner.ps1` prépare hors ligne
`.venv-scanner/python.exe` avec le Python embarqué 3.13.14 déjà installé avec
pgAdmin et les dépendances Python pures de pytest déjà présentes dans le projet.
Ce runtime est ignoré par Git ; le script permet de le reconstruire. Sur un autre
poste, fournir un runtime embarqué installé avec `-PythonSourceDir`.

Le scanner n'a plus besoin de pandas/pyarrow : `CatalogueParquet` utilise le CLI
DuckDB installé, joignant les deux Parquets au code exact. Il conserve les doublons
et les valeurs nulles, et convertit les nutriments en nombres. Sur ce poste :
1 247 336 lignes produits, **1 247 309 codes distincts**. Il n'importe pas le
catalogue entier en mémoire. `DUCKDB_EXE` permet de préciser le chemin du CLI.
Le DataFrame du TP18 reste accepté par l'API, sans modifier l'assistant texte.

Le script de tests utilise un temporaire neuf dans `.tmp` pour éviter le dossier
pytest système inaccessible. **53 tests passent**, dont six tests d'intégration
avec de vrais Parquets temporaires, les doublons et les chemins contenant une apostrophe.

Les 3 500 photos locales ont été examinées par OCR pour repérer des tableaux.
Le jeu réel diagnostique contient trois photos inspectées visuellement : un
fromage sans identité visible, une étiquette d'avoine multicolonne et une face
avant sans tableau. Le premier essai donne **2/3** : le fromage est refusé à tort
comme illisible. Ce résultat est conservé comme un échec, pas comme une validation.
Ce résultat historique est amélioré par la version 3 décrite ci-dessous.

## Géométrie OCR et caractères ambigus (version 3)

Windows OCR peut lire successivement tous les libellés, puis toutes les valeurs
d'une colonne. Les concaténer dans cet ordre fait perdre les associations entre
nutriments et chiffres. Le scanner regroupe maintenant les mots dont les centres
verticaux sont proches, puis les trie de gauche à droite. Les mots, leurs rectangles,
le facteur d'agrandissement et les normalisations restent dans la trace.

Sur les petites images (grand côté au plus 800 pixels), le redimensionnement est
fait en mémoire, avec un grand côté cible de 1 600 pixels et un facteur maximal 4.
Le fichier photo n'est pas modifié. Le code n'utilise aucun recadrage fixé pour Charal.

Une correction de caractères est autorisée dans un en-tête : `1 OOg` peut devenir
`100 g` quand il s'agit d'une base explicite (`pour/par/por/per`, ou en-tête seul).
Elle est enregistrée dans `trace.ocr.corrections`, avec le texte précédent.
Les nombres nutritionnels et les codes ne sont pas corrigés de cette façon.
Les libellés français et espagnols courants sont reconnus par le validateur.

Les valeurs ambiguës comme `05 g`, les preuves traversant plusieurs lignes et
les lignes portant plusieurs valeurs de la même unité sont rejetées. Un code
EAN imprimé sous la forme `3 017620 422003` est accepté après contrôle de sa clé,
sans fusion de chiffres provenant de lignes différentes.

Résultat : le fromage espagnol du jeu local fournit maintenant **228 kcal,
18 g de lipides et 12 g de saturés**. L'identité reste inconnue : `non_verifie`.
Le modèle propose aussi 5 g de sucres depuis `05 g` et 15 g de protéines sans
unité OCR : ces deux propositions sont rejetées, les champs restent à `null`.

Le jeu local passe de 2/3 à 3/3 statuts attendus. La photo publique Charal reste
illisible ; il ne faut pas annoncer 100 % sur l'ensemble des photos réelles.
Un essai séparé avec Tesseract 5.5.3 et le modèle français n'a pas suffi à lire
ce tableau ; Tesseract n'est pas une dépendance du parcours livré.

## Ce qu'il faut retenir

- **Lire n'est pas identifier.** L'OCR peut lire des chiffres sans savoir de quel
  produit il s'agit. C'est le contrôle d'identité qui autorise le rattachement.
- **Le LLM propose ; le code contrôle.** Un JSON bien formé ne prouve pas que les
  chiffres sont exacts. Chaque valeur retenue doit aussi avoir une preuve OCR.
- **`null` n'est pas zéro.** La démonstration a réellement perdu le sel `0,5 g`
  lors de l'OCR de l'image non vérifiée : il est resté inconnu, sans être inventé.
- **Le Nutri-Score vient du catalogue vérifié.** Il n'est ni deviné ni calculé
  depuis un tableau partiel.
- **S'abstenir est un résultat utile.** Une photo sans tableau doit demander une
  nouvelle photo, sans emprunter les valeurs d'un produit ressemblant.
- **Les tests et les mesures répondent à deux questions différentes.** Les tests
  contrôlent les règles ; les mesures observent OCR + vrai modèle. Trois images
  propres ne suffisent pas à estimer les performances en conditions réelles.
- **Ce n'est pas encore du RAG.** Le scanner transcrit une étiquette et contrôle
  une fiche ; il ne répond pas aux questions générales de nutrition.

## Limites et suite

Le mot `verifie` signifie « concordant avec ce catalogue selon ces contrôles »,
pas une certification du contenu de l'emballage ni de la qualité du catalogue.
La trace prouve une présence dans l'OCR, dont la reconnaissance peut être fausse.
Les cas réels doivent donc être relus sur les photos.

Le prototype exige que le nom, la marque, le code imprimé et le tableau soient
visibles dans la même image. Il ne décode pas les barres du code-barres.
Il refuse les tableaux multicolonnes par portion ; les lectures pour 100 ml
restent non vérifiées faute de base équivalente explicite dans le catalogue.
Windows OCR est requis ; aucune dépendance vision n'est ajoutée à Ollama.

Prochaine validation : vraies photos avec tableaux, flou, lumière, identité
incomplète, variantes proches et produits absents, avec le catalogue complet.
Le bloc 1 n'est pas présenté comme validé par le contrat officiel manquant.

Référence technique : [Windows.Media.Ocr.OcrEngine — Microsoft](https://learn.microsoft.com/en-us/uwp/api/windows.media.ocr.ocrengine).
Résultats exécutés : [mesures_scanner.md](mesures_scanner.md).
