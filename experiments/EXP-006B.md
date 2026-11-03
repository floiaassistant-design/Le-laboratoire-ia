# EXP-006B — vérification préalable d'un second corpus réel (sans scoring)

**Statut : qualification de sources et de métadonnées, pas reproduction d'erreurs.**

## Pourquoi ne pas lancer directement 149 bugs ?

EXP-004A à EXP-006A étudient des défauts QuixBugs déjà connus. Il serait trompeur d'appeler les nouveaux calculs sur ces défauts une « validation indépendante ». Le laboratoire doit d'abord qualifier des projets réels en conservant les versions fautive/corrigée, les contraintes de licence, le système de tests et les dépendances historiques.

## Sources inspectées le 3 novembre 2026

| Corpus | Identifiant figé | Observations |
|---|---|---|
| [BugsInPy](https://github.com/soarsmu/BugsInPy) | `11c5f1eea954a42132cfd06bf257766a7963e0fd` | Métadonnées `projects/<projet>/bugs/<numéro>/bug.info`, commits source fixés, scripts de test et setup ; **aucune licence racine explicite** trouvée. |
| [PyBugHive](https://github.com/pybughive/pybughive) | `b62d56c19395c31eda9b9071ed6ad79cbf07f990` | README annonce 149 bugs réels sur 11 projets. La racine du dépôt ne contient pas de fichier LICENSE et l'API GitHub ne déclare pas de licence. Le `setup.py` mentionne « BSD », **insuffisant** pour établir les droits de redistribution de tout le dataset. |
| [PySnooper](https://github.com/cool-RR/PySnooper) | Deux paires de commits précis ci-dessous | Projet tiers à licence MIT, vérifiée dans les sources historiques. Les deux cas viennent du **même projet**, donc ils ne couvrent pas deux projets indépendants. |

L'absence d'une licence à la racine **ne prouve pas** une interdiction générale de réutilisation, mais la redistribution ne doit pas être présumée autorisée. Le laboratoire **n'embarque aucune copie** du code ou des tests BugsInPy/PyBugHive.

## Échantillon préenregistré avant exécution

Les dossiers `PySnooper/bugs/1` et `PySnooper/bugs/3` ont été choisis sur la base de métadonnées publiques (commits directs et taille du projet), sans examen des scores d'algorithmes. Détails épinglés dans `experiments/exp006b-manifest.json`.

- **PySnooper-1 :** fautif `e21a31162f4c54be693d8ca8260e42393b39abd3`, corrigé `56f22f8ffe1c6b2be4d2cf3ad1987fdb66113da2`. Régression `tests/test_chinese.py::test_chinese`, test présent dans le commit corrigé, mais absent du fautif : **il faudra réfléchir à comment rejouer le test du commit corrigé sur la version fautive**. Le test corrigé importe `python_toolbox`.
- **PySnooper-3 :** fautif `6e3d797be3fa0a746fb5b1b7c7fea78eb926c208`, corrigé `15555ed760000b049aff8fecc79d29339c1224c3`. Régression `tests/test_pysnooper.py::test_file_output` ; dépendances de test historiques à qualifier. Les fiches indiquent Python 3.8.1, contre Python 3.11 actuellement sur GitHub Actions.

Des fichiers `PySnooper-pass.txt` peuvent avoir des listes de bugs numérotées différemment du sous-dossier courant : **se fier aux fichiers `bug.info` de la révision figée**, pas aux agrégats historiques.

## Vérifications automatiques

Le module `lab.external_corpus_preflight` :

1. Refuse les SHA non figés, les tests à chemin dangereux, les duplications et les affirmations de licence ou de reproduction non établies.
2. En mode en ligne (uniquement GitHub Actions), lit l'API publique GitHub pour vérifier que le commit corrigé a **exactement le commit fautif comme parent**, confirme la licence MIT historique et l'existence du test de régression dans le commit corrigé.
3. Produit un JSON versionnable de résultats de qualification. **Ne fait ni checkout, ni pip install, ni exécution des scripts provenant des projets tiers.** Aucun « bug reproduit » n'est comptabilisé.
4. Archive le JSON brut dans GitHub Actions. Toute source inaccessible ou discordante fait échouer la CI au lieu de produire une réussite fictive.

## Critères pour passer au benchmark réel

Le fait que les métadonnées soient accessibles **ne suffit pas**. Il faut ensuite installer une version compatible de Python dans un environnement isolé, comprendre le rôle du test du correctif et ses dépendances, vérifier les transitions buggy FAIL / fixed PASS, et identifier un ensemble de tests comparables. La politique de sélection de test sera gelée **avant de voir les résultats de scoring**. Les 2 cas actuels ne fournissent aucune preuve de généralisation.

## Reproduction

```bash
python -m unittest discover -s tests -v
python -m lab.external_corpus_preflight --offline
python -m lab.external_corpus_preflight --online
```

L'exécution en ligne nécessite une connexion réseau publique et ne se fait automatiquement que sur PR/push. Aucun modèle local, aucune API commerciale et aucune automatisation planifiée.


## Épreuve de reproductibilité réelle, séparée du scoring

Un **deuxième job GitHub Actions** sur Python 3.8 tente de vérifier le bug Unicode PySnooper-1 : récupérer le projet PySnooper directement depuis son dépôt MIT, replacer successivement les deux commits figés, et exécuter **notre propre mini-probe**, sous une locale ASCII explicite. L'attente est un `UnicodeEncodeError` précis dans la version fautive et un passage réussi dans la version corrigée. Une erreur d'import, une panne réseau ou un échec commun aux deux commits **ne sont pas comptés comme reproduction**.

Cette épreuve **ne réutilise pas** le test officiel de BugsInPy, ne copie pas le code source de PySnooper dans notre dépôt et n'installe pas les dépendances historiques. C'est une **calibration d'exécution sur un seul bogue connu**, pas une évaluation aveugle et encore moins une amélioration de nos politiques de sélection.

La CI doit être entièrement verte ; si cette calibration échoue, publier et examiner la raison, sans fusionner une PR rouge.


## Résultat confirmé EXP-006B — source et premier bug réel

La [CI de la PR n° 12, exécution n° 41601918091](https://github.com/floiaassistant-design/Le-laboratoire-ia/actions/runs/41601918091) est **entièrement réussie**, avec **61 tests unitaires**. Deux paires de commits PySnooper (issues de BugsInPy) ont été qualifiées par métadonnées : leur relation directe fautif → corrigé, les tests historiques présents dans le correctif et la licence MIT ont été vérifiés.

**Une véritable reproduction** a ensuite été effectuée en Python **3.8.18** sur Ubuntu 22.04, sans `pip install` ni scripts setup tiers : sur PySnooper-1, sous une locale ASCII contrôlée, la version fautive `e21a3116...` provoque précisément un `UnicodeEncodeError`, tandis que le correctif `56f22f8f...` réussit à écrire les caractères Unicode. Un mini-test autonome basé sur le symptôme connu a servi à cette calibration : **ce n'est pas** le test officiel BugsInPy et **ce n'est pas** un test indépendant découvert par un agent.

Résultat machine conservé dans `results/exp006b-summary.json`, détails du précontrôle et du bug dans les artefacts `exp006b-corpus-preflight` et `exp006b-realbug-smoke` de la CI. Le résultat couvre **un bug connu**, sur un projet, et ne démontre aucune amélioration de nos stratégies de priorisation. Le second cas est **seulement qualifié**, pas reproduit. Les licences des corpus BugsInPy et PyBugHive ne sont pas établies pour une éventuelle redistribution.

### Suite scientifique

Préparer une reproduction fiable d'un deuxième défaut dans un projet **distinct**, puis définir une interface de test homogène et un véritable lot de validation sans voir les résultats des bugs avant de geler les méthodes. Ne pas confondre test de calibration du bug déjà connu avec mesure de performance de la nouvelle politique.
