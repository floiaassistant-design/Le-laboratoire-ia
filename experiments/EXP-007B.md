# EXP-007B — comparer les identifiants AST à la collecte effective unittest

## Protocole enregistré avant le premier run CI

Suite directe de l'expérience EXP-007A, où le nombre de **90 définitions AST** égalait le nombre de **90 tests `unittest`** exécutés dans le laboratoire, sans preuve que ce soient les *mêmes* tests. La question EXP-007B est donc : **l'identité exacte de chaque candidat statique correspond-elle à l'identité de chacun des tests collectés par unittest sur notre propre dépôt ?**

### Méthode

1. Réutiliser **sans changement** le scanner AST `lab.real_test_inventory` : retourner les identifiants `tests/chemin.py::Classe::test_methode`, sans lire les résultats d'exécution.
2. Charger la suite de tests avec `unittest.TestLoader().discover(start_dir="tests", top_level_dir=racine)` dans un **processus GitHub Actions distinct** de l'exécution des méthodes de test. L'outil **n'appelle jamais** `suite.run()` ni `TestCase.run()`.
3. Parcourir les objets `TestCase` du `TestSuite` et traduire leurs identifiants de module, classe et méthode vers le même format de chemin que l'AST. Ne pas masquer les erreurs `loader.errors`.
4. Comparer des **multiensembles** d'identifiants (avec `Counter`) : fichiers ou méthodes manquants, candidats AST non collectés, répétitions du même identifiant. Une égalité de **compte seule ne suffit plus**. Faire échouer la CI si une identité diverge.
5. Enregistrer le JSON des identifiants manquants, des candidats surnuméraires et les empreintes SHA-256 ordonnées, puis publier des résultats qu'ils soient positifs ou négatifs.
6. Ajouter des tests unitaires **sans import tiers** couvrant le faux succès d'égalité de compte, les doublons, les méthodes héritées ou fonctions pytest (en tant que cas synthétiques de divergence), et le fait que parcourir une suite ne lance aucun test.

### Limites et sécurité

- **La collecte unittest n'est PAS une lecture passive** : `discover` importe les modules de tests et peut exécuter leurs instructions globales, leurs hooks `load_tests` et toute logique d'import. Pour cette raison, on la limite à notre propre dépôt de confiance ; le drapeau `--allow-imports` est obligatoire.
- Ce mécanisme ne doit jamais être lancé tel quel sur du code tiers inconnu ou dans un environnement possédant des secrets. Une étape future devra prévoir un environnement isolé et des permissions minimales avant d'inspecter des dépôts externes.
- Le scanner AST et le collecteur `unittest` peuvent **légitimement différer** : fonctions pytest non chargées par unittest, cas de classe hérités, paramétrisation, génération dynamique, plugins, `load_tests`. Sur ces jeux, il faut **signaler les divergences** au lieu de les faire disparaître.
- Les deux bugs historiques PySnooper/tqdm ne sont pas considérés comme un corpus indépendant de validation. EXP-007B ne charge aucune version défectueuse pour scoring, n'exécute aucun test collecté et ne démontre aucune politique de priorisation.
- Ce n'est pas une expérience d'agents IA. Aucune API facturée, aucun modèle local, aucune tâche planifiée.

### Exécution autorisée uniquement sur le dépôt local de confiance

```bash
python -m unittest discover -s tests -v
python -m lab.real_test_collector --root . --scan-dir tests --allow-imports --verify-exact
```

La CI conserve les résultats bruts `results/exp007b-identity-report.json` en artefact ; la synthèse est versionnée après vérification.


## EXP-007B — résultat vérifié, identité des tests (CI #41650099193)

Sur **notre suite de tests interne**, l'inventaire AST a produit **104 identifiants**, et `unittest discover` a réellement collecté **104 objets TestCase**. La comparaison des **multiensembles d'identifiants exacts** a donné **104/104 correspondances**, **0 candidat uniquement statique**, **0 test uniquement runtime**, **0 erreur d'import/collecte**. Les **104 tests unitaires ont réussi**, tout comme les trois jobs de GitHub Actions (y compris PySnooper et les trois répétitions tqdm). Résultat synthétique : `results/exp007b-summary.json` ; sortie complète de comparaison : artefact `exp007b-identity-raw` du [run #41650099193](https://github.com/floiaassistant-design/Le-laboratoire-ia/actions/runs/41650099193).

Cette étape améliore la précédente : les identifiants **correspondent individuellement**, ce n'est plus seulement une égalité de nombre. Mais la vérification est limitée **à notre dépôt de confiance**. La collecte `unittest` a importé les modules de tests, pouvant exécuter du code de niveau module ou des hooks `load_tests` ; le programme comparateur n'a appelé **aucune méthode de test**. La CI, elle, exécute séparément les tests unitaires habituels.

**0 défaut testé pour performance, 0 politique comparée, 0 agent IA évalué.** Les suites pytest, paramètres dynamiques, plugins et héritages ne sont pas encore qualifiés. Prochaine tâche : mettre en place l'isolation pour un vrai corpus tiers et comparer les inventaires dans cette isolation, *sans consulter les résultats de bugs*, avant toute étude de performance.
