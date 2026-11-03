# EXP-007A — inventaire statique de tests Python, sans scoring

**Protocole et choix techniques gelés avant le premier inventaire.** Sous-étape de l'[issue #14](https://github.com/floiaassistant-design/Le-laboratoire-ia/issues/14).

## Objectif

Un même mécanisme doit représenter les **définitions de tests** présentes dans une base Python avant toute tentative de priorisation. Cette étape ne porte ni sur la découverte d'un bug, ni sur la précision d'un algorithme : elle valide uniquement une première interface de lecture de tests, exécutée sur **nos propres fichiers**.

## Règles de l'inventaire

- Lecture **AST pure**, via `ast.parse` ; ne pas importer les modules, ne pas appeler `pytest --collect-only`, ne pas lancer les tests, ne consulter ni versions défectueuses ni correctifs.
- Scanner récursivement uniquement `test_*.py` et `*_test.py` dans le répertoire explicitement fourni (défaut : `tests`), sans suivre les liens symboliques, et exclure les environnements, dépôts cachés et `third_party`.
- Repérer les fonctions `test_*` au niveau du module et les méthodes `test_*` dans les classes dont le nom commence par `Test` ou qui dérivent *syntaxiquement* de `TestCase`. Reconnaître `async def`.
- Conserver des identifiants fixes `chemin::Classe::test_methode`, la position dans le fichier, le genre, les nombres d'assertions / appels / branches / boucles / gestionnaires de contexte / exceptions, et des marqueurs structurels bornés. **Aucun résultat FAIL/PASS, aucune variable de scoring**.
- Signaler `@pytest.mark.parametrize` mais ne **pas** le développer en cas d'exécution : une définition paramétrée peut correspondre à plusieurs tests collectés. Les tests créés dynamiquement, hérités ou générés par plugin sont hors portée.
- Limiter la lecture à **1000 fichiers** de taille maximale **512 000 octets** chacun. Reporter explicitement les fichiers non lisibles, les erreurs de syntaxe et les identifiants de tests dupliqués ; CI rouge si erreur ou inventaire vide.
- Produire un résultat JSON ordonné de façon déterministe ; archiver l'intégralité en artefact GitHub Actions, et conserver une synthèse versionnée après validation.

## Ce que l'inventaire ne prouve PAS

Une **définition de test repérée statiquement** n'est pas nécessairement collectée ni exécutable. L'inventaire peut manquer des tests provenant de fonctions imbriquées, fichiers à noms inhabituels, classes héritées ou plugins, et il peut compter des définitions dont `__test__ = False` ou une configuration de collecte les exclut. Les features structurelles et identifiants sont préparatoires : **aucune politique n'est encore entraînée, optimisée ou comparée**.

La prochaine validation à réaliser sera la concordance entre les candidats AST et des collectes de tests effectives, **dans une sandbox historique compatible** (en tenant compte du fait que la collecte pytest peut déjà exécuter des imports), puis le choix **préenregistré** de bugs vraiment indépendants. Les calibrations PySnooper/tqdm déjà examinées ne doivent jamais devenir un holdout.

## Commande reproductible (Python 3.11)

```bash
python -m unittest discover -s tests -v
python -m lab.real_test_inventory --root . --scan-dir tests --output results/exp007a-inventory.json --require-tests
```

La CI vérifie le nombre minimal de tests unitaires découverts et archive `results/exp007a-inventory.json`. **Aucun modèle supplémentaire, aucune API facturée, aucune tâche récurrente.**
