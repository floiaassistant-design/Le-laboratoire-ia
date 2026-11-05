# EXP-012 — pilote exploratoire du solveur GPT-6 en conversation unique

## Préenregistrement avant les réponses

L'issue [#45](https://github.com/floiaassistant-design/Le-laboratoire-ia/issues/45)
précise le cadre. Objectif : mesurer une **première calibration non comparative**
avec le modèle ChatGPT utilisé dans le dialogue de travail, sans API.
C'est **distinct** des 64 essais EXP-011 : aucune revendication de
comparaison des routes `single`, `parallel`, `review` ou `adaptive`.

### Cohorte et règle de passage figées

- Source officielle GSM8K MIT : `openai/grade-school-math`,
  révision `3101c7d5072418e28b9008a6636bde82a006892c`,
  blob Git `e4c2ff4942b9a78bd74f04141224c11e28d12dc9`.
- Seulement les quatre indices de **calibration** EXP-011 :
  `13, 37, 59, 81` (base zéro), dans cet ordre.
- Les douze indices d'évaluation EXP-011 ne sont PAS ouverts par ce pilote.
- Le même modèle répond une fois par question, sous forme
  `FINAL: <integer or decimal>` ; chaque réponse est figée avant
  consultation de l'oracle; pas d'outil calculateur/recherche pour résoudre.
- L'agent ne reçoit que les champs `question`, jamais `answer`.
  La lecture technique du corpus s'effectue dans un outil qui
  filtre les champs avant affichage.
- Une réponse incorrecte ou invalide reste dans le dénominateur 4.
  Le score est calculé uniquement après consignation des quatre réponses,
  par comparaison numérique avec les quatre champs `answer` épinglés.
  Le calcul de score ne renvoie pas les solutions au modèle solveur.

### Provenance et limites

L'observation est **auto-déclarée** par l'assistant dans une **même
conversation ChatGPT** : pas de transcript serveur attesté, de nouvelle
instance de modèle, de contexte frais ou de paramètres API contrôlés.
Le modèle peut connaître GSM8K par apprentissage préalable ; la
conversation courante contient la méthodologie. Ce pilote est un
indicateur exploratoire de capacité de résolution arithmétique,
**pas une preuve de performance comparative, d'indépendance ou
d'innovation de l'orchestration**.

Les appels de rôle et les coûts en tokens ne sont pas estimés comme
des chiffres réels mesurés. Aucune API payante ou exécution de modèle
local, aucun code de projets tiers.

Les scores EXP-008B/009E et le protocole EXP-011 restent inchangés.
Toutes les réponses brutes et tous les échecs doivent être conservés,
sans sélection post hoc. Les réponses du solveur seront enregistrées
dans `results/exp012-calibration-observations.json`; l'oracle sera
consulté seulement après cet enregistrement.


## Observation gelée puis score

Les quatre réponses ont été consignées **avant de lire les oracles**
dans `results/exp012-calibration-observations.json`, commit
`6611afa785417c87cc6985929da71f47c645fe61`.

La consultation ultérieure des quatre lignes officielles au blob Git
`e4c2ff4942b9a78bd74f04141224c11e28d12dc9` a donné **4/4**,
sans réponse absente ni malformée. Le rapport initial a été versionné
dans `results/exp012-calibration-score.json`. La vérification des
**quatre lignes** a été réalisée par le connecteur GitHub et ne vaut pas
vérification de la copie du fichier complet : un workflow CI
`exp012-calibration-verification` effectue cette vérification
supplémentaire par `lab.exp012_calibration` et compare les statistiques
au rapport enregistré. Ne pas présumer ce workflow vert avant lecture
de son résultat.

Commande entièrement hors réseau après téléchargement contrôlé de la
source au commit prévu :

```bash
python -m lab.exp012_calibration \
  --source test.jsonl \
  --observations results/exp012-calibration-observations.json \
  --report /tmp/exp012-rescore.json
```

Le score n'établit pas la valeur de l'architecture multi-agent :
seulement **quatre questions de calibration connues sur quatre**
dans une conversation non isolée. Aucune précision comparative,
aucune mesure de coût et aucun résultat sur les douze tâches
de validation.
