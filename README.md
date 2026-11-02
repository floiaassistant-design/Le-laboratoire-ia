# Laboratoire IA — recherche expérimentale

Prototype indépendant consacré à l'évaluation rigoureuse de méthodes de vérification et, plus tard, de véritables architectures d'agents IA.

**Statut :** V0.2 — EXP-001, EXP-001B et EXP-003 exécutées localement, code de reproduction publié. Aucune API facturée, aucune automatisation périodique. GitHub Actions lance uniquement les tests lors des push/PR.

## Reproduire (Python 3.10+ ; dépendances externes : aucune)

```bash
python -m unittest discover -v
python run_experiment.py
python run_robustness.py
python run_hybrid.py
```

Chaque script enregistre un JSON dans `results/`. Les expériences utilisent 12 entrées par défaut et par répétition, répétées 200 fois, avec graines fixes. Les tests sont déterministes. Les fichiers historiques EXP-001 et EXP-001B peuvent être recalculés sans API.

## Expériences et résultats

| Expérience | Méthode aléatoire | Méthode ciblée | Hybride |
|---|---:|---:|---:|
| EXP-001, 6 mutants de frontières | 57/1200 (4,75 %) | 1200/1200 (100 %) | — |
| EXP-001B, 5 mutants d'intérieur | 531/1000 (53,1 %) | 302/1000 (30,2 %) | — |
| EXP-003, apprentissage, 11 mutants | 574/2200 (26,09 %) | 1518/2200 (69,0 %) | **1625/2200 (73,86 %)** |
| EXP-003, lot de validation, 6 mutants | 371/1200 (30,92 %) | 772/1200 (64,33 %) | **846/1200 (70,5 %)** |

L'hybride retient **3 tests aux frontières et 9 tests aléatoires**, choisis sur l'ensemble d'apprentissage avant de calculer les résultats du second ensemble. La politique dite « ciblée » utilise les frontières disponibles puis des tirages aléatoires pour compléter le budget.

**Limites importantes :**
- Tous les programmes sont des **défauts synthétiques imaginés par l'auteur**, pas des défauts réels ni des sorties d'IA.
- Le lot de validation est distinct du lot d'apprentissage **mais pas aveugle** : le concepteur connaît les défauts.
- Les 200 répétitions par cas ne sont pas 200 défauts indépendants ; la précision statistique apparente ne doit pas être surestimée.
- EXP-003 ne démontre PAS la supériorité d'agents IA. Comparaison d'agents reportée.

## Structure

- `lab/cases.py` : 6 défauts de frontières (EXP-001).
- `lab/robustness.py` : 5 défauts autres (EXP-001B).
- `lab/hybrid.py`, `lab/holdout.py` : protocole EXP-003.
- `run_*.py` : reproduction hors réseau.
- `tests/` : tests de validité, budget égal et reproductibilité.
- `experiments/` : protocoles et limites.
- `ETAT.md` : état et prochaine étape de travail.

Aucune action n'est effectuée sur les autres dépôts. Aucun coût d'API. La maintenance et les expériences continuent uniquement lors d'une session déclenchée par l'utilisateur.

## EXP-004A — calibration externe (QuixBugs)

Avant de comparer à nouveau les stratégies, le laboratoire doit valider un exécuteur sur un corpus indépendant : 20 programmes du jeu de données QuixBugs, chacun avec sa version défectueuse, sa version corrigée et ses tests canoniques. Sources figées au commit `4257f44b0ff1181dedaedee6a447e133219fcebf`, licence MIT fournie sous `third_party/quixbugs/LICENSE`.

```bash
python -m lab.quixbugs_screen
```

Produit `results/exp004a.json`, avec les détails par programme, cas validés par l'oracle, cas exclus et erreurs détectées. Le banc d'essai protège les appels par des délais maximaux et exécute chaque programme dans un processus enfant distinct.

