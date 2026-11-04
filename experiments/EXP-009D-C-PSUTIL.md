# EXP-009D-C — versions alternatives de psutil (sonde post hoc)

**Nature : étude de compatibilité environnementale exploratoire,
explicitement post hoc.** Elle fait suite au blocage initial de
\`psutil==5.6.7\` sous Linux/Python 3.7. Ce nouveau protocole est
figé **avant les observations sur les versions alternatives**.
Il ne remplace ni EXP-009D ni EXP-009D-B et ne mesure aucun bug.

## Hypothèse et plan conservé

Trois versions sont préchoisies selon leur ordre chronologique :
\`psutil==5.7.3\` (2020), \`psutil==5.8.0\` (2020),
\`psutil==5.9.8\` (2024). Les trois sont testées individuellement,
dans cet ordre, par \`pip download --only-binary=:all: --no-deps\`.

**Règle de sélection avant résultat** : prendre la *première* version
dans la liste ordonnée dont la roue binaire est téléchargée dans
l'environnement Python 3.7 du job ; si aucune ne fonctionne, déclarer
le blocage sans chercher à le cacher. La version choisie est alors
soumise à une seconde sonde de téléchargement binaire avec
\`pyte==0.8.0\`, \`pytest==5.4.3\`, \`pexpect==4.8.0\` (cette fois en
résolvant les dépendances transitives). Tous les échecs et les autres
versions sondées restent visibles.

## Contention et limites

- Aucun paquet n'est installé ; seul le téléchargement de roues PyPI
  (aucun sdist, aucun build) est autorisé.
- Pas d'import ni d'exécution des tests du projet TheFuck. Pas de
  secrets transmis à pip, pas de logs bruts vers les artefacts.
- Les trois cas \`thefuck-1/2/3\` restent dans le dénominateur de
  l'étude précédente ; **les comptes originaux sont inchangés**.
- Les versions candidates sont **postérieures au logiciel historique**.
  Une disponibilité ou résolution réussie ne signifie pas que ces
  versions de psutil sont sémantiquement équivalentes à la version
  historiquement attendue. Il faudra documenter et contrôler ce risque
  avant une véritable reproduction de bugs.

Ce protocole ne permet pas un score primaire ou secondaire,
ne valide aucun nouvel algorithme ou agent et ne fournit aucun
holdout aveugle. Les résultats négatifs ne seront pas retirés.
Les critères et l'ordre figurent dans
\`experiments/exp009d-c-psutil-candidates.json\`.
