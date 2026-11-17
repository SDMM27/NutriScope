# ADR 0001 — L'assistant utilise `qwen3:8b` en local via Ollama, mode sans raisonnement (`think: false`)

Date : 09/11/2026 · Statut : **acceptée**

## Contexte

L'assistant NutriScope répond sur les produits **à partir du catalogue** (Open Food Facts, ODbL) en appelant l'outil `chercher_produit`. Le modèle doit donc savoir appeler un outil de façon fiable et répondre en français. Contraintes : projet de formation avec 10 € de crédits OpenRouter pour une comparaison ponctuelle, démonstration sur poste Windows (Intel, sans GPU dédié identifié), questions d'utilisateurs potentiellement sensibles (santé), et aucun secret dans le dépôt.

## Options

1. **API commerciale** (Claude, GPT…) : modèle hébergé hors UE, clé d'API en variable d'environnement.
2. **API hébergée en Europe** (ex. Mistral) : même principe, données traitées dans l'UE.
3. **Modèle local via Ollama** : `qwen3:8b` ou `qwen3:4b-instruct`, avec ou sans mode raisonnement.

## Critères

Mesures faites le 09/11 sur le poste de démo (Windows 11, Intel) : un appel outillé = 1er tour où le modèle doit demander `chercher_produit` ; 5 répétitions après une chauffe, `temperature = 0`.

| Option | Appel d'outil demandé | Latence médiane 1 tour | Réponse complète (2 tours) | Coût marginal | Confidentialité |
|---|---|---|---|---|---|
| `qwen3:8b`, `think: false`, **sans** prompt système | **0 / 5** (répond « je n'ai pas accès ») | 3,9 s | — | 0 € | données restent sur le poste |
| `qwen3:8b`, `think: false`, avec prompt système | 5 / 5 | **2,6–2,9 s** | 6 à 18 s (notebook) | 0 € | idem |
| `qwen3:8b`, `think: true`, avec prompt système | 5 / 5 | 5,9 s | ≈ ×2 | 0 € | idem |
| `qwen3:4b-instruct`, avec prompt système | 5 / 5 | 2,5 s | non mesuré | 0 € | idem |
| OpenRouter (`openai/gpt-oss-20b:floor`) | appel sur la première question ; suivi résolu avec l'historique | — | 2,0 s puis 1,9 s | **0,000073 $** au total (0,000034 $ puis 0,000039 $) | données envoyées à un tiers (routage à vérifier pour le modèle choisi) |

Qualité (observée sur la démo `notebooks/tp18_assistant_llm.ipynb`) : `qwen3:8b` appelle le bon outil avec des arguments valides dans 100 % des cas testés, et aucun chiffre hors résultat d'outil n'a été détecté. Mais il commet des erreurs de formulation (voir Conséquences). Sur les deux questions comparées, Ollama et OpenRouter donnent les mêmes valeurs ; OpenRouter répond de façon plus concise. Exécution du 10/11 (tableau récapitulatif du notebook) : latences totales de 8,2 s (Ollama) contre 2,0 s (OpenRouter) pour le Nutri-Score, puis de 3,3 s contre 1,9 s pour le suivi sur les sucres. Ces deux observations ne constituent pas un benchmark général.

## Décision

**`qwen3:8b` en local via Ollama, `think: false`, `temperature = 0`, avec un prompt système qui impose l'outil.**

- Gratuit, sans clé, et les questions (parfois liées à la santé) ne quittent pas le poste.
- Le mode raisonnement double la latence (5,9 s contre 2,7 s) sans gain sur l'appel d'outil mesuré.
- 8b plutôt que 4b-instruct : seulement 0,1 à 0,4 s d'écart, pour un modèle plus capable sur la rédaction. Le 4b reste la solution de repli si la machine manque de mémoire.
- Les clients (`src/assistant/client_ollama.py` et `client_openrouter.py`) partagent la méthode `discuter(messages, outils)`. La comparaison ponctuelle avec `openai/gpt-oss-20b:floor` confirme les mêmes valeurs pour un coût API total de 0,000073 $, sans remettre en cause le choix local par défaut.

## Conséquences

- ✅ Coût nul, aucune donnée envoyée à un tiers, aucun secret à gérer. La démo tourne hors ligne (hors téléchargement du modèle).
- ✅ Format d'outil compatible OpenAI : un adaptateur OpenRouter existe pour comparer le modèle local à un modèle hébergé.
- ❌ **Lent** : 6 à 18 s pour une réponse complète sur CPU. C'est acceptable pour une démo, trop lent pour l'application grand public (TP 23) sans GPU ni serveur dédié.
- ❌ **Qualité de rédaction limitée** : dans la démo, le modèle écrit « ne contient pas de fibres » pour une valeur **absente** (null), et, même après le renforcement du prompt sur la recommandation, il présente des chips notées D sous le titre « bon Nutri-Score (A ou B) » et propose des chips comme alternative au Nutella. Le prompt seul ne suffit pas, d'où le vérificateur de chiffres (`verifier_chiffres`, qui rattache chaque nombre au nutriment cité), qui ne détecte toutefois que les nombres, pas les contresens. La vraie recommandation attend le moteur de substitution (TP 21).
- ❌ **Le prompt système est indispensable** : sans lui, 0/5 appel d'outil. Toute modification du prompt doit être rejouée sur la démo.
- À réexaminer si : la latence devient bloquante (TP 23), le taux d'erreurs de formulation reste élevé après correction du prompt, ou une API hébergée dans l'UE doit être évaluée séparément.
