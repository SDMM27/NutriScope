# TP 14 — Prédire le Nutri-Score

> Projet fil rouge **NutriScope** · mardi 20/10, Christophe Ringot, demi-journée
> Après le module 4.3 « Classification » (12, 13 et 14/10)
> En équipe de 2-3, dans le dépôt Git de l'équipe
> Données : `data-nutriscope/ml/nutriscope_ml_sample.parquet` — © Open Food Facts contributors — ODbL

## Le sujet, tel qu'il figure au Cahier de TP

**Objectif : première brique ML sérieuse — classification A→E depuis les caractéristiques produit.**

1. Baselines d'abord : classe majoritaire, puis arbre de décision simple. Ce sont elles qu'il faudra battre — les noter.
2. Modèles du matin appliqués : régression logistique multinomiale, random forest ; pipeline scikit-learn complet (préprocesseur inclus) pour éviter toute fuite de données.
3. Validation croisée 5 plis stratifiée ; métriques adaptées au déséquilibre (F1 macro, matrice de confusion normalisée).
4. Lecture des variables importantes : est-ce cohérent avec la définition officielle du Nutri-Score ? Si le modèle triche (fuite via une colonne dérivée du score), le dire et corriger.
5. Trois erreurs types analysées à la main, produits réels à l'appui.

**À committer** : `notebooks/ml_nutriscore.ipynb` + tableau comparatif baseline/modèles.

---

## Mise en situation

Depuis le 24 septembre, NutriScope a nettoyé, exploré, raconté et industrialisé ses
données. Le jalon J3 du 14 octobre a livré un pipeline qui va du CSV brut aux exports
prêts pour l'entraînement. Et depuis le 6 octobre, la phase 4 vous a donné les outils :
la régression au 4.2, la classification cette semaine.

La direction — les formateurs — attend maintenant la première réponse à la question qui
porte tout le projet : **peut-on prédire la lettre d'un produit à partir de ses
caractéristiques ?** Pas pour remplacer le Nutri-Score officiel, qui existe déjà, mais
pour deux usages concrets :

- **compléter** les fiches qui n'ont pas de grade (une large part du catalogue Open Food
  Facts) ;
- **repérer** les fiches dont le grade déclaré ne colle pas aux nutriments — celles que
  le nettoyage a laissées passer.

Vous avez une demi-journée. Ce n'est pas un concours de performance : c'est un TP sur le
**protocole**. Une équipe qui rend 0,86 avec un protocole défendable vaut mieux qu'une
équipe qui rend 0,98 sans avoir vu qu'elle trichait.

## Prérequis

- **TP 9** (nettoyage industrialisé) : les règles de cohérence, réutilisées pour lire les
  erreurs du modèle.
- **TP 12 et TP 13** : le Parquet « features » et la colonne `split` figée. Vous ne la
  recalculez pas.
- **Module classification**

## Les données

|                         | Valeur                                                                                                                                   |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Fichier                 | `data-nutriscope/ml/nutriscope_ml_sample.parquet`                                                                                        |
| Produits                | 30 041 (train 24 076 / test 5 965)                                                                                                       |
| Cible                   | `nutriscore_grade` — a, b, c, d, e                                                                                                       |
| Features                | 7 nutriments obligatoires, `fiber_100g`, `fruits-vegetables-legumes_100g`, `nova_group`, `additives_n`, `pnns_groups_1`, `pnns_groups_2` |
| **Jamais des features** | `code`, `product_name`, `brands`, `split` — et **`nutriscore_score`**                                                                    |

Le chemin se résout par rapport au fichier, et la variable d'environnement
`NUTRISCOPE_DATA` l'écrase :

```python
from pathlib import Path
import os

def data_dir() -> Path:
    env = os.environ.get("NUTRISCOPE_DATA")
    if env:
        p = Path(env).expanduser().resolve()
        return p.parent if p.is_file() else p
    return Path(__file__).resolve().parents[2] / "data-nutriscope"
```

## Étapes, avec leurs points de contrôle

