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

## EXP-005 — permutations des tests ciblés

Même 16 programmes, mêmes 12 cas ciblés par programme que dans EXP-004B. L'hypothèse est que leur **ordre** pénalise les petits budgets. Script `python -m lab.quixbugs_order`, protocole `experiments/EXP-005.md`. Comparaison du préfixe initial et de permutations aléatoires avec probabilité combinatoire exacte. Il s'agit d'une analyse exploratoire, pas d'une validation sur un nouveau benchmark ni de l'exécution d'agents IA. Le résultat est à publier après vérification CI.


## Résultats vérifiés EXP-005 (CI n° 41598473940)

| Budget | Ordre initial : programmes détectés | Ordre uniformément permuté : espérance exacte | 10e–90e centile empirique, 256 permutations |
|---:|---:|---:|---:|
| 1 | 0/16 | 8,33/16 | 6 à 10 |
| 3 | 11/16 | 12,46/16 | 11 à 14 |
| 6 | 12/16 | 14,70/16 | 13 à 16 |
| 12 | 16/16 | 16/16 | 16 |

La **même liste de 12 tests ciblés par programme** a été utilisée dans les deux conditions. Aucun nouveau cas n'a été ajouté. Les 16 programmes ont été évalués, aucun test de référence n'a été rejeté et les 39 tests unitaires ont réussi.

Les 256 permutations ne sont pas 256 bogues indépendants. Ce résultat montre l'importance de l'ordre de nos tests ciblés sur **ces défauts connus**, pas la supériorité d'une méthode intelligente de réorganisation ni l'efficacité d'agents IA. Les statistiques sont **exploratoires**. Le résultat complet et les comptes par programme sont dans `results/exp005-summary.json`. Les observations détaillées ont été enregistrées en artefact `exp005-order-raw` du run GitHub (conservation temporaire).

**Prochaine question :** apprendre ou prédéfinir un ordre de test sans consulter les défauts à détecter, puis vérifier sur de nouveaux programmes réellement indépendants. Ne pas choisir un ordre ici et revendiquer ensuite une validation sur ces 16 mêmes programmes.

## EXP-006A — pilote de priorisation sans modèle

Un ordre fondé uniquement sur la **diversité structurelle des entrées** est comparé à l'ordre fixe et à l'ordre uniformément aléatoire sur les 4 programmes pilotes QuixBugs. Méthode gelée avant résultat ; détails dans `experiments/EXP-006A.md`. Aucun modèle IA n'est appelé, aucune connexion au PC et aucune API. Les cas ne sont pas indépendants du développement du projet ; ce sont des résultats exploratoires.


## EXP-006A — résultats du pilote (GitHub Actions n° 41599592799)

| Budget | Ordre fixe, programmes détectés | Diversité, programmes détectés | Permutation uniforme, espérance exacte |
|---:|---:|---:|---:|
| 1 | 1/4 | 1/4 | 2,8333/4 |
| 3 | 4/4 | 4/4 | 3,7409/4 |
| 6 | 4/4 | 4/4 | 3,9697/4 |
| 12 | 4/4 | 4/4 | 4/4 |

**Conclusion du pilote :** la priorisation par diversité Jaccard/farthest-first n'améliore pas la couverture sur ces quatre cas connus. Avec un seul test, elle reste moins efficace en couverture que l'espérance théorique d'une permutation uniformément aléatoire de ces mêmes entrées. Le premier cas sélectionné n'est pas nécessairement le plus révélateur d'un défaut, malgré sa singularité structurelle.

Les 48 tests unitaires sont réussis, quatre programmes ont été évalués, aucune entrée rejetée par l'oracle. Résultat complet par programme : `results/exp006a-summary.json`. Données brutes : artefact `exp006a-diversity-raw` du [run GitHub n° 41599592799](https://github.com/floiaassistant-design/Le-laboratoire-ia/actions/runs/41599592799).

Limites : seulement 4 défauts indépendants, dans un corpus déjà connu ; pas de nouvelle méthode validée, pas d'agents IA évalués. **Il ne faut pas sélectionner de nouveaux paramètres sur ces quatre cas et déclarer ensuite une validation indépendante sur les mêmes bugs.** La prochaine étape est une étude de faisabilité d'un deuxième benchmark reproductible sur GitHub Actions, puis un protocole nouveau avec séparation claire développement/validation.

## EXP-006B — qualification d'un nouveau corpus de bugs réels

L'étape suivante examine [BugsInPy](https://github.com/soarsmu/BugsInPy) et [PyBugHive](https://github.com/pybughive/pybughive). La licence de ces dépôts **n'est pas confirmée** : leur contenu n'est pas recopié ici. Deux cas PySnooper (projet MIT) servent de candidats de **qualification de métadonnées seulement** : commits fautif/corrigé, filiation du correctif, présence des tests, licence du code source. Le script `python -m lab.external_corpus_preflight --online` ne lance aucune version bugguée, n'installe rien et ne produit aucun score de détection. Voir `experiments/EXP-006B.md` et `experiments/exp006b-manifest.json`. L'expérimentation réelle exige encore un environnement Python historique et des épreuves FAIL/PASS validées.


