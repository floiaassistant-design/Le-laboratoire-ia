# État du laboratoire IA

## REPRISE IMMÉDIATE — pour un autre agent (état vérifié le 4 novembre 2026)

> **Cette section prime sur les anciennes rubriques « prochaine étape » ci-dessous**, qui constituent un journal historique. Ne pas supposer que les derniers messages d'une conversation sont plus récents que GitHub : vérifier l'état du dépôt avant toute action. Un agent ne possède pas automatiquement le contexte des chats précédents.

**Projet unique :** [\`floiaassistant-design/Le-laboratoire-ia\`](https://github.com/floiaassistant-design/Le-laboratoire-ia). Branche officielle : \`main\`. Dernier commit technique vérifié lors de cette rédaction : \`4ba1854d1fa8236e78553106eb3055371be267fe\` (PR #22, EXP-009A). **Cette empreinte n'est pas une branche à imposer : relire \`main\` au moment de la reprise.** Au contrôle du 4 novembre : **aucune PR ouverte** et [dernier run sur \`main\` #41719295541](https://github.com/floiaassistant-design/Le-laboratoire-ia/actions/runs/41719295541) entièrement vert.

### Travail accompli, à ne pas refaire

- **EXP-008A** : 2 paires de vrais bugs historiques dans 2 projets (youtube-dl et Tornado) ; à budget de 12 tests, **0/2** pour les trois ordres. Résumé : [\`results/exp008a-summary.json\`](results/exp008a-summary.json).
- **EXP-008B** : **8 paires de défauts réels historiques, 3 projets** (youtube-dl, Tornado, Cookiecutter), **8 évaluées / 0 bloquée** ; comparaison inchangée des ordres lexical, aléatoire à graine fixe et diversité de structure aux budgets 1/3/6/12. Au budget 12 : **2/8** pour chaque ordre ; seuls **4/8** cas ont au moins un test confirmant **FAIL assertion sur buggy / PASS sur fixed**. Résumé : [\`results/exp008b-summary.json\`](results/exp008b-summary.json), protocole : [\`experiments/EXP-008B.md\`](experiments/EXP-008B.md), PR #20.
- **EXP-009A terminée** (PR #22, [issue #21](https://github.com/floiaassistant-design/Le-laboratoire-ia/issues/21) clôturée). Audit **sans rescoring** des fichiers bruts d'EXP-008B : parmi 4 cas sans test strictement révélateur, **3 montrent ERROR sur buggy → PASS sur fixed** (\`youtube-dl-4\`, \`tornado-2\`, \`cookiecutter-1\`), et **1 reste PASS des deux côtés** (\`tornado-3\`). Les types/causes de ces exceptions ne sont pas encore attribués. Les chiffres d'EXP-008B restent **2/8** : ne pas transformer rétroactivement ERROR en FAIL. Résultat durable : [\`results/exp009a-oracle-audit.json\`](results/exp009a-oracle-audit.json), protocole : [\`experiments/EXP-009A.md\`](experiments/EXP-009A.md).
- **Infrastructure actuelle** : Python 3.11 pour les tests du laboratoire et Python 3.8 sur runners Ubuntu 22.04 pour les anciens programmes. Seuil CI actuel : **271 tests unitaires** ; le [workflow \`laboratory-checks\`](.github/workflows/tests.yml) exécute les tests, reproductions historiques et expériences externes. Les suites tierces s'exécutent en jobs isolés, pas sur le poste utilisateur.

### Reprise après EXP-009E fusionnée — missions #29 et #35 (4 novembre 2026)

- **EXP-009D terminé en trois protocoles distincts** : [PR #31](https://github.com/floiaassistant-design/Le-laboratoire-ia/pull/31) (Black 9 roues, FastAPI 9, HTTPie 38, TheFuck bloqué), [PR #33](https://github.com/floiaassistant-design/Le-laboratoire-ia/pull/33) (diagnostic **post hoc** : `psutil==5.6.7` bloque), et [PR #34](https://github.com/floiaassistant-design/Le-laboratoire-ia/pull/34) (alternatives **post hoc préordonnées** : 5.7.3 bloquée ; 5.8.0 et 5.9.8 téléchargeables ; 5.8.0 retenue par règle figée ; 14 roues groupées). **Les trois PR sont fusionnées**. Dernier commit de cette phase antérieure : `fd979fd821f4126e9148d4a93ecfe14f798558f4`. Les six workflows post-fusion étaient verts, dont [laboratory-checks #41807236772](https://github.com/floiaassistant-design/Le-laboratoire-ia/actions/runs/41807236772).
- **[PR #36](https://github.com/floiaassistant-design/Le-laboratoire-ia/pull/36) fusionnée / [issue #35](https://github.com/floiaassistant-design/Le-laboratoire-ia/issues/35) toujours ouverte** : analyse **AST statique** des fichiers de tests à SHA corrigé pour 12 cas, sans aucun import/exécution amont. Hypothèses métier rédigées à partir des correctifs historiques, **oracle secondaire inactif**. Première CI [#41807828816](https://github.com/floiaassistant-design/Le-laboratoire-ia/actions/runs/41807828816) : **12 cas inspectés, 0 bloqué et 448 occurrences statiques** (Black 372, FastAPI 24, HTTPie 19, TheFuck 33). Ce ne sont **pas des IDs runtime ni des observations indépendantes**. Résultats versionnés dans `results/exp009e-summary.json` et protocole `experiments/EXP-009E-TESTBANK.md`.
- **PR #36 vérifiée et fusionnée** au commit `c9a5268e1a0d19272cf7ab6788e2638822f3c764`. Sur la PR puis sur `main`, **271 tests unitaires** et **7 workflows GitHub Actions** sont verts, dont [laboratory-checks #41808619042](https://github.com/floiaassistant-design/Le-laboratoire-ia/actions/runs/41808619042) et [inventaire AST #41808619098](https://github.com/floiaassistant-design/Le-laboratoire-ia/actions/runs/41808619098). Aucun score de politique n'a été évalué sur les nouveaux 12 bugs.
- **Suites scientifiques #29 et #35** : qualifier les environnements et les dépendances, figer par bug les entrées/sorties métier, IDs runtime, l'OS et l'oracle secondaire avant tout résultat buggy/fixed. `thefuck-2` dépend du séparateur Windows PATH ; `thefuck-3` requiert Fish ou un mock strict. Garder les douze cas dans le dénominateur, y compris les blocages.

**Limites** : zéro des 12 nouveaux bugs exécuté, zéro score primaire nouveau, aucun bug inconnu découvert, aucun modèle IA évalué. EXP-008B conserve 2/8 par politique au budget 12. Pas d'API payante ni code tiers lancé sur le PC utilisateur.

### Situation actuelle et reprise — 4 novembre 2026

- **Quatre PR fusionnées dans cette séquence** : [#25](https://github.com/floiaassistant-design/Le-laboratoire-ia/pull/25) (diagnostic sans rescoring), [#26](https://github.com/floiaassistant-design/Le-laboratoire-ia/pull/26) (12 candidats), [#27](https://github.com/floiaassistant-design/Le-laboratoire-ia/pull/27) (provenance, licences et Python) et [#28](https://github.com/floiaassistant-design/Le-laboratoire-ia/pull/28) (dépendances statiques). Le dernier commit fonctionnel fusionné est `e7ee6e09734ecc3dc4af1d450a7db0bc45165dec`. Toutes les CI des PR sur leur SHA final ont été vertes. La CI post-fusion de ce dernier commit est [laboratory-checks #41801142377](https://github.com/floiaassistant-design/Le-laboratoire-ia/actions/runs/41801142377) + [sources #41801142219](https://github.com/floiaassistant-design/Le-laboratoire-ia/actions/runs/41801142219) + [diagnostics #41801142244](https://github.com/floiaassistant-design/Le-laboratoire-ia/actions/runs/41801142244) ; vérifier leurs conclusions au moment de la reprise, ne pas les supposer vertes sans lecture.
- **EXP-009B provenance : 12/12 candidats qualifiés sur les métadonnées des deux commits**, licences et fichiers de tests ; python 3.7.17/3.8.18 disponibles sur Ubuntu 22.04 mais différent des patchs historiques. Rapports durables dans `results/exp009b-source-summary.json`.
- **EXP-009C dépendances : 12/12 candidats, 21 fichiers de configuration lus en AST/JSON/TOML/texte uniquement**, 0 blocage et 0 dépendance tierce installée. Black a un lockfile historique ; FastAPI et les autres projets ont aussi des contraintes ouvertes/non exactes. Rapport durable `results/exp009c-dependency-summary.json`, détails dans les artefacts CI de la PR #28. **Ce n'est pas une qualification d'installation.** Seuil de CI : **214 tests unitaires**.
- **Prochaine mission active : [issue #29 — EXP-009D](https://github.com/floiaassistant-design/Le-laboratoire-ia/issues/29)**. Établir les environnements des 12 cas et figer les tests, les résultats métier attendus, les oracles primaires/secondaires et les règles d'exclusion **avant toute comparaison de politiques**. Éviter de regarder des sorties de bugs avant le gel de ce protocole ; rapporter toutes les incompatibilités, blocages et cas négatifs.
- **Limites non négociables** : 0 test des 12 nouveaux bugs exécuté jusqu'ici ; 0 nouveau bug découvert ; aucun agent IA évalué ; les résultats EXP-008B restent 2/8 par méthode au budget 12 ; pas de validation aveugle avec des tests de correctif ; aucun code tiers sur l'ordinateur utilisateur, pas d'API payante ni d'automatisation périodique.

### Critères toujours actifs — **EXP-009B, issue #23 ouverte**

Consulter [**issue #23 — qualifier les exceptions et préparer un oracle secondaire**](https://github.com/floiaassistant-design/Le-laboratoire-ia/issues/23) et en suivre les critères. La **mission suivante est l'issue #29** (préparation des environnements et oracles) ; se référer prioritairement à la section ci-dessus. Objectifs concrets :

1. Définir un diagnostic d'exception **borné et expurgé** : type d'exception, phase \`setup/call/teardown\`, trames de code projet seulement, pas de trace brute, chemins locaux, URL, identifiants ou secrets ; le tester d'abord sur **fixtures internes synthétiques**.
2. Qualifier **sans nouveau score primaire** les trois transitions ERROR→PASS et le comportement inchangé \`tornado-3\`. Une exception de type connu n'est **pas** automatiquement la preuve d'un défaut logiciel.
3. **Préenregistrer séparément** un oracle secondaire et la sélection d'un **nouveau lot de 12+ bugs sur 4+ projets**, avec commits, licences, règles d'exclusion, environnements et budgets fixés **avant de consulter leurs résultats**. Les exemples historiques des EXP-006/008/009 ne sont pas des holdouts vierges.
4. Publier les observations et les **résultats négatifs** sans sélectionner les seuls cas réussis. Ne pas modifier les ordres historiques pour améliorer rétrospectivement leur score.

**Important :** la qualification des sources est distincte de la future expérience de détection : les 12 candidats ne sont pas encore un corpus évalué. Relire la liste des issues et PR au moment de la reprise : si #23 est terminée, prendre l'issue suivante plutôt que relancer EXP-009B.

### Procédure sûre et reproductible de reprise

1. **Vérifier la source de vérité** : \`main\`, [PR ouvertes](https://github.com/floiaassistant-design/Le-laboratoire-ia/pulls), [issues ouvertes](https://github.com/floiaassistant-design/Le-laboratoire-ia/issues), [derniers runs GitHub Actions](https://github.com/floiaassistant-design/Le-laboratoire-ia/actions). Ne pas confondre une CI réussie sur une ancienne PR avec la CI de son dernier commit.
2. **Lire dans cet ordre** : cette section, \`README.md\`, l'issue active (#23 à ce jour), le protocole \`experiments/EXP-009A.md\`, les synthèses \`results/exp009a-oracle-audit.json\` et \`results/exp008b-summary.json\`, puis les scripts/tests concernés. Ne jamais inventer des résultats absents des fichiers.
3. **Travailler sur une branche**, documenter l'hypothèse **avant exécution**, les différences de méthode, les limites, les sources et chaque cas invalidé. Mettre à jour **cette section, les protocoles, les synthèses \`results/\` et l'issue** à chaque reprise ; ne pas effacer le journal historique. Si la mission dépasse la portée des outils, consigner le blocage.
4. **Contrôles locaux (sur code du laboratoire uniquement)** : \`python -m unittest discover -s tests -v\` et \`python -m lab.real_test_inventory --root . --scan-dir tests --require-tests\`. Les expériences externes peuvent importer/exécuter du code tiers : les lancer **exclusivement** sur GitHub Actions isolées, sans credentials persistants ni secrets ; éviter de les faire tourner sur le PC.
5. **PR puis CI** : vérifier tous les jobs du workflow, y compris ceux des trois projets, les nombres de tests effectivement découverts et les artefacts; **ne fusionner que si chaque contrôle requis est terminé et vert** sur le SHA exact de la tête de PR, puis contrôler encore \`main\` après fusion. En cas d'échec, corriger et relancer plutôt que fusionner.
6. **Transmettre à l'agent suivant** : indiquer dans \`ETAT.md\` **PR/issue**, **SHA courant**, **actions réalisées**, **résultats chiffrés**, **écarts/blocages**, **CI finale**, **prochaine étape**, et **points nécessitant un accord utilisateur**. Ne pas prétendre avoir fusionné ou terminé avant confirmation sur GitHub.

### Limites à préserver

Ce laboratoire teste **actuellement des politiques Python déterministes**, pas un système d'agents IA, et **n'a découvert aucun nouveau bug inconnu**. Les bugs des cohortes historiques étaient déjà documentés/corrigés ; les tests sont souvent issus de versions post-correctif, donc les résultats **ne sont pas une validation aveugle**. Ne jamais appeler des répétitions ou des budgets de tests « défauts indépendants ». Aucune API de modèle payante, aucun modèle local obligatoire, **pas d'automatisation périodique**, ni modification d'autres dépôts sans accord explicite. Les **artefacts GitHub Actions expirent** (rétention habituelle 30 jours) : **les fichiers de synthèse versionnés sont les traces durables**, mais ne remplacent pas toutes les données brutes.

---

**Journal historique ouvert le 2 novembre 2026** — V0.2 initiale ; les étapes ci-dessous peuvent être dépassées. Lire d'abord « REPRISE IMMÉDIATE ».

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

## EXP-007A — phase d'inventaire statique

- Création d'un inventaire de définitions de tests Python (AST pur), sans exécution, sans import ni lecture de résultats de bugs.
- Validation sur la suite de tests du laboratoire ; identifiants, métriques de structure, paramétrisations non développées.
- 16 tests unitaires spécifiques ajoutés ; seuil attendu de 90 tests ; chiffres réels à confirmer par la CI.
- Étape suivante : vérifier l'inventaire contre une collecte réelle dans un environnement isolé, puis préparer un corpus non utilisé auparavant. Pas de scoring de politiques dans cette phase.


## EXP-007A — résultats du premier inventaire statique (CI #41607357594)

Sur **nos propres fichiers `tests`**, le module a repéré **11 fichiers de tests Python**, lu les 11 avec succès, et relevé **90 définitions candidates**. Le contrôle parallèle `unittest discover` a exécuté **90 tests unitaires**, tous réussis. Aucun fichier erroné, aucune définition paramétrée non développée, aucun défaut logiciel noté, aucune politique de sélection évaluée.

Les **trois jobs** CI de la [PR #16 — run #41607357594](https://github.com/floiaassistant-design/Le-laboratoire-ia/actions/runs/41607357594) ont réussi, y compris les calibrations historiques PySnooper et tqdm. La sortie complète est archivée dans l'artefact `exp007a-inventory-raw` ; cette synthèse est versionnée dans `results/exp007a-summary.json`.

**Interprétation limitée :** 90 candidats statiques et 90 tests exécutés sur le laboratoire représentent une **égalité de compte**, pas la preuve que les 90 identifiants AST correspondent individuellement à toutes les unités de test collectées par des outils comme pytest. Le code n'a exécuté aucun fichier inspecté ; il ne couvre pas toutes les formes de paramétrisation, héritage ou génération dynamique. Le programme ne doit pas être présenté comme un agent IA ni comme un algorithme de découverte de bugs.

**Suite :** validation de l'interface d'identifiants sur une collecte isolée et comparaisons réellement aveugles sur **de nouveaux bugs et projets**, en excluant les deux défauts historiques déjà connus.

## EXP-007B — audit d'identités des tests

- Comparaison multiensemble AST versus `unittest discover` des identifiants complets, plutôt qu'égalité simple du nombre de tests.
- Le collecteur **importe** les modules du laboratoire (donc peut exécuter du code de niveau module), mais **n'exécute aucune méthode de test**. Uniquement sur le checkout local de confiance, drapeau d'autorisation explicite.
- 14 tests unitaires de contrôle supplémentaires ; seuil CI attendu 104. Résultats et éventuelles différences à publier tels quels après exécution.


## EXP-007B — résultat vérifié, identité des tests (CI #41650099193)

Sur **notre suite de tests interne**, l'inventaire AST a produit **104 identifiants**, et `unittest discover` a réellement collecté **104 objets TestCase**. La comparaison des **multiensembles d'identifiants exacts** a donné **104/104 correspondances**, **0 candidat uniquement statique**, **0 test uniquement runtime**, **0 erreur d'import/collecte**. Les **104 tests unitaires ont réussi**, tout comme les trois jobs de GitHub Actions (y compris PySnooper et les trois répétitions tqdm). Résultat synthétique : `results/exp007b-summary.json` ; sortie complète de comparaison : artefact `exp007b-identity-raw` du [run #41650099193](https://github.com/floiaassistant-design/Le-laboratoire-ia/actions/runs/41650099193).

Cette étape améliore la précédente : les identifiants **correspondent individuellement**, ce n'est plus seulement une égalité de nombre. Mais la vérification est limitée **à notre dépôt de confiance**. La collecte `unittest` a importé les modules de tests, pouvant exécuter du code de niveau module ou des hooks `load_tests` ; le programme comparateur n'a appelé **aucune méthode de test**. La CI, elle, exécute séparément les tests unitaires habituels.

**0 défaut testé pour performance, 0 politique comparée, 0 agent IA évalué.** Les suites pytest, paramètres dynamiques, plugins et héritages ne sont pas encore qualifiés. Prochaine tâche : mettre en place l'isolation pour un vrai corpus tiers et comparer les inventaires dans cette isolation, *sans consulter les résultats de bugs*, avant toute étude de performance.

## EXP-008A — première comparaison réelle (protocole figé)

- Deux projets distincts encore inutilisés comme cas de calibration : `youtube-dl-1` et `tornado-1`, commits directs fautif → correctif figés.
- Une même suite de tests **post-correctif** dans les deux versions ; tests importés/exécutés sous CI isolée, sans installation ni identifiants persistants.
- Trois ordres préenregistrés : lexical, mélange aléatoire reproductible et diversité structurelle ; budgets 1/3/6/12, détection uniquement si FAIL assertion sur ancien et PASS sur corrigé.
- 13 nouveaux tests unitaires de politique et protocole, minimum attendu **117**.
- Après CI : publier tous les chiffres, **même nuls**, en rappelant que 2 bugs connus ne constituent pas une validation indépendante.


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

## EXP-008B — lot de huit bugs fixé avant mesure

- youtube-dl (2,3,4), Tornado (2,3,4), Cookiecutter (1,2), commits fautifs/corrigés tous confirmés de parenté directe.
- Politiques d'EXP-008A réutilisées sans changement, budgets 1/3/6/12.
- Déroulement rétrospectif sur les tests issus des correctifs : jamais une validation aveugle.
- Un cas peut être évalué ou bloqué par son environnement, toujours enregistré dans le dénominateur de 8.
- 18 nouveaux tests unitaires ; seuil de contrôle 135. Les jobs externes doivent être inspectés avant toute conclusion.


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