### Étape 1 — Les baselines (30 min) — point 1 du sujet

Entraînez et notez **trois** baselines en validation croisée 5 plis stratifiée :

- `DummyClassifier(strategy="most_frequent")` — tout le monde dans la classe majoritaire ;
- `DummyClassifier(strategy="stratified")` — le tirage au hasard qui respecte les proportions ;
- un **arbre de décision simple** (`max_depth=3`, puis `max_depth=8`) — celui que le sujet
  demande explicitement.

Pour chacune : F1 macro avec son écart-type, accuracy, accuracy équilibrée.

> **Point de contrôle 1.** Votre baseline majoritaire doit afficher une accuracy
> d'environ 0,29 et un F1 macro d'environ 0,09. Si les deux chiffres sont proches, vous
> avez calculé un F1 pondéré, pas un macro. Le rapport entre les deux — plus de trois —
> est **le** chiffre à commenter dans le journal.

> **Point de contrôle 2.** L'arbre de profondeur 3 ne doit dépasser 0,40 de F1 macro
> sous aucun réglage. S'il le fait, regardez ses feuilles : dit-il jamais « a » ou
> « b » ? Avec huit feuilles pour cinq classes déséquilibrées, il ne devrait pas.

### Étape 2 — Le pipeline complet (45 min) — point 2 du sujet

Assemblez **un seul objet** `Pipeline` qui contient toute la préparation puis le modèle :