## Résultat confirmé EXP-006B — source et premier bug réel

La [CI de la PR n° 12, exécution n° 41601918091](https://github.com/floiaassistant-design/Le-laboratoire-ia/actions/runs/41601918091) est **entièrement réussie**, avec **61 tests unitaires**. Deux paires de commits PySnooper (issues de BugsInPy) ont été qualifiées par métadonnées : leur relation directe fautif → corrigé, les tests historiques présents dans le correctif et la licence MIT ont été vérifiés.

**Une véritable reproduction** a ensuite été effectuée en Python **3.8.18** sur Ubuntu 22.04, sans `pip install` ni scripts setup tiers : sur PySnooper-1, sous une locale ASCII contrôlée, la version fautive `e21a3116...` provoque précisément un `UnicodeEncodeError`, tandis que le correctif `56f22f8f...` réussit à écrire les caractères Unicode. Un mini-test autonome basé sur le symptôme connu a servi à cette calibration : **ce n'est pas** le test officiel BugsInPy et **ce n'est pas** un test indépendant découvert par un agent.

Résultat machine conservé dans `results/exp006b-summary.json`, détails du précontrôle et du bug dans les artefacts `exp006b-corpus-preflight` et `exp006b-realbug-smoke` de la CI. Le résultat couvre **un bug connu**, sur un projet, et ne démontre aucune amélioration de nos stratégies de priorisation. Le second cas est **seulement qualifié**, pas reproduit. Les licences des corpus BugsInPy et PyBugHive ne sont pas établies pour une éventuelle redistribution.

### Suite scientifique

Préparer une reproduction fiable d'un deuxième défaut dans un projet **distinct**, puis définir une interface de test homogène et un véritable lot de validation sans voir les résultats des bugs avant de geler les méthodes. Ne pas confondre test de calibration du bug déjà connu avec mesure de performance de la nouvelle politique.

## EXP-006C — deuxième projet réel (tqdm)

Reproduction technique d'un bug publié affectant `tqdm.contrib.tenumerate(start=42)`, sur deux commits upstream explicitement figés issus des métadonnées BugsInPy. Python 3.8 / GitHub Actions ; aucune dépendance installée et aucun code du benchmark recopié. Critère : ancienne version indexe `[0,1,2]` et corrigée `[42,43,44]`. **Calibration de bug connu**, pas découverte ni validation de stratégie. Voir `experiments/EXP-006C.md`. Résultat à insérer uniquement après CI.


## EXP-006C — résultat confirmé (CI GitHub #41603652941)

**Deuxième logiciel indépendant : `tqdm`**, sur le bug historique `tenumerate(start)` (BugsInPy bug n° 1). Dans un clone temporaire de code upstream, sous Python **3.8.18** (Ubuntu 22.04), notre probe de calibration a demandé l'énumération de trois valeurs en partant de `42` :

| Version | Résultat de l'indice de départ | Verdict |
|---|---|---|
| Défectueuse `8cc777fe...` | `[0,1,2]` | Erreur de décalage reproduite |
| Corrigée `c0dcf39b...` | `[42,43,44]` | Comportement attendu |

Les valeurs `["a","b","c"]` ont été conservées ; **les deux programmes se sont exécutés**, et seule la sémantique d'indexation était incorrecte avant le correctif. Les **trois jobs CI** ont réussi, avec **69 tests unitaires** réellement découverts. La vérification des sources historiques PySnooper utilise désormais le jeton GitHub temporaire *read-only*, envoyé **uniquement** à l'API GitHub et jamais aux autres hôtes, pour éviter les limites d'accès anonymes. Les exécutions de code tiers ne conservent pas de jeton Git dans le checkout.

Résultat versionné : `results/exp006c-summary.json` ; détails : artefact `exp006c-tqdm-realbug` du [run #41603652941](https://github.com/floiaassistant-design/Le-laboratoire-ia/actions/runs/41603652941).

**Conclusion scientifique limitée :** le laboratoire peut désormais **reproduire deux bugs connus dans deux logiciels réels différents** (PySnooper et tqdm). Il n'a **pas** découvert de bug inconnu ni démontré la qualité des politiques aléatoire/ciblée/hybride/diversité sur un corpus de bugs réels. La version d'origine documentait Python 3.6.9, tandis que notre calibration utilise 3.8.18. Le probe utilise une classe de progression transparente et n'est pas le test officiel de BugsInPy.

**Suite :** définir une méthode uniforme de sélection de tests réels, choisir et figer plusieurs bugs *avant d'examiner leurs résultats*, puis mesurer les comparaisons avec coûts et incertitudes groupés par défaut/projet. Ne pas réutiliser les deux calibrations connues comme preuves indépendantes.


## Contrôle post-fusion du 3 novembre 2026 : instabilité détectée et correction

Le [premier run post-fusion #41604159224](https://github.com/floiaassistant-design/Le-laboratoire-ia/actions/runs/41604159224) a **échoué**, alors que la CI de la PR #13 était verte : les deux commits ont produit les indices `[0,1,2]`. Le résultat EXP-006C n'était donc pas encore suffisamment reproductible. Le code de calibration changeait de commit **dans le même dossier**, tout en exécutant le Python de chaque version dans le même chemin. Une **contamination par cache de bytecode** est l'explication plausible ; elle n'est pas prouvée comme cause unique.

La correction crée désormais deux **worktrees Git physiquement distincts**, fait pointer `PYTHONPATH` vers chacun, désactive l’écriture de nouveaux fichiers .pyc et sépare les répertoires pour éviter de relire les caches de l’autre version (`-B` et `PYTHONDONTWRITEBYTECODE=1`) et répète le test de tqdm trois fois dans des répertoires temporaires frais. Elle applique la même isolation au test PySnooper. Un seul échec rend le workflow rouge ; aucun échec n'est ignoré.

**Ces trois répétitions ne sont pas trois bugs indépendants.** Elles vérifient uniquement que la calibration de notre infrastructure est stable. Les deux projets restent des défauts historiques connus, impropres à une mesure indépendante de la performance de politiques de priorisation. Les conclusions doivent se fonder sur le run corrigé, pas sur la seule première CI verte.


### EXP-006C : correction confirmée sur la PR #15

Le [run #41604816339](https://github.com/floiaassistant-design/Le-laboratoire-ia/actions/runs/41604816339) a réussi : **74 tests unitaires**, les **trois jobs CI**, et **trois répétitions fraîches** de la calibration tqdm. À chacune, le commit défectueux produit `[0,1,2]` et le correctif `[42,43,44]`, avec les mêmes valeurs `["a","b","c"]`. La calibration PySnooper a également réussi avec ses worktrees séparés.

L'échec post-fusion précédent est **conservé** dans le journal scientifique : il s'agissait d'une non-reproductibilité de notre procédure (probablement liée aux caches Python lors des changements de commit dans le même dossier), pas de la découverte d'un nouveau bug. Le changement corrige l'isolation et les trois répétitions réussies attestent un meilleur comportement dans la CI. **La cause exacte n'est pas démontrée isolément**. La reproductibilité devra rester surveillée sur `main`.

Les répétitions ne comptent pas comme de nouveaux défauts, et la nouvelle méthode de sélection n'est toujours pas évaluée sur ces logiciels réels.

## EXP-007A — inventorier les tests réels sans les exécuter

`lab.real_test_inventory` lit statiquement les définitions Python `test_*` via l'AST, génère des identifiants et des signatures structurelles, et signale les erreurs. La CI valide d'abord ce mécanisme sur les fichiers du laboratoire ; **aucun programme bugué n'est exécuté, aucune stratégie testée, aucun modèle IA requis**. Ce ne sont que des candidats de tests (pas une collecte pytest certifiée). Protocole : `experiments/EXP-007A.md`.


## EXP-007A — résultats du premier inventaire statique (CI #41607357594)

Sur **nos propres fichiers `tests`**, le module a repéré **11 fichiers de tests Python**, lu les 11 avec succès, et relevé **90 définitions candidates**. Le contrôle parallèle `unittest discover` a exécuté **90 tests unitaires**, tous réussis. Aucun fichier erroné, aucune définition paramétrée non développée, aucun défaut logiciel noté, aucune politique de sélection évaluée.

Les **trois jobs** CI de la [PR #16 — run #41607357594](https://github.com/floiaassistant-design/Le-laboratoire-ia/actions/runs/41607357594) ont réussi, y compris les calibrations historiques PySnooper et tqdm. La sortie complète est archivée dans l'artefact `exp007a-inventory-raw` ; cette synthèse est versionnée dans `results/exp007a-summary.json`.

**Interprétation limitée :** 90 candidats statiques et 90 tests exécutés sur le laboratoire représentent une **égalité de compte**, pas la preuve que les 90 identifiants AST correspondent individuellement à toutes les unités de test collectées par des outils comme pytest. Le code n'a exécuté aucun fichier inspecté ; il ne couvre pas toutes les formes de paramétrisation, héritage ou génération dynamique. Le programme ne doit pas être présenté comme un agent IA ni comme un algorithme de découverte de bugs.

**Suite :** validation de l'interface d'identifiants sur une collecte isolée et comparaisons réellement aveugles sur **de nouveaux bugs et projets**, en excluant les deux défauts historiques déjà connus.