**Attention :** l'EXP-004A ne teste pas encore nos trois politiques. Les tests fournis par QuixBugs sont choisis pour révéler leurs défauts : leur taux de réussite ne peut pas servir à mesurer un gain d'une méthode de sélection de tests. L'EXP-004B devra définir des générateurs indépendants et figer une grille équitable de budgets avant l'évaluation.

Sources : https://github.com/jkoppel/QuixBugs (commit épinglé ci-dessus). Les fichiers tiers restent sous licence MIT et ne sont pas modifiés.

**Contrôle qualité EXP-004A :** la CI vérifie explicitement la découverte d'au moins 16 tests ; l'ancienne CI exécutait 0 tests à l'insu du rapport de statut. Le code de comparaison normalise maintenant les générateurs Python (cas `flatten`).

### Résultat vérifié EXP-004A (CI #41538320018)
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

## EXP-004B — 16 nouveaux programmes QuixBugs

Les quatre programmes pilotes sont exclus. Trois politiques à budgets égaux (1, 3, 6, 12) sont comparées sur des entrées générées depuis les domaines d'entrée, sans usage des fixtures fournies. Le code et protocole se trouvent dans `lab/quixbugs_external.py` et `experiments/EXP-004B-EXTERNAL.md`. Ce n'est pas un benchmark aveugle et **aucune IA n'est appelée**. Résultats attendus dans les journaux GitHub Actions et l'artefact brut de la PR après exécution. Aucun résultat n'est revendiqué avant la CI.

## EXP-004B — résultats externes, 16 programmes (CI #41540117757)

| Budget maximal | Aléatoire | Ciblé | Hybride |
|---:|---:|---:|---:|
| 1 | 94/160 (58.75 %) | 0/160 (0.00 %) | 0/160 (0.00 %) |
| 3 | 131/160 (81.88 %) | 110/160 (68.75 %) | 110/160 (68.75 %) |
| 6 | 150/160 (93.75 %) | 120/160 (75.00 %) | 143/160 (89.38 %) |
| 12 | 154/160 (96.25 %) | 160/160 (100.00 %) | 158/160 (98.75 %) |

- Tous les 16 programmes ont été évalués ; aucun processus n'a échoué ; 0 entrée rejetée par l'oracle dans ces mesures.
- **Programme distinct** : au budget 1, au moins une erreur a été détectée sur 16/16 programmes par les tirages aléatoires, contre 0/16 par les premiers tests ciblés. Au budget 12, au moins un essai détecte le défaut dans les 16 programmes pour chaque stratégie.
- **Interprétation :** aucune politique n'est systématiquement supérieure. Les premiers tests ciblés sont peu informatifs et l'ordre figé pénalise particulièrement les budgets 1 et 3. À budget 12 le ciblé détecte 160/160 essais, l'hybride 158/160 et l'aléatoire 154/160.
- 32 tests unitaires ont été découverts et réussis. Résumé JSON : `results/exp004b-external-summary.json`. Données brutes : artefact `exp004b-external-raw` dans la [run GitHub](https://github.com/floiaassistant-design/Le-laboratoire-ia/actions/runs/41540117757) (durée de conservation temporaire).
- Les dix répétitions par programme sont corrélées ; seules 16 erreurs distinctes ont été étudiées. Les cas avaient été publiquement accessibles avant la conception des politiques : **ce n'est pas une évaluation aveugle**. Aucune IA/agent n'a été comparée.

### Prochain objectif : EXP-005
Évaluer séparément l'**ordre des tests ciblés**, en gardant un budget fixe et en effectuant des permutations sans retoucher les ensembles de cas. Analyser l'effet sur le premier test et sur les budgets 3/6, sur le même corpus comme *analyse exploratoire*. Puis concevoir un protocole réellement nouveau (ou des corpus aveugles) pour vérifier sa généralisation, sans utiliser ces résultats pour choisir une méthode et la valider sur ces mêmes défauts.
