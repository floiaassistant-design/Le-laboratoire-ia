# EXP-011 — protocole d'évaluation manuelle sur problèmes mathématiques réels

**État au 4 novembre 2026 : protocole préenregistré, ZERO exécution d'un modèle, ZERO score scientifique.**

Le laboratoire dispose désormais d'un routeur hors ligne (EXP-010A)
et d'une évaluation simulée (EXP-010B). EXP-011 doit rendre possible
une évaluation avec un modèle réellement interrogé, sans forcer
l'utilisation d'une API payante. Il **n'automatise pas** les sessions
ChatGPT et ne prétend pas disposer de modèles indépendants.

## Corpus et provenance

Source : jeu GSM8K, dépôt officiel openai/grade-school-math,
licence MIT, commit
3101c7d5072418e28b9008a6636bde82a006892c.

- Fichier : grade_school_math/data/test.jsonl.
- Empreinte du blob Git : e4c2ff4942b9a78bd74f04141224c11e28d12dc9.
- Total du fichier : 1 319 exemples, réponses en dernière ligne #### nombre.
- Sélection figée dans exp011-gsm8k-plan.json :
  4 indices (0-based) de calibration : 13, 37, 59, 81 ;
  12 indices de comparaison : 103, 158, 202, 271, 349, 418,
  503, 611, 704, 826, 943, 1159.
- Indices décidés sans consulter les sorties d'un nouveau modèle.
  Les seuils du routeur ont également été écrits avant toute évaluation.
  La sélection n'est ni exhaustive, ni aléatoire, ni représentative.

**Important** : GSM8K est un benchmark public et largement utilisé ;
le modèle peut l'avoir vu durant son entraînement. Les 12 exemples
ne sont **pas** une validation aveugle indépendante, ni une preuve
de découverte d'une architecture nouvelle. Une prochaine étude devrait
choisir un corpus plus vaste et inédit ou réellement tenu à l'écart.

## Politique d'orchestration pré-déclarée

Comparateurs EXP-010A inchangés : always_single,
always_parallel (deux résolutions dans deux contextes séparés),
always_review (résolveur puis critique), adaptive.

Profil calculé à partir de la **question seule** :
- au moins 65 mots : incertitude 2 -> revue ;
- sinon au moins 40 mots : possibilité de deux résolutions séparées ;
- sinon solveur seul.
Budget fixe : 2 appels de rôle pour chaque tâche, toutes politiques
confondues. Aucun mécanisme n'a accès à la réponse oracle pour choisir
la route. L'ordre d'exécution des politiques doit être équilibré ou
alterné entre tâches afin de réduire un effet d'ordre. Pas de réglage
des seuils après lecture des résultats de validation.

Les rôles utilisent le même modèle et des consignes strictes :
- Solveur : réponse finale numérique uniquement, forme FINAL: 42.
- Indépendant : nouvelle conversation sans connaissance du solveur,
  même modèle / paramètres / outils.
- Critique : nouvelle conversation, reçoit la question et la seule
  réponse finale du solveur, jamais la solution oracle ; rend
  VERDICT: APPROVE ou VERDICT: REJECT.
- Deux réponses numériques identiques comptent comme consensus
  **même si elles peuvent être fausses**. Si elles diffèrent,
  l'architecture parallèle s'abstient.
- Un critique qui approuve peut lui aussi se tromper.

L'incertitude et le coût du coordinateur ne sont pas mesurés par cette
version : ce n'est pas une comparaison équitable de coût réel tant
que ces métriques ne sont pas disponibles.

## Mode opératoire sans API (à exécuter volontairement lors d'une session)

1. Télécharger manuellement le fichier test.jsonl depuis le dépôt
   officiel à la révision exacte ci-dessus.
   URL :
   https://raw.githubusercontent.com/openai/grade-school-math/3101c7d5072418e28b9008a6636bde82a006892c/grade_school_math/data/test.jsonl

2. Vérifier le protocole et préparer trois fichiers LOCAUX
   (aucun appel réseau dans le programme Python) :

       python -m lab.exp011_manual preflight
       python -m lab.exp011_manual prepare --source test.jsonl --out-dir .lab-private/exp011

   Le code vérifie l'empreinte Git du fichier et le nombre de lignes.
   questions.json ne contient que les questions, profils et routes.
   ANSWER-KEY-PRIVATE.json contient les solutions et **ne doit jamais
   être collé dans ChatGPT ni transmis avec les questions**.
   responses.json est un formulaire JSON de relevé de sessions
   **vide au départ**. Le répertoire .lab-private est ignoré par Git.

3. Pour chaque couple tâche/politique, utiliser les consignes de rôle
   du fichier questions.json. Noter les réponses strictes dans
   responses.json, avec identifiant de conversation différent pour
   chaque rôle, même modèle utilisé et état des sessions.
   Ne PAS mettre les conversations à réponse déjà connue en prétendue
   validation indépendante ; si l'absence de mémoire ne peut être
   garantie, documenter la contamination possible.
   Les champs de tokens / latence inconnus restent null : ne jamais
   entrer zéro pour faire disparaître un coût non mesuré.

4. Une fois les données récoltées, lancer :

       python -m lab.exp011_manual score --out-dir .lab-private/exp011 --report .lab-private/exp011/score.json

   Le programme distingue correct, incorrect, abstention, blocage
   de politique, session non indépendante, réponse malformée et
   essai non réalisé. Les résultats d'essais incomplets **restent
   dans le dénominateur** des 12 tâches de validation. Le mode
   calibration est rapporté séparément, sans l'utiliser comme
   preuve de supériorité.

## Contrôles, limites et interdictions

- Aucune API de modèle, abonnement supplémentaire ou installation
  tierce n'est requise pour générer le paquet et le noter.
- Le langage du benchmark est l'anglais. Limiter les variations
  de présentation / traduction des questions entre modes.
- Les identifiants de session, le modèle et les coûts rapportés
  manuellement **ne constituent pas une preuve d'indépendance**.
- Le modèle peut avoir mémorisé GSM8K ; l'évaluation pourrait aussi
  souffrir des biais d'opérateur, d'ordre et de sujets sélectionnés.
- Un échec de format n'est pas une preuve de raisonnement erroné.
- Les quotas/limites du produit ChatGPT ne sont pas équivalents à un
  plafond de tokens contrôlé d'API. Ne pas affirmer avoir comparé des
  budgets réels identiques.
- Les fichiers de travail et réponses restent privés, non committés,
  jusqu'à décision explicite de publier des résultats expurgés.
- Aucune issue EXP-009B/D/E ni aucun score historique de détection
  de bugs n'est modifié par EXP-011.
