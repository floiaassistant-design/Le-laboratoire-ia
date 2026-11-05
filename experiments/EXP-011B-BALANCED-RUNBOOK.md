# EXP-011B — carnet de sessions manuelles équilibrées

**Nature : outil d'exécution EXP-011, sans nouveau modèle ni changement des
données préenregistrées.** Aucun appel à une IA et aucun score scientifique
ne sont produits par ce module. EXP-010A / 010B et les scores de bugs sont
inchangés.

## Hypothèse d'ingénierie

L'EXP-011 prévoyait de comparer quatre politiques sur le même jeu GSM8K,
mais demandait encore à un opérateur de gérer la succession des rôles et
l'équilibrage des politiques. Un ordre déterministe et une séparation
explicite des instructions peuvent réduire les erreurs de procédure,
**sans démontrer** qu'un agent devient plus performant.

Ce carnet organise **64 essais planifiés** (16 tâches x 4 politiques),
d'abord les quatre tâches de calibration, puis les douze d'évaluation.
Pour chaque tâche, la première politique tourne parmi
`adaptive`, `always_single`, `always_parallel`, `always_review`.
Chaque politique occupe chaque rang exactement une fois en calibration,
et trois fois en évaluation. Les tâches bloquées par la politique
préenregistrée restent dans le carnet avec **zéro appel planifié**.

## Générer le carnet sans API

Exécuter après la procédure `prepare` d'EXP-011 et en conservant le fichier
GSM8K d'origine :

```bash
python -m lab.exp011_manual prepare --source test.jsonl --out-dir .lab-private/exp011
python -m lab.exp011_runbook --source test.jsonl --out-dir .lab-private/exp011
```

Si les fichiers ont déjà été préparés, **ne pas relancer `prepare`**
(car il refuse l'écrasement) : exécuter seulement `exp011_runbook`.
Le programme relit et vérifie le corpus épinglé et les deux fichiers
`questions.json` / `ANSWER-KEY-PRIVATE.json` contre la source.
Il refuse d'écraser un ancien `manual-runbook.json`.

Le carnet ne contient que les questions, les chemins de décision déjà
figés, l'ordre des essais, les emplacements de conversations et
les modèles de messages de rôle. **La clé de réponses n'y apparaît pas.**
La clé est vérifiée en mémoire par le préparateur, mais jamais transmise
dans un prompt.

Pour chaque entrée du carnet :

1. Si la route est `blocked`, ne lancer aucun rôle, conserver ce cas
   dans les 64 enregistrements.
2. Si `single`, utiliser le message `solver` dans une nouvelle
   conversation. Si `parallel`, lancer ensuite `independent` dans
   une **autre** conversation, sans lui donner la réponse du solveur.
3. Si `review`, lancer le solveur puis une conversation distincte
   avec le texte du critique, en remplaçant
   `{{SOLVER_FINAL}}` par la réponse **finale** du solveur
   (jamais par la réponse oracle).
4. Renseigner les sorties, références de conversations et informations
   de modèle dans `responses.json`. Les marqueurs
   `planned_context_slot` du carnet sont des **identifiants de
   planification**, et ne constituent pas une preuve de conversation
   effectivement indépendante.
5. Noter seulement via la commande `score` d'EXP-011, sans changer
   la sélection ni les seuils de routage.

## Limites scientifiques à conserver

- Une rotation équilibrée n'est pas une randomisation. L'opérateur et
  le modèle peuvent dériver dans le temps ; l'ordre des tâches n'est pas
  rendu aléatoire.
- Les quatre modes n'utilisent **pas nécessairement le même nombre
  d'appels** : un blocage en consomme zéro, un solveur seul un, et
  une résolution parallèle ou une revue deux. Un budget autorisé de
  deux n'est pas deux appels effectivement effectués.
- Les contextes indépendants, l'identité de modèle, les paramètres,
  les délais et les coûts ne sont pas garantis par le carnet ni par
  l'interface utilisateur : ils restent à relever ou à qualifier
  d'inconnus.
- Le jeu GSM8K est public, petit et susceptible d'avoir figuré dans
  l'entraînement du modèle. Ne pas attribuer de causalité ou de
  supériorité à un éventuel score sans protocole plus fort.
- Aucun modèle local, API payante, déploiement ou exécution continue
  n'est utilisé. L'étude reste entièrement **manuelle**.
