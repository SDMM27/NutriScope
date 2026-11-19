# Ce que montre la mesure sans RAG

`// modèle de rédaction — les crochets sont à remplir avec VOS chiffres, mesurés lundi sur votre assistant`

**Mesure du 16/11, modèle `[qwen3:8b]`, assistant du TP 18 tel quel, 10 questions du bloc 2.**

1. **[N] / 10 réponses conformes** (`refus_correct`). [N] réponses justes mais non sourcées, [N] inventées, [N] outils détournés : l'assistant [refuse prudemment / répond de mémoire / mélange les deux].
2. **Ce qui a surpris :** [exemple attendu : les questions sur le nouveau calcul (B04, B05) reçoivent une réponse sûre d'elle mais fondée sur l'ancien algorithme ; ou : l'assistant appelle `chercher_produit("Nutri-Score")` et conclut à partir d'une fiche sans rapport].
3. **Ce que le RAG doit changer :** répondre aux questions de connaissance **en citant un document du corpus**, sans perdre les refus corrects (`erreurs` doit rester à 0 jeudi). Objectif mesurable sur le jeu d'évaluation : passer de [N] / 30 à [N] / 30 conformes, à erreurs constantes ou en baisse.
