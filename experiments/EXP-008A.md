# EXP-008A — premier pilote comparatif sur des bugs réels

**Hypothèse, choix des cas, budgets, politique et règles de scoring enregistrés avant toute exécution.**

## Hypothèse exploratoire

La priorisation par **diversité structurelle statique** des méthodes de test (AST + mots des identifiants) pourrait révéler des défauts réels plus vite que l'ordre lexical ou un ordre aléatoire, **sans consulter leurs résultats**.

Il s'agit d'une question testable, **pas** d'une innovation revendiquée : la diversification par Jaccard et la stratégie farthest-first sont connues.

## Deux nouveaux projets réels (pas les deux calibrations précédentes)

| Sujet | Source upstream | Defect avant -> après | Tests |
|---|---|---|---|
| youtube-dl bug 1 | [ytdl-org/youtube-dl](https://github.com/ytdl-org/youtube-dl), licence Unlicense | `99036a1298089068dcf80c0985bfcc3f8c24f281` -> `1cc47c667419e0eadc0a6989256ab7b276852adf` | `test/test_utils.py` |
| Tornado bug 1 | [tornadoweb/tornado](https://github.com/tornadoweb/tornado), licence Apache-2.0 | `6a5a0bfa370b6c0d3dbbf9589a560a98202d2baa` -> `4677c54cc18bbfbdf0f4dadf11610fab6203fd63` | `tornado/test/websocket_test.py` |

Identifiants des bugs extraits des métadonnées BugsInPy (révision `11c5f1eea954a42132cfd06bf257766a7963e0fd`), mais **aucun code du benchmark BugsInPy n'est recopié**. Les licences sont vérifiées dans les projets upstream. Les deux bugs déjà examinés (PySnooper-1 et tqdm-1) sont **exclus**.

## Protocole figé — budgets 1, 3, 6, 12

1. Cloner chaque projet upstream en CI et construire des **worktrees distincts** de la version défectueuse et corrigée, aux SHA précis. Python 3.8 sur Ubuntu 22.04. Ne pas lancer d'installations ou de scripts setup tiers.
2. Garder **exactement le même fichier de tests issus de la révision corrigée** dans les deux worktrees (copie dans un répertoire temporaire, aucune modification des commits Git). C'est une *suite rétrospective post-correctif*, capable de contenir un nouveau test de régression construit en connaissant le bug. La sélection des cas par les politiques n'a pas connaissance des résultats, **mais la création initiale de la suite n'est pas aveugle**.
3. Charger les tests du seul module indiqué via `unittest`. Exiger les **mêmes identifiants** des deux côtés, au moins 12 tests, et aucune erreur de collecte. Cette étape importe et exécute le code de niveau module ; ne pas l'effectuer hors runner isolé.
4. Exécuter les méthodes **une fois par version**, avec gestion des fixtures `unittest`. Statuts individuels `PASS`, `FAIL`, `ERROR`, `SKIP`, `XFAIL`. Toute erreur d'installation/collecte fait échouer la CI ; les tests incapables de passer sur la version corrigée sont conservés, non comptés comme révélateurs.
5. **Détection conservatrice :** *le même identifiant* passe sur la version corrigée et échoue avec une **assertion** sur la fautive. Les exceptions de la version fautive sont rapportées séparément, sans les compter automatiquement comme bugs (elles peuvent venir de l'environnement). Un seul indicateur booléen par bug et budget.
6. Trois politiques déterministes, définies avant scoring : `lexical` (ordre des identifiants triés), `seeded_random` (permutation uniforme graine **20261103 + indice de projet**), `structural_diversity` (distance Jaccard entre tokens de noms et marqueurs AST, cas le plus atypique initialement, puis farthest-first, égalités départagées alphabétiquement).
7. Ne pas ajuster ces politiques après observation des résultats. Pour comparaison additionnelle, calculer l'**espérance combinatoire exacte** d'une permutation uniforme sur le nombre de tests révélateurs. Réutiliser les mêmes statuts observés pour les différents ordres : cela suppose une exécution déterministe, non démontrée.
8. Publier les détections aux budgets 1/3/6/12, le nombre de tests du banc et les statuts par version, y compris si **zéro bug** est révélé. Un sujet mal installé ou une collecte incompatible fait échouer la CI et reçoit une raison explicite, jamais un score implicite de zéro.

## Limites scientifiques importantes

- Deux défauts historiques **déjà corrigés** sur deux projets ne démontrent aucune supériorité générale, ni une découverte inconnue, ni une nouvelle innovation.
- L'usage des **tests après correctif** favorise la présence d'un test explicitement ajouté pour reproduire le bug. L'ordre est choisi sans résultat, mais le **banc de tests n'est pas indépendant** de la connaissance du défaut.
- Les mesures de budget sont des lectures *post hoc* des mêmes exécutions, pas des expériences de latence indépendantes.
- Chaque suite s'exécute sous un seul processus Python par version ; les tests peuvent partager de l'état malgré les fixtures, ce qui peut perturber la comparaison.
- Python historique des projets : **3.7.0**, runner pratique : **3.8.x** ; cette différence doit être rappelée.
- Les deux cas précédemment calibrés ne sont pas inclus, mais les politiques restent issues d'expériences précédentes sur QuixBugs. **Ne pas appeler cela une validation aveugle**.
- Le projet n'est pas encore un groupe autonome d'agents IA : tout repose sur Python et ChatGPT en sessions ponctuelles.

## Mesures et sécurité

Le runner GitHub Actions n'a que `contents:read`, ne conserve pas les identifiants Git, travaille dans des répertoires éphémères, dispose de bornes de temps et n'installe pas de dépendances tierces. **Il exécute néanmoins du code historique externe**, qui doit être considéré comme non fiable. Ne pas utiliser sur l'ordinateur de l'utilisateur.

## Reproduction

```sh
python -m unittest discover -s tests -v
# Avec Git + réseau et Python 3.8, uniquement dans l'Action isolée :
python -m lab.real_bug_priority --output results/exp008a-real-priority.json
```

Les données brutes sont conservées en artefact CI et le résumé rédigé sera versionné, même si l'expérience est négative.
