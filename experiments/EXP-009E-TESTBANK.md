# EXP-009E — hypothèses métier et inventaire statique des tests

**Protocole avant la première inspection automatique, 4 novembre 2026.**
L'objectif est de préparer l'étude rétrospective de 12 défauts historiques
sur 4 projets, **sans exécuter leurs tests ni connaître leurs verdicts**.

La liste figée \`experiments/exp009e-semantic-hypotheses.json\` contient
douze hypothèses métier dérivées des *correctifs historiques déjà connus*
(\`bug_patch.txt\` du corpus BugsInPy au SHA
\`11c5f1eea954a42132cfd06bf257766a7963e0fd\`).
Chaque cas reste **hypothesis_only** : les entrées exactes, les sorties
attendues et les identifiants de tests runtime ne sont pas encore gelés ;
l'oracle secondaire est **désactivé**.

## Question et méthode

Pour chacun des 12 fichiers de tests préenregistrés dans
\`experiments/exp009b-candidates.json\`, récupérer seulement sa version
historique **corrigée** par GitHub API en lecture seule. Décoder
localement le contenu et l'inspecter avec \`ast.parse\`, **sans import,
install, exécution de code tiers, accès direct aux sockets, modèle IA ou
API de modèle**. Les résultats donnent :

- l'empreinte Git du fichier et le commit épinglé ;
- les fonctions/méthodes dont le nom commence par \`test_\` au premier
  niveau du module ou d'une classe ;
- les noms statiques (sans paramètres développés), le compte de
  décorateurs \`parametrize\` identifiables, les éventuels noms rejetés
  et le SHA256 de la liste canonique triée ;
- tous les cas bloqués, sans les écarter du lot fixe.

**Attention :** un nom trouvé par AST ne constitue pas un ID runtime.
Des tests générés dynamiquement, des paramètres, les hooks pytest et les
fixtures peuvent modifier les identifiants ou la population réellement
collectée. On ne revendique **aucune équivalence** avec la collection
runtime avant de la mesurer indépendamment dans un environnement
qualifié. Une nouvelle version du protocole devra être gelée avant
toute observation des résultats buggy/fixed.

## Points sensibles par projet

Black : \`fmt: on\`, options CLI et fallback multiprocessing.
FastAPI : sorties modèles Pydantic, dépendances WebSocket et
\`exclude_unset\`. HTTPie : limite de nom de fichier, redirections
et en-têtes de session. TheFuck : correction de messages pip,
**séparateur PATH dépendant de Windows** et dépendance à
**Fish shell** pour une autre correction.

Le cas \`thefuck-2\` pourrait ne pas montrer son bug sous Linux puisque
\`os.pathsep\` y vaut le séparateur déjà codé en dur ; il exige un
environnement Windows ou une simulation **préenregistrée**.
\`thefuck-3\` demande Fish ou une simulation explicite de \`Popen\`.
Ces cas restent dans le dénominateur même s'ils sont bloqués.

## Score futur : règles conservées mais non activées

- Politiques lexical, aléatoire avec graine \`20261103\` et diversité
  structurelle ; budgets 1, 3, 6, 12.
- Oracle primaire : **même ID runtime, FAIL d'assertion sur buggy et
  PASS sur fixed**.
- Un \`ERROR\` générique ne vaut pas une détection. L'oracle secondaire
  devra définir avant exécution un **témoin sémantique et sa sortie
  métier** pour chaque cas, en excluant les erreurs d'environnement.
- Cette étude est rétrospective et informée par les correctifs :
  elle n'est **pas une validation aveugle** de politiques d'agents.
  Pas de nouveaux bugs inconnus revendiqués.

L'issue [#35](https://github.com/floiaassistant-design/Le-laboratoire-ia/issues/35)
porte la suite, notamment le gel des témoins métier précis et des
conditions OS. La qualification des dépendances et environnements
reste suivie dans l'issue #29.
