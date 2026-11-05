# Laboratoire IA — recherche expérimentale

**EXP-017 fusionnée le 5 novembre 2026** ([PR #61](https://github.com/floiaassistant-design/Le-laboratoire-ia/pull/61), **8 workflows PR verts, 458 tests**) : [protocole](experiments/EXP-017-CONSERVATIVE-ROUTING.md), [16 questions figées](experiments/exp017-cases.json) et [résultats versionnés](results/exp017-conservative-summary.json). Routeur prudent **sans appel de modèle** : 8 `single`, 4 `needs_review`, 3 `uncertain`, 1 `unsupported` sur les 16 nouveaux cas stylisés ; **16/16** questions naturelles EXP-016 réutilisées restent `uncertain`. Les annotations balisées sont stables mais **la couverture demeure très faible**, sans gain d'exactitude ou de coût réel démontré. Prochaine mission : [EXP-018, issue #62](https://github.com/floiaassistant-design/Le-laboratoire-ia/issues/62), couverture sur nouvelles demandes naturelles et perturbations non balisées.


**EXP-016 fusionnée le 5 novembre 2026** ([PR #58](https://github.com/floiaassistant-design/Le-laboratoire-ia/pull/58), **8 workflows PR verts et 439 tests**) : [protocole](experiments/EXP-016-ROUTING-STRESS.md), [16 questions figées](experiments/exp016-cases.json) et [résumé durable](results/exp016-routing-summary.json). Le nouveau remplissage neutre ne modifie aucune des 16 routes du candidat, contrairement aux 16 du témoin longueur. Mais le candidat refuse **16/16** cas en nombres écrits en mots, change **12/16** routes avec un `then` non mathématique, et **4/4** lors d'un remplacement du connecteur. **Aucun LLM appelé, aucune supériorité de précision démontrée, pas de validation aveugle**. Prochaine mission : [EXP-017, issue #59](https://github.com/floiaassistant-design/Le-laboratoire-ia/issues/59), routeur prudent et abstention explicite.


**EXP-015 fusionnée le 5 novembre 2026** ([PR #55](https://github.com/floiaassistant-design/Le-laboratoire-ia/pull/55), **8 workflows PR verts, 424 tests**) : [audit d'un routeur à indices de contenu](experiments/EXP-015-CONTENT-ROUTING.md). Sur les six questions EXP-014 **déjà connues**, 0/6 variation de route sous le remplissage exact, contre 6/6 pour l'ancien routeur. Un contre-exemple avec `then` trompeur fait varier le candidat dans 3/6 cas. [Synthèse durable](results/exp015-routing-summary.json). **Aucun LLM n'a été appelé et aucune amélioration de qualité n'a été démontrée.** Prochaine mission : [EXP-016, issue #56](https://github.com/floiaassistant-design/Le-laboratoire-ia/issues/56), nouveaux cas et perturbations gelés avant calcul.



**EXP-014 fusionnée le 5 novembre 2026** ([PR #52](https://github.com/floiaassistant-design/Le-laboratoire-ia/pull/52), **8 workflows PR verts et 410 tests**) :
[stabilité du routeur face au remplissage neutre](experiments/EXP-014-NEUTRAL-PADDING.md).
Six problèmes arithmétiques × trois longueurs : **6/6 changements de route**
sous un ajout de phrases sans nouvelles données numériques et **6 → 12
appels de rôle prévus**. La [synthèse versionnée](results/exp014-routing-summary.json)
est contrôlée par les tests. **Ce résultat est mécanique, pas une mesure
d'intelligence, de coût réel ni d'avantage multi-agent.** Le protocole
GSM8K EXP-011 reste inchangé.



**EXP-013 fusionnée le 5 novembre 2026** ([PR #49](https://github.com/floiaassistant-design/Le-laboratoire-ia/pull/49), 8 workflows verts, 391 tests) :
[analyse appariée des stratégies et des données manquantes](experiments/EXP-013-PAIRED-ANALYSIS.md).
Elle prépare le calcul honnête des résultats des 12 tâches d'évaluation
EXP-011, sépare blocages de politique et erreurs de modèle, rend
explicites les abstentions et les limites de coût, et conserve les
évaluations non observées. **Précontrôle synthétique uniquement : zéro
nouvel appel de modèle, aucune preuve de supériorité multi-agent.**



**Nouveau pilote exploratoire :** [EXP-012 — calibration GPT-6 en
conversation unique](experiments/EXP-012-SINGLE-CONTEXT-CALIBRATION.md).
Quatre réponses réelles auto-déclarées ont été enregistrées avant
lecture des solutions, puis vérifiées ligne à ligne : **4/4** sur
quatre questions de **calibration**, sans contexte indépendant.
Un score sur quatre questions publiques ne constitue pas une validation
des politiques multi-agents. La [PR #46](https://github.com/floiaassistant-design/Le-laboratoire-ia/pull/46) est fusionnée : ses huit workflows sont verts, dont la vérification indépendante du fichier source complet et du score **4/4**.


**Étape du 5 novembre 2026 :** [EXP-011B — carnet de sessions manuelles équilibrées](experiments/EXP-011B-BALANCED-RUNBOOK.md), fusionnée via [PR #43](https://github.com/floiaassistant-design/Le-laboratoire-ia/pull/43). Il prévoit l'ordre des 64 essais de l'EXP-011, prépare des consignes séparées et contrôle les sources. **Aucun modèle IA n'est automatiquement interrogé et aucun score n'est encore mesuré.**


**État vérifié :** [ETAT.md](ETAT.md) — projet Python
reproductible et expériences documentées sur GitHub.

Les trois expériences récentes sont **fusionnées** :
[EXP-010A — routeur adaptatif](experiments/EXP-010A-ADAPTIVE-ROUTING.md),
[EXP-010B — comparateurs simulés](experiments/EXP-010B-SYNTHETIC-EVALUATION.md)
et [EXP-011 — protocole GSM8K public](experiments/EXP-011-MANUAL-REAL-TASKS.md)
([PR #41](https://github.com/floiaassistant-design/Le-laboratoire-ia/pull/41)).
Les 350 tests unitaires requis ont passé la CI de la PR #41.

**Limite déterminante : EXP-011 n'a interrogé aucun vrai modèle IA.**
Les 16 problèmes GSM8K ne sont pas un jeu de validation aveugle.
Le code sait préparer des questions sans réponses et, séparément,
noter des sorties de sessions **manuellement** renseignées après
vérification de la source officielle. Il ne lance ni ChatGPT ni un modèle
local, et n'a pas accès automatiquement aux coûts de tokens.
La prochaine étape est suivie par
[l'issue #40 — essais réels](https://github.com/floiaassistant-design/Le-laboratoire-ia/issues/40).
Les chantiers historiques de bugs (#29 et #35) restent distincts.

Prototype indépendant consacré à l'évaluation rigoureuse de méthodes de vérification et, plus tard, de véritables architectures d'agents IA.

**État actuel et consignes de reprise entre agents : [ETAT.md — REPRISE IMMÉDIATE](ETAT.md#reprise-immédiate--pour-un-autre-agent-état-vérifié-le-4-novembre-2026).** Le projet a progressé jusqu'à **EXP-009E**, inventaire AST des tests des 12 défauts historiques (448 occurrences statiques, **sans exécution de leurs tests ni score**). Les missions suivantes sont [#29 — environnements reproductibles](https://github.com/floiaassistant-design/Le-laboratoire-ia/issues/29) et [#35 — témoins métier et contraintes OS](https://github.com/floiaassistant-design/Le-laboratoire-ia/issues/35), à figer avant toute mesure. L'[issue #23](https://github.com/floiaassistant-design/Le-laboratoire-ia/issues/23) conserve l'historique scientifique des phases précédentes. Les rubriques plus anciennes de ce README restent un historique des expériences. Aucune API de modèle facturée, aucune automatisation périodique.

## Reproduire les tests internes (Python 3.11+ ; pas d'installation tierce nécessaire)

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

## EXP-007B — comparaison des identifiants de tests

Le script `lab.real_test_collector` compare les tests candidats identifiés statiquement aux **identifiants unittest réellement collectés**, y compris les différences et doublons. Le collecteur importe le code de test : utilisation volontairement limitée au dépôt de confiance, avec `--allow-imports`. Aucun test collecté n'est exécuté par cette comparaison, aucun bug évalué et aucun agent/modèle IA connecté. Protocole : `experiments/EXP-007B.md`.


## EXP-007B — résultat vérifié, identité des tests (CI #41650099193)

Sur **notre suite de tests interne**, l'inventaire AST a produit **104 identifiants**, et `unittest discover` a réellement collecté **104 objets TestCase**. La comparaison des **multiensembles d'identifiants exacts** a donné **104/104 correspondances**, **0 candidat uniquement statique**, **0 test uniquement runtime**, **0 erreur d'import/collecte**. Les **104 tests unitaires ont réussi**, tout comme les trois jobs de GitHub Actions (y compris PySnooper et les trois répétitions tqdm). Résultat synthétique : `results/exp007b-summary.json` ; sortie complète de comparaison : artefact `exp007b-identity-raw` du [run #41650099193](https://github.com/floiaassistant-design/Le-laboratoire-ia/actions/runs/41650099193).

Cette étape améliore la précédente : les identifiants **correspondent individuellement**, ce n'est plus seulement une égalité de nombre. Mais la vérification est limitée **à notre dépôt de confiance**. La collecte `unittest` a importé les modules de tests, pouvant exécuter du code de niveau module ou des hooks `load_tests` ; le programme comparateur n'a appelé **aucune méthode de test**. La CI, elle, exécute séparément les tests unitaires habituels.

**0 défaut testé pour performance, 0 politique comparée, 0 agent IA évalué.** Les suites pytest, paramètres dynamiques, plugins et héritages ne sont pas encore qualifiés. Prochaine tâche : mettre en place l'isolation pour un vrai corpus tiers et comparer les inventaires dans cette isolation, *sans consulter les résultats de bugs*, avant toute étude de performance.

## EXP-008A — premier pilote comparatif sur deux nouveaux bugs réels

Deux paires de versions historiques épinglées **youtube-dl** et **Tornado** (sources Unlicense/Apache-2.0) sont évaluées avec une même suite de tests post-correctif, contre trois politiques de sélection **lexicale / aléatoire / diversité AST** (budgets 1/3/6/12). Le banc de tests inclut potentiellement des régressions créées après découverte des bugs : il s'agit d'une **étude rétrospective exploratoire, non aveugle** ; aucun modèle IA n'est utilisé. Critère conservateur : fail d'assertion sur la version fautive et pass sur la corrigée. Les expériences sont exécutées en GitHub Actions Python 3.8, jamais sur l'ordinateur utilisateur. Protocole `experiments/EXP-008A.md`, paramètres épinglés `experiments/exp008a-manifest.json`. Résultats après CI.


## EXP-008A — premier pilote comparatif sur deux vrais bugs (CI #41662325778)

**Résultat : aucune des trois politiques préenregistrées n'a détecté l'un des deux défauts aux budgets 1, 3, 6 ou 12.** Les quatre jobs CI sont verts, avec **117 tests unitaires** et toutes les expériences historiques précédentes.

| Sujet | Tests réellement exécutés par version | Tests révélateurs (ancien FAIL, corrigé PASS) | Rang du seul test révélateur — lexical / aléatoire / diversité |
|---|---:|---:|---|
| youtube-dl-1 | 79 | 1 : `test_match_str` | 33 / 71 / 53 |
| tornado-1 | 47 | 1 : `test_nodelay` | 31 / 28 / 33 |

Le banc de **youtube-dl** passe totalement en version corrigée (79 PASS) et possède 78 PASS + 1 FAIL en version fautive. **Tornado** compte 46 PASS + 1 SKIP sur le correctif, contre 45 PASS + 1 SKIP + 1 FAIL sur la version fautive. **Aucune erreur d'installation, aucun test exclus silencieusement.**

L'espérance *exacte* d'un ordre uniformément aléatoire, calculée sur ces deux corpus de tailles 79 et 47 avec un test révélateur chacun, vaut **0,4072 bug détecté sur 2 au budget 12**, contre **0** pour la permutation particulière exécutée. Ce n'est pas une estimation de performance générale : seulement une probabilité combinatoire sur ces deux bancs connus.

Résultat durable : `results/exp008a-summary.json`. Données par test et politique : artefact `exp008a-real-bug-priority-raw` du [run #41662325778](https://github.com/floiaassistant-design/Le-laboratoire-ia/actions/runs/41662325778).

**Interprétation :** les tests qui révèlent les deux défauts n'ont pas été priorisés dans les 12 premiers. C'est un **résultat négatif**, pas une preuve que les trois approches ont les mêmes performances en général, ni que la diversité ne sert jamais. Les tests viennent de la révision *après le correctif* : le banc contient donc des régressions informées de la panne connue, même si nos politiques n'ont pas consulté leurs issues.

**Prochaine question :** préenregistrer un *nouveau lot* de défauts sur **au moins trois projets** et comparer également une priorisation par coût, par couverture statique ou par chemin d'appel des tests, sans réutiliser ces deux cas comme validation indépendante. Il faudra mesurer la capacité à généraliser, et pas seulement fabriquer un nouvel ordre qui met `test_match_str` ou `test_nodelay` en premier.

## EXP-008B — huit bugs historiques préenregistrés

Huit paires de commits de youtube-dl, Tornado et Cookiecutter, mêmes politiques lexical/aléatoire/diversité que dans EXP-008A, budgets 1/3/6/12. Chaque projet s'exécute dans son propre job GitHub Actions ; chaque défaut est soit évalué soit déclaré bloqué, jamais effacé du total. Tests tirés des révisions après correctif : étude rétrospective, non aveugle. Aucun agent IA ni API facturée. Protocole : experiments/EXP-008B.md ; résultats à confirmer après exécution.


## EXP-008B — résultats vérifiés (GitHub Actions #41690471790)

**Les huit défauts préenregistrés ont été exécutés, sans cas bloqué** : trois youtube-dl, trois Tornado, deux Cookiecutter. CI intégralement verte (**7 jobs**, **135 tests unitaires** découverts et réussis). Les suites de test de la révision corrigée, rejouées sur les deux versions, totalisent **402 identifiants de test par version** sur l'ensemble des huit cas.

| Défaut historique | Tests collectés | Tests révélateurs (ancien FAIL assertion / nouveau PASS) | Premier rang lexical / aléatoire fixe / diversité |
|---|---:|---:|---|
| youtube-dl-2 | 9 | 1 | 9 / 7 / 9 |
| youtube-dl-3 | 76 | 1 | 63 / 63 / 62 |
| youtube-dl-4 | 12 | 0 | — / — / — |
| tornado-2 | 52 | 0 | — / — / — |
| tornado-3 | 48 | 0 | — / — / — |
| tornado-4 | 184 | 2 | 129 / 78 / 19 |
| cookiecutter-1 | 11 | 0 | — / — / — |
| cookiecutter-2 | 10 | 2 | 2 / 2 / 7 |

**Détection aux budgets préenregistrés (sur 8 cas, dont 4 avec au moins un test strictement révélateur) :**

| Budget | Lexical | Aléatoire (une graine fixe) | Diversité | Espérance d'un ordre uniformément aléatoire |
|---:|---:|---:|---:|---:|
| 1 | 0 | 0 | 0 | 0,335 |
| 3 | 1 | 1 | 0 | 0,939 |
| 6 | 1 | 1 | 0 | 1,677 |
| 12 | 2 | 2 | 2 | 2,284 |

L'espérance aléatoire est **une moyenne mathématique conditionnelle**, pas un résultat de répétitions indépendantes. Les suites de 9, 10 et 11 tests sont intégralement couvertes quand le budget demandé vaut 12. Les quatre défauts sans test révélateur ne sont **pas** des échecs de setup : seul notre critère de détection primaire ne montre pas de différence FAIL/PASS exploitable dans le fichier de tests sélectionné.

**Conclusion négative nuancée :** à budget 12 aucune stratégie ne se distingue ; à budgets 3 et 6, l'ordre lexical et le tirage aléatoire fixé trouvent un bug, la diversité aucun. Mais **8 défauts corrélés par projet ne démontrent pas la supériorité** d'une méthode. Sur Tornado-4, la diversité classe son premier test révélateur en position 19 au lieu de 129 (lexical) ou 78 (aléatoire) : intéressant pour préparer une *autre* hypothèse, mais hors budget déclaré ; ne pas réinterpréter l'expérience après coup.

Les trois rapports **intégraux par test et par version** sont archivés pour 30 jours en artefacts \`exp008b-youtube-dl-raw\`, \`exp008b-tornado-raw\`, \`exp008b-cookiecutter-raw\` du [run #41690471790](https://github.com/floiaassistant-design/Le-laboratoire-ia/actions/runs/41690471790). Résumé durable : \`results/exp008b-summary.json\`. Le code des politiques d'EXP-008A **n'a pas été modifié**.

**Limite décisive :** ce sont des bugs **historiques et connus**, comparés avec des tests post-correctif. Il n'y a **aucune découverte de bug inédit**, ni validation aveugle, ni démonstration qu'une IA améliore la sélection. Aucune API facturée ni aucun modèle supplémentaire n'a été utilisé.

**Prochaine étape :** auditer les quatre cas sans témoin d'assertion, puis construire un protocole séparé et figé sur de **nouveaux bugs** avec un oracle plus complet (sans transformer artificiellement les erreurs d'environnement en vrais défauts). Ne pas choisir un ordre à partir des rangs observés ici puis prétendre l'évaluer indépendamment sur ces huit cas.

## EXP-009A — audit du banc d'oracles

Trois des quatre cas sans témoin d'assertion dans EXP-008B présentent en fait une transition ERROR (ancien) -> PASS (corrigé) : youtube-dl-4, tornado-2 et cookiecutter-1. Le quatrième, tornado-3, conserve PASS des deux côtés. Ces ERROR sont des signaux non attribués, **pas des bugs automatiquement prouvés**. Les anciens scores restent inchangés. Protocole : experiments/EXP-009A.md ; résultat permanent : results/exp009a-oracle-audit.json ; vérificateur de statuts sans rescoring : lab.oracle_audit.
