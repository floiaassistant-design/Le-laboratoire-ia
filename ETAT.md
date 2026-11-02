# État du laboratoire IA

**Date : 2 novembre 2026** — V0.2, dépôt GitHub dédié.

## Terminé
- EXP-001 et EXP-001B : deux familles de défauts synthétiques, budgets identiques.
- EXP-003 : allocations 0/3/6/9/12 d'un budget de 12 tests ; sélection sur 11 mutations connues.
- Ratio choisi sur apprentissage : **3 tests limites + 9 aléatoires**.
- Sur 6 défauts de validation distincts : **70,5 % hybrides, 64,33 % ciblés, 30,92 % aléatoires**.
- Code Python reproductible, tests de budget/seed et CI GitHub Actions.

## À ne pas affirmer
- Aucun agent IA n'a résolu les défauts : c'est du test algorithmique synthétique.
- Les cas ne sont ni représentatifs ni sélectionnés en aveugle.
- Une même famille de programmes et l'auteur des mutants restent des sources de biais.

## Prochaine étape autonome
EXP-004 : construire un corpus d'exercices indépendant, avec fautes réalistes et tests oracles, non utilisé pour choisir les stratégies. Évaluer les cas par unité (défaut), et non simplement par essai répété ; comparer les variantes de politique et les budgets. Ajouter intervalle d'incertitude et ablations. Seulement ensuite envisager les agents IA réels, avec des coûts et quotas explicitement maîtrisés.

## Contraintes
Ne pas utiliser d'API payante, de planification récurrente, de déploiement public ni de modifications des autres dépôts sans demande séparée. Ne jamais fusionner une PR si la CI échoue.

## Suite du 2 novembre 2026 — EXP-004A
- Intégration en cours : corpus externe QuixBugs, 20 défauts avec versions corrigées, fixtures et licence, au commit épinglé.
- Exécuteur de calibration : comparaison par oracle, isolation par processus, délais par appel, et journal JSON.
- Aucun résultat de politique hybride sur ce corpus : phase suivante EXP-004B, générateurs à concevoir et geler avant exécution.
