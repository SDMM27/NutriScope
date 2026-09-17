# Note d'hypothèses — kpi_roi.xlsx

| Hypothèse | Valeur retenue | Source / justification | Fragilité |
|---|---|---|---|
| Utilisateurs actifs mensuels | 1000 / 5000 / 20000 (pess./centr./optim.) | Ordre de grandeur estimé, pas de canal d'acquisition chiffré | Élevée |
| Taux de conversion premium (scénarios coûts/ROI) | 2 % / 3 % / 5 % | Hypothèse centrale, pas de benchmark cité | Élevée |
| Taux de conversion premium (cible KPI produit) | 10 % | ⚠️ Incohérent avec le scénario central ci-dessus (3 %) — à harmoniser | Élevée |
| Prix abonnement premium | 1,45 € / 2,99 € / 5,99 € / mois | Alignement approximatif sur des concurrents (type Yuka) | Moyenne |
| Taux d'activation (J+7) | 70 % | Hypothèse centrale, cible ambitieuse non benchmarkée | Élevée |
| Rétention à 30 jours | 60 % | Hypothèse centrale | Moyenne |
| Taux de substitution acceptée | 40 % | Marqué "à valider par tests" | Élevée |
| Coût par requête assistant | 0,02 € | "Trouvé sur internet", pas de prix fournisseur/volume réel | Élevée |
| Conversations assistant / utilisateur / mois | 3 (cible KPI) vs. ~1 (utilisé pour chiffrer le coût IA/API) | ⚠️ Incohérent — le coût IA/API ci-dessous sous-estime si la cible de 3 conversations est atteinte | Élevée |
| Jours-hommes développement | 25 / 18 / 12 j | Charge équipe estimée, valorisée à 350 €/j (TJM dev junior) | Élevée |
| Coûts infra / an | 300 € / 700 € / 1750 € | Hébergement API + base + front, mis à l'échelle des utilisateurs actifs | Moyenne |
| Coûts IA/API / an | 50 € / 250 € / 1000 € | Coût par requête (0,02 €) × ~1 conversation/utilisateur actif/mois × 12 | Élevée |

Les jours-hommes et les coûts infra/IA varient en sens inverse d'un scénario à l'autre : les premiers dépendent de la difficulté d'exécution (un scénario optimiste = moins de friction, moins de jours), les seconds du volume d'usage (un scénario optimiste = plus d'utilisateurs, donc plus de charge et de requêtes à payer).

## 3 hypothèses les plus fragiles et comment les vérifier tôt

1. **Taux de conversion premium** — incohérent entre onglets (3 % dans les scénarios ROI, 10 % en cible KPI produit) et non benchmarké. À vérifier via un test de paywall (offre limitée dans le temps) sur une cohorte beta avant le lancement complet.
2. **Coût par requête assistant (0,02 €)** — chiffre générique, pas lié au prix réel du LLM choisi ni à un volume de conversations mesuré. À chiffrer sur un échantillon de vraies conversations testées en interne avec le modèle retenu.
3. **Taux de substitution acceptée (40 %)** — marqué "à valider par tests", directement lié à la proposition de valeur du produit. À mesurer sur le MVP avec un petit groupe d'utilisateurs test (clic/usage réel des alternatives).