- imputation des colonnes optionnelles (médiane + indicateur de manquant) ;
- les features dérivées (ratios, écart d'énergie) créées **dans** le pipeline via un
  `FunctionTransformer`, jamais à la main sur le DataFrame ;
- standardisation des numériques ;
- one-hot des deux catégorielles, avec `handle_unknown="ignore"` et un `min_frequency`
  pour regrouper les rayons rares ;
- puis `LogisticRegression` (multinomiale) ou `RandomForestClassifier`.

Entraînez les deux modèles que le sujet nomme : **régression logistique multinomiale** et
**random forest**.

> **Point de contrôle 3.** Écrivez le test qui prouve que le préparateur n'a pas vu le
> test : après `fit` sur le train, la moyenne d'une colonne standardisée du **train**
> transformé doit être nulle à 1e-9 près, et celle du **test** transformé ne doit pas
> l'être. Si les deux sont nulles, vous avez ajusté sur tout le jeu.

> **Point de contrôle 4.** Comptez les colonnes en sortie du préparateur. Vous devez en
> avoir une soixantaine à partir de 13 colonnes brutes. Un nombre très supérieur signale
> un one-hot sans regroupement des catégories rares.

### Étape 3 — La validation croisée et les métriques (30 min) — point 3 du sujet

Construisez les plis **une seule fois** et passez-les à chaque modèle :

```python
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
```

Produisez un tableau unique : une ligne par modèle, F1 macro avec son écart-type,
accuracy, accuracy équilibrée, temps d'ajustement et de prédiction. Puis, pour le
meilleur modèle, la **matrice de confusion normalisée par ligne**.

> **Point de contrôle 5.** Votre matrice normalisée doit sommer à 1 sur chaque ligne. Si
> elle somme à 1 par colonne, vous avez normalisé par `"pred"` — chaque case devient une
> précision et non un rappel, ce qui ne se lit pas de la même manière.

> **Point de contrôle 6.** Les plis doivent être identiques d'un modèle à l'autre.
> Vérifiez-le : deux appels à `cv.split(X, y)` doivent rendre exactement les mêmes
> indices. Sans cette garantie, votre tableau ne compare rien.

Décidez ensuite si le déséquilibre mérite un traitement. Mesurez d'abord le rapport
majoritaire / minoritaire, puis comparez le modèle brut à une version
`class_weight="balanced"` et, si vous voulez, à SMOTE — **dans** un
`imblearn.pipeline.Pipeline`.

> **Point de contrôle 7.** Si votre score bondit après SMOTE, vérifiez le placement
> **avant** de vous réjouir. SMOTE appliqué avant le découpage gonfle le F1 macro de
> près de 0,02 sur ce jeu, et ce gain est une fiction.

### Étape 4 — Importances, barème officiel, et la fuite (45 min) — point 4 du sujet

**4a. Reproduisez la fuite, volontairement.** Entraînez le même modèle avec
`nutriscore_score` ajouté aux features, en validation croisée. Notez le F1 macro obtenu.
Calculez ensuite l'importance par permutation et regardez quelle part cette seule
colonne prend.

**4b. Diagnostiquez.** Écrivez, en trois lignes, les symptômes que vous observez et
pourquoi cette colonne est une fuite — l'argument métier compte autant que le chiffre.

**4c. Corrigez.** Retirez la colonne, et écrivez un **test** qui garantit qu'elle ne peut
pas revenir par accident.

**4d. Contrôle négatif.** Rejouez la même procédure sur une colonne légitime (par exemple
`completeness`). Elle ne doit rien signaler : un détecteur qui crie au loup partout ne
sert à rien.

**4e. Confrontez au barème.** Calculez les importances par permutation du modèle honnête,
sur un pli de validation **interne au train**, et comparez-les aux sept composantes
officielles du Nutri-Score : énergie, sucres, graisses saturées et sel (défavorables) ;
fibres, protéines, fruits-légumes-légumineuses (favorables). Ni `nova_group`, ni
`additives_n`, ni les glucides totaux, ni les lipides totaux n'y figurent.

Répondez par écrit : **est-ce cohérent ?** Et si une colonne hors barème pèse lourd,
est-ce une fuite ou un **proxy** ? Justifiez.

> **Point de contrôle 8.** Avec la fuite, vous devez dépasser 0,97 de F1 macro. Sans
> elle, vous devez rester sous 0,90. Si vous obtenez plus de 0,90 sans la colonne,
> cherchez une autre fuite : une feature dérivée du grade s'est glissée quelque part.

> **Point de contrôle 9.** Les importances par permutation se calculent sur un jeu que
> le modèle n'a **pas** vu à l'entraînement. Si vous les calculez sur le train
> d'ajustement, elles reflètent la mémorisation, pas la généralisation.

### Étape 5 — Le test, puis trois erreurs (45 min) — point 5 du sujet

Ajustez le modèle retenu sur **tout** le train, prédisez le test, et écrivez les chiffres
**avant** de les commenter. C'est la seule fois où vous regardez le test.

Puis remontez aux produits : sortez les prédictions fausses, triées par écart de grade
puis par confiance du modèle, avec leur `code`, leur `product_name` et leurs nutriments.
**Choisissez-en trois de natures différentes** et analysez-les à la main.

Pour chacune, écrivez :

1. les nutriments du produit, tels qu'ils figurent dans la fiche ;
2. pourquoi le modèle a prédit ce qu'il a prédit ;
3. le **diagnostic** : erreur d'apprentissage, fiche fausse, règle métier absente des
   features, ou référentiel différent ;
4. l'**action** : réglage du modèle, règle à ajouter au TP 9, ou limite à documenter.

> **Point de contrôle 10.** Si vos trois diagnostics sont « le modèle doit mieux
> apprendre », vous n'avez pas assez creusé. Sur ce jeu, la majorité des erreurs très
> confiantes sont des problèmes de données ou de périmètre — et c'est **ça**, le
> rendement de l'analyse d'erreurs.

> **Point de contrôle 11.** Votre écart entre la validation croisée et le test ne doit
> pas dépasser 0,05. Au-delà, soit le split n'est pas représentatif, soit vous avez fait
> un choix en regardant le test.

## Conseils

- **Ne cherchez pas la performance.** Le module vous a donné les chiffres de référence :
  la forêt tourne autour de 0,86, la logistique autour de 0,77. Si vous y êtes, passez
  aux points 4 et 5, qui portent l'essentiel de la note.
- **Écrivez les chiffres avant de les commenter.** Un tableau rempli après coup pour
  justifier une conclusion se voit.
- **Un notebook narratif.** Chaque section répond à un point du sujet, chaque tableau est
  suivi de deux ou trois lignes de lecture. Le notebook se lit sans que vous soyez là.
- **Répartissez.** À trois : un sur les baselines et le pipeline, un sur la validation
  croisée et le déséquilibre, un sur la fuite et les erreurs. Puis relecture croisée.
- **Committez à chaque étape**, avec un message qui dit ce qui marche. Et notez dans
  `docs/journal.md` la phrase de synthèse du modèle.

## Dépannage

| Symptôme                               | Cause probable                                                 | Que faire                                                                  |
| -------------------------------------- | -------------------------------------------------------------- | -------------------------------------------------------------------------- |
| `ConvergenceWarning` sur la logistique | `max_iter` par défaut (100) trop bas                           | passer à 3000 ; vérifier que la standardisation est bien dans le pipeline  |
| F1 macro au-dessus de 0,95             | une fuite                                                      | lister les features ; chercher une colonne dérivée du grade ou du score    |
| F1 macro autour de 0,20                | le modèle prédit presque toujours la même classe               | vérifier que la cible n'a pas été encodée à l'envers ; regarder la matrice |
| Le score change à chaque exécution     | graine non fixée                                               | `random_state=42` sur le modèle **et** sur `StratifiedKFold`               |
| `imblearn` refuse le pipeline          | un `Pipeline` scikit-learn est passé comme étape intermédiaire | aplatir les étapes du préparateur dans la liste de l'`ImbPipeline`         |
| Le Parquet est introuvable             | chemin relatif au répertoire courant                           | résoudre par rapport au fichier ; `export NUTRISCOPE_DATA=...`             |
| `predict` change le nombre de lignes   | SMOTE appliqué hors pipeline                                   | le rééchantillonnage ne s'applique qu'au `fit`                             |

## Grille d'évaluation sur 20

| Critère                              | Points | Ce qui est attendu                                                                                                                                                                         |
| ------------------------------------ | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Baselines** (point 1)              | 3      | les trois baselines entraînées et notées ; le piège de l'accuracy explicitement commenté                                                                                                   |
| **Pipeline sans fuite** (point 2)    | 5      | toute la préparation dans un seul `Pipeline` ; logistique multinomiale **et** forêt ; la preuve que le préparateur n'a pas vu le test                                                      |
| **Protocole et métriques** (point 3) | 4      | fold stratifiés construits une fois ; F1 macro avec écart-type ; matrice normalisée lue, pas seulement affichée ; test regardé une seule fois                                              |
| **Fuite et importances** (point 4)   | 5      | la fuite reproduite, diagnostiquée avec ses trois symptômes, corrigée, et la correction testée ; les importances confrontées aux sept composantes officielles, avec les proxies identifiés |
| **Trois erreurs** (point 5)          | 3      | trois produits réels, de natures différentes, avec nutriments, diagnostic et action ; au moins un diagnostic qui ne soit pas « le modèle doit mieux apprendre »                            |

**Pénalités** : `nutriscore_score` laissé dans les features sans que ce soit signalé
(−5) ; test regardé plusieurs fois ou modèle choisi dessus (−3) ; chiffres cités sans
écart-type ni baseline (−2) ; notebook non exécutable de haut en bas (−2) ; crédit Open
Food Facts absent (−1).

## Ce que le TP 15 reprendra

Le **tableau comparatif**, les **plis** et les **métriques** de ce TP. Le 22 octobre, vous
mesurerez le gradient boosting dans **exactement** les mêmes conditions — même
préparation, mêmes plis, mêmes métriques, même colonne `split`. Toute condition changée
invaliderait la comparaison.

Vous reprendrez aussi vos **trois erreurs analysées** : le TP 15 demande d'examiner les
confusions restantes (b/c, d/e) et de rédiger la note « ce que le modèle rate ». Ce que
vous écrivez aujourd'hui en sera le premier paragraphe.

---

Données : Open Food Facts — **© Open Food Facts contributors — ODbL**.
Tout livrable qui les utilise porte ce crédit.
