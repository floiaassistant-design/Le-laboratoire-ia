# EXP-009D, phase 1 — faisabilité des dépendances binaires

**Préenregistrement daté du 4 novembre 2026, antérieur aux résultats de ce
nouveau contrôle.** L'objectif n'est PAS de détecter un bug : déterminer si
certaines distributions binaires Python pourraient être obtenues avec des
interpréteurs de la famille des versions historiques, afin de préparer un
environnement isolé.

## Variables fixées et quatre sondes

Source immuable : \`experiments/exp009b-candidates.json\` (12 défauts
historiques sur quatre logiciels). Sonde fixée dans
\`experiments/exp009d-wheel-feasibility.json\` :

| Logiciel | Python disponible sur runner | Versions directes exploratoires choisies *avant* le sondage |
| --- | --- | --- |
| Black | 3.8 | \`click==7.1.1\`, \`pytest==5.4.3\`, \`typed-ast==1.4.1\` |
| FastAPI | 3.8 | \`starlette==0.13.2\`, \`pydantic==1.5.1\`, \`pytest==5.4.3\` |
| HTTPie | 3.7 | \`requests==2.21.0\`, \`pygments==2.4.2\`, \`pytest==4.6.11\`, \`pytest-httpbin==0.0.7\` |
| TheFuck | 3.7 | \`psutil==5.6.7\`, \`pyte==0.8.0\`, \`pytest==5.4.3\`, \`pexpect==4.8.0\` |

Ces choix sont des **hypothèses explicites de faisabilité**, pas des
dépendances exactes prouvées par le commit historique, ni des jeux complets.
Elles peuvent être incompatibles. Les dépendances transitives ne sont pas
préverrouillées ; elles ne constituent donc pas encore un environnement
reproductible. Tout remplacement ultérieur doit être enregistré comme
nouvelle version du protocole, sans réécrire les résultats de la sonde.

## Méthode

La CI utilise GitHub Actions Ubuntu 22.04, Python 3.7 ou 3.8, permissions
\`contents:read\`, \`persist-credentials: false\`. Une invocation de
\`python -m pip download --only-binary=:all:\` télécharge les roues depuis
\`https://pypi.org/simple\` dans un répertoire temporaire, sans installation,
sans scripts de construction et sans exécution/import d'un code du logiciel
étudié. Les variables de secrets ne sont pas transmises au processus pip.

Le rapport enregistre pour chaque projet les **trois ID de défauts
concernés**, la version majeure.mineure courante, le statut, un code
de blocage expurgé, la liste complète des noms/tailles/SHA256 des
roues éventuellement obtenues et la durée. Les journaux détaillés pip
ne sont ni publiés ni archivés. Une erreur de téléchargement ne fait pas
disparaître un bug du lot, ni ne le transforme en zéro de détection.
Un job vert signifie que **le rapport complet a été produit** ; pour
savoir si la sonde a réussi, regarder son champ \`status\`.

## Règle d'inférence

Même si les quatre sondes réussissent, elles ne prouvent ni qu'une
installation serait saine ni que les tests de l'époque seraient fiables.
Les interpréteurs ne correspondent pas exactement aux patchs historiques
3.7.0 / 3.7.3 / 3.8.3. Les dépendances système (ex. shell \`fish\`),
extensions natives, extras de test, dépendances transitives et le
comportement métier restent à qualifier. **Les 12 tests historiques ne
sont pas exécutés dans cette phase.**

Pour la future évaluation, les seules baselines sont
\`lexical\`, \`seeded_random\`, \`structural_diversity\`,
graine \`20261103\`, budgets 1/3/6/12. L'oracle primaire reste
**même ID : assertion FAIL en version fautive et PASS en version corrigée**.
Un \`ERROR\` ne devient pas un succès de détection sans témoin métier
secondaire défini indépendamment **avant** tout score ; aucun oracle
secondaire n'est activé par cette sonde.

Pas de modèle IA, pas d'API payante, pas de test tiers sur la machine
personnelle, pas d'automatisation récurrente. L'expérience reste
historique, rétrospective et non aveugle.
