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

### Incident qualité vérifié
Première exécution de la PR #3 : 0 tests unitaire effectivement découverts, même si étape GitHub verte. Correction : `unittest discover -s tests` et assert >=16. La version corrigée de `flatten` retourne un générateur ; l'exécuteur doit épuiser ce générateur avant comparaison. Ces corrections doivent être confirmées par un nouveau run CI avant fusion.

### Journal de résultats vérifiés EXP-004A (CI #41538320018)
- 20 programmes QuixBugs sélectionnés, 20 programmes évaluables, 20 défauts exposés par au moins une fixture canonique.
- 153 fixtures chargées : 151 validées par l'oracle, 2 exclues (Levenshtein).
- 107 fixtures valides exposent le défaut documenté.
- 16 tests unitaires découverts et réussis. Données source : `results/exp004a.json`.
- **Pas de comparaison de nos politiques, et pas de taux de réussite d'agent IA**. Les fixtures QuixBugs sont faites pour révéler les bogues connus.


## Résultats EXP-004B pilote (GitHub Actions #41539090595)

**Pré-enregistré avant lecture des résultats.** Quatre programmes × 40 répétitions, trois méthodes et budgets 1, 3, 6, 12. Source officielle : `results/exp004b-pilot-summary.json`.

| Maximum de tests | Aléatoire | Ciblée | Hybride |
|---|---:|---:|---:|
| 1 | 151/160 (94,375 %) | 40/160 (25 %) | 40/160 (25 %) |
| 3 | 160/160 | 160/160 | 160/160 |
| 6 | 160/160 | 160/160 | 160/160 |
| 12 | 160/160 | 160/160 | 160/160 |

**Interprétation :** sur ce pilote, les deux politiques ciblées perdent fortement à budget 1, en raison du premier cas de frontière imposé. Dès le budget 3, le score de détection sature pour les trois politiques. Le banc d'essai ne démontre donc pas de gain général de l'hybride, et quatre défauts restent beaucoup trop peu pour généraliser. Les 40 répétitions ne sont pas des observations indépendantes. Aucun modèle IA n'a été appelé.

**Étape suivante :** élaborer les générateurs et oracles pour les 16 autres programmes, vérifier la validité des domaines, puis mener une comparaison à budget limité. L'étape doit signaler les biais liés aux bogues connus et distinguer les comparaisons de politiques des véritables agents IA.

## EXP-004B évaluation 16 programmes — préparation
- Politiques figées, 16 programmes distincts du pilote.
- Budget 1/3/6/12 avec 10 répétitions par programme.
- CI configurée pour tests unitaires (>=32) et archivage brut.
- Pas d'ajustement des politiques après lecture du résultat : examiner les échecs et ouvrir EXP-005 pour analyses exploratoires si nécessaire.
