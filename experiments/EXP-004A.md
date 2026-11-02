# EXP-004A — étalonnage externe QuixBugs

Date : 2 novembre 2026.

### Objectif
Tester la chaîne d'évaluation sur des programmes défectueux créés indépendamment de notre laboratoire. Vingt programmes non-graphes de QuixBugs (https://github.com/jkoppel/QuixBugs) sont copiés sans modification à partir du commit épinglé : `4257f44b0ff1181dedaedee6a447e133219fcebf`.

### Mesure et règles
- Charger, pour chaque programme, sa version corrigée, sa version défectueuse et **toutes** les lignes de `json_testcases`.
- Un cas n'est admissible que si le programme corrigé renvoie la valeur attendue. Sinon le déclarer exclu, sans masquer cet échec.
- Pour les cas admissibles, compter les discordances de sortie, exceptions ou dépassements du délai côté version défectueuse.
- Rapport primaire : nombre de **programmes distincts** ayant au moins un cas qui expose le défaut, sur le nombre de programmes évaluables.
- Rapport secondaire : nombre de cas valides, invalides, et cas exposant un défaut. Les cas d'un même programme ne sont pas indépendants.
- Isolation : un sous-processus par programme, limite globale 15 s ; limite de 250 ms par appel Python.
- Aucun appel modèle/agent, aucune API facturée, aucun réglage de la politique hybride sur les données externes.

### Limites
Les fixtures QuixBugs sont conçues pour exposer les défauts connus ; leur pouvoir de détection peut être artificiellement élevé. Les programmes n'ont pas tous les mêmes domaines, et une exception du code défectueux ne prouve pas toujours une erreur métier si l'oracle n'est pas valide (raison de l'exclusion préalable). Cette étape est une calibration de faisabilité **et non une validation d'une politique de tests**.

### Suite EXP-004B
Figurer au préalable des générateurs d'entrées valides et indépendants de l'emplacement du bogue, et comparer 12 tests aléatoires, 12 ciblés et 3 ciblés + 9 aléatoires sur ces 20 programmes. Mesurer chaque programme une seule fois pour la mesure principale, inclure les échecs et rapporter la variance entre programmes. Aucun ajustement de politique autorisé sur le lot final.

### Correction de l'infrastructure
Un contrôle GitHub a révélé que l'ancienne commande `python -m unittest discover -v` affichait un succès en exécutant **zéro test** (dossier de tests non reconnu). La CI utilise désormais `discover -s tests` et vérifie qu'au moins 16 cas ont été découverts. L'itérateur de référence `flatten` est converti en liste avant comparaison, conformément à la spécification du benchmark.
