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

## EXP-005 — protocole de travail

- Statut : codage de l'analyse de permutations, vérification CI à réaliser.
- Aucun changement des entrées / générateurs d'EXP-004B : réemploi de `edge_probes`.
- Comparaison de l'ordre initial et de 256 permutations, budgets 1/3/6/12, probabilité exacte calculée à partir des erreurs détectables pour chaque programme.
- Conserver les résultats même s'ils invalident l'hypothèse, sans ajustement post hoc ; ne pas confondre permutations et défauts indépendants.

### Correction technique dans la PR #8
La première CI a exécuté les 39 tests mais un test utilisait une égalité stricte entre nombres flottants pour la probabilité `1/12`. Le calcul était correct ; l'assertion a été corrigée avec `assertAlmostEqual`, sans changer les données, les politiques ni les formules. Le run GitHub suivant doit confirmer cette correction avant toute fusion.


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

## EXP-006A — priorisation structurale

- Politique farthest-first / distance de Jaccard entièrement fondée sur la forme des entrées, sans lecture des erreurs.
- Limité aux quatre programmes pilotes, 12 cas ciblés déjà présents, budgets 1/3/6/12.
- Scores d'abord produits par la CI ; conclusion à ne pas annoncer avant vérification des logs. Toute validation indépendante sur corpus nouveau reste à faire.


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

## EXP-006B — préqualification des sources externes

- Deux candidats PySnooper issus de BugsInPy, figés à leurs SHA de commits de 2019.
- Vérification automatique en CI des liens parents fautif → correctif, test de régression fixé et licence historique MIT, **sans installer/exécuter le code tiers**.
- Corpus BugsInPy et PyBugHive non redistribués car les droits d'ensemble restent à confirmer.
- Prochaine étape après qualification : isoler Python 3.8.1 et les dépendances, reproduire au moins un FAIL/PASS, puis définir de nouvelles règles de comparaison avant scoring.


## Résultat confirmé EXP-006B — source et premier bug réel

La [CI de la PR n° 12, exécution n° 41601918091](https://github.com/floiaassistant-design/Le-laboratoire-ia/actions/runs/41601918091) est **entièrement réussie**, avec **61 tests unitaires**. Deux paires de commits PySnooper (issues de BugsInPy) ont été qualifiées par métadonnées : leur relation directe fautif → corrigé, les tests historiques présents dans le correctif et la licence MIT ont été vérifiés.

**Une véritable reproduction** a ensuite été effectuée en Python **3.8.18** sur Ubuntu 22.04, sans `pip install` ni scripts setup tiers : sur PySnooper-1, sous une locale ASCII contrôlée, la version fautive `e21a3116...` provoque précisément un `UnicodeEncodeError`, tandis que le correctif `56f22f8f...` réussit à écrire les caractères Unicode. Un mini-test autonome basé sur le symptôme connu a servi à cette calibration : **ce n'est pas** le test officiel BugsInPy et **ce n'est pas** un test indépendant découvert par un agent.

Résultat machine conservé dans `results/exp006b-summary.json`, détails du précontrôle et du bug dans les artefacts `exp006b-corpus-preflight` et `exp006b-realbug-smoke` de la CI. Le résultat couvre **un bug connu**, sur un projet, et ne démontre aucune amélioration de nos stratégies de priorisation. Le second cas est **seulement qualifié**, pas reproduit. Les licences des corpus BugsInPy et PyBugHive ne sont pas établies pour une éventuelle redistribution.

### Suite scientifique

Préparer une reproduction fiable d'un deuxième défaut dans un projet **distinct**, puis définir une interface de test homogène et un véritable lot de validation sans voir les résultats des bugs avant de geler les méthodes. Ne pas confondre test de calibration du bug déjà connu avec mesure de performance de la nouvelle politique.

## EXP-006C — qualification d'un deuxième projet réel

- Candidat : tqdm bug n° 1 de BugsInPy (`tenumerate(start)`), commit fautif `8cc777fe...`, correctif direct `c0dcf39b...`.
- Sélection sur bug connu et correctif lu : **test de calibration**, jamais démonstration d'une politique de test.
- CI indépendante Python 3.8/Ubuntu 22.04, sans install ou scripts sources, dans un clone temporaire. Deux processus doivent rendre des indices attendus distincts ; échec d'import/setup ne compte jamais comme un bug.
- Résultat à rapporter après CI, même si la reproduction échoue.
