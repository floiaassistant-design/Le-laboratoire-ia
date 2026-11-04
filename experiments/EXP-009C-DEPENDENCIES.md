# EXP-009C — inventaire statique des dépendances historiques

**Hypothèse et protocole fixés avant la première exécution CI :**
les 12 candidats issus des quatre nouveaux projets ne disposent pas tous
d'un environnement Python fidèlement reproductible simplement parce que
les commits, licences et tests existent. En particulier, une contrainte
\`>=\` ou une dépendance sans version n'assure pas que la version de 2026
reproduit l'installation historique.

## Sources autorisées, versions et méthode

Lire en **données uniquement** les fichiers suivants, à la révision
\`fixed\` déjà épinglée dans \`experiments/exp009b-candidates.json\` :

| Projet | Descripteurs consultés | Interpréteur disponible mais pas patch historique |
| --- | --- | --- |
| Black | \`Pipfile.lock\`, \`setup.py\` | 3.8.18, référence historique 3.8.3 |
| FastAPI | \`pyproject.toml\` | 3.8.18, référence historique 3.8.3 |
| HTTPie | \`requirements-dev.txt\`, \`setup.py\` | 3.7.17, référence historique 3.7.3 |
| TheFuck | \`requirements.txt\`, \`setup.py\` | 3.7.17, référence historique 3.7.0 |

\`lab.exp009c_dependencies\` interroge **uniquement GitHub API** avec les
dépôts et chemins allowlistés et le jeton temporaire du job read-only.
Aucun \`setup.py\`, fichier de tests ou paquet externe n'est **exécuté**.
Il utilise \`ast.parse\` / \`ast.literal_eval\` pour les seuls littéraux
de \`setup.py\`, \`tomllib\` pour la configuration FLIT, \`json\` pour le
lockfile et un comptage des contraintes des fichiers requirements.
Chaque rapport contient 3 cas, les empreintes Git des descripteurs, le nombre
de déclarations explicitement verrouillées/non verrouillées, les constructions
dynamiques repérées, les refus et leurs motifs codés. Aucun texte source,
ligne d'installation ou traceback n'est archivé.

Une construction dynamique dans \`setup.py\` ne doit pas être interprétée
ni exécutée pour compléter le rapport. Les lignes de dépendances optionnelles,
extras, markers, lockfiles spécifiques à une plateforme et contraintes
conditionnelles peuvent être partiellement observées : **l'inventaire
n'est pas un résolveur**. Les résultats sont enregistrés quels qu'ils soient,
y compris les cas inexploitables.

## Observations préliminaires non expérimentales

Lecture de la première révision corrigée de chaque projet avant ce
préenregistrement :

- Black possède un \`Pipfile.lock\` avec de nombreuses versions \`==\`,
  mais aussi des références locales et contraintes conditionnelles.
- FastAPI déclare notamment \`starlette ==0.13.2\` et une plage de versions
  \`pydantic\`, avec plusieurs dépendances de test non fixées exactement.
- HTTPie utilise un \`requirements-dev.txt\` contenant \`pytest\`,
  \`pytest-httpbin>=0.0.6\` et d'autres paquets sans version exacte ;
  son \`setup.py\` comporte des ajouts conditionnels.
- TheFuck déclare des outils de tests sans versions exactes dans
  \`requirements.txt\`.

Ces constats **ne sont pas** des échecs d'installation constatés et ne
constituent pas des scores de détection.

## Prochaine expérience, non lancée

1. Établir des jeux de versions réellement installables et isolés avec
   vérification des wheels, dépendances transitives, licences et maturité
   des archives, sans exécuter de setup externe au laboratoire.
2. Figer par cas un environnement et une politique d'exclusion **avant de
   connaître les verdicts** des 12 nouveaux bugs. Ne pas éliminer
   silencieusement les cas difficiles.
3. Définir pour chaque défaut l'entrée, la sortie métier attendue, les
   tests et l'oracle primaire/secondaire avant toute comparaison de
   politiques.
4. Lancer ensuite les tests exclusivement dans GitHub Actions avec sandbox
   et aucun secret. Les 12 bugs historiques et leurs tests post-correctif
   restent une étude rétrospective, non une validation aveugle.

Les scores d'EXP-008B restent inchangés et aucun modèle IA n'est évalué.
