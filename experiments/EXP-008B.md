# EXP-008B — huit défauts réels historiques, trois projets (protocole gelé)

**Enregistré avant toute nouvelle mesure.** Suite de l'issue [#19](https://github.com/floiaassistant-design/Le-laboratoire-ia/issues/19).

### Échantillon déclaré à l'avance

Huit couples de versions fautive/corrigée provenant des métadonnées figées du corpus BugsInPy (`11c5f1eea954a42132cfd06bf257766a7963e0fd`) : **youtube-dl bugs 2,3,4 ; Tornado bugs 2,3,4 ; Cookiecutter bugs 1,2**. Les huit identifiants de commits SHA-40, les chemins de tests et leurs interpréteurs historiques sont dans `experiments/exp008b-manifest.json`.

**Contrôle préalable effectué :** chacun des huit commits corrigés a un unique parent direct correspondant au commit fautif enregistré. Les projets upstream sont distribués sous Unlicense, Apache-2.0 et BSD-3-Clause, respectivement ; aucun code BugsInPy n'est recopié dans le laboratoire. Les deux calibrations PySnooper/tqdm et les bugs 1 de youtube-dl/Tornado déjà évalués dans EXP-008A sont exclus.

### Comparaison prévue AVANT résultat

- **Trois politiques inchangées par rapport à EXP-008A** : identifiant lexical, permutation aléatoire reproductible (graine 20261103 + indice du cas, débutant à zéro), diversification AST/Jaccard farthest-first. Réutiliser les fonctions du module EXP-008A, sans réentraîner, modifier les poids ni utiliser les patches ou sorties du programme pour ordonner.
- **Budgets identiques : 1, 3, 6, 12 tests.** Si une suite comporte moins de tests, le budget effectif est plafonné à la taille de la suite et déclaré ; aucune erreur ne doit être effacée.
- **Même fichier de tests du commit CORRIGÉ dans les deux worktrees.** Cette suite est rétrospective ; elle a pu intégrer des régressions expressément écrites pour le bug. Ne pas la présenter comme une suite aveugle.
- Collecter les identifiants `unittest` ou `pytest` et exécuter chaque banc une fois dans la version fautive et une fois dans la version corrigée. Exiger exactement **les mêmes identifiants**, et garder les statuts par test. Les `pytest.mark.parametrize` sont comptés comme tests exécutables distincts, mais gardent les caractéristiques statiques de leur définition commune.
- **Règle primaire de détection** : même test en `FAIL` par assertion sur la version fautive, `PASS` sur la corrigée. Les erreurs `ERROR` de modules, d'import, de fixture ou d'environnement ne comptent pas automatiquement comme des bogues et doivent être déclarées séparément. Si la collecte, les identifiants ou l'environnement corrigé sont erronés, le cas est noté `blocked`, **pas 0/8**.
- L'ordre aléatoire théorique est calculé exactement par `1 - C(n-d,k)/C(n,k)` en utilisant les indicateurs observés, sans confondre les répétitions et les bugs indépendants. Un seul ordre aléatoire initial fait partie de la comparaison, comme dans EXP-008A.
- **Résultats négatifs ou bloqués intégralement publiés** ; le dénominateur reste 8, même si un cas est techniquement impossible à reproduire. Résumé par politique/budget et par projet, avec nombre de cas évalués vs bloqués et temps d'exécution.

### Infrastructure et limites

- GitHub Actions séparées pour chacun des trois projets afin de limiter les durées, `ubuntu-22.04` et Python 3.8 ; chaque job possède `contents:read` et aucun credential Git persistant. Les projets upstream sont clonés temporairement ; le laboratoire n'installe pas de scripts setup tiers.
- `unittest` est utilisé sur youtube-dl et Tornado ; Cookiecutter exige un collecteur `pytest` avec **versions de dépendances figées**, dans son job isolé. L'installation des dépendances peut échouer et ce blocage doit rester documenté, sans sélectionner un autre bug opportuniste.
- Les tests tiers **s'exécutent réellement** dans la CI ; considérer ces sources anciennes comme du code non fiable, donc ne jamais les exécuter sur l'ordinateur de l'utilisateur ou dans un job avec des secrets.
- Les versions historiques indiquent Python 3.7.0 (youtube-dl/Tornado) et 3.6.9 (Cookiecutter), alors que la CI utilise Python 3.8.x pour la faisabilité. Il ne s'agit pas de reproduction parfaite de leur environnement historique.
- Une suite peut comporter de l'état partagé ou des dépendances réseau. Les budgets sont calculés après exécution, et ne prédisent pas exactement la consommation en temps réel d'une politique.
- Avec seulement 8 bogues répartis entre trois projets, **aucune généralisation statistique forte** n'est possible. Le banc post-correctif est par définition informé par les bugs déjà connus ; ne pas appeler cette étude une validation aveugle, ni une découverte de nouveaux bugs.
- Il s'agit de Python déterministe, **aucun agent IA évalué**, aucun modèle supplémentaire ni API payante.

### Critères d'acceptation

Le code d'étude doit exécuter ou enregistrer explicitement les huit cas (aucun oubli silencieux), archiver les détails par projet, faire passer les tests unitaires, et obtenir un workflow CI vert. **CI verte ne signifie pas que les huit cas ont forcément été reproduits** : lire le nombre de cas `evaluated` et `blocked` dans le résultat avant toute conclusion scientifique.
