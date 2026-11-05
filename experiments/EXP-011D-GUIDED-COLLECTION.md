# EXP-011D — collecte manuelle guidée des réponses de modèle

**Statut : implémentation expérimentale, sans appel de modèle.** Le travail a été [préenregistré dans l'issue #69](https://github.com/floiaassistant-design/Le-laboratoire-ia/issues/69) avant l'ajout du code. Il s'appuie sur le protocole inchangé [EXP-011](EXP-011-MANUAL-REAL-TASKS.md), le carnet [EXP-011B](EXP-011B-BALANCED-RUNBOOK.md) et l'audit [EXP-011C](EXP-011C-PROVENANCE-AUDIT.md).

## Pourquoi cette étape

Nous avons **64 essais prévus** sur 16 tâches GSM8K et quatre politiques, mais aucun outil du dépôt n'ouvre ni n'interroge des conversations ChatGPT distinctes. Le présent guide réduit les manipulations : un prompt à la fois, référence de conversation obligatoire, sortie préservée et contrôle des erreurs de saisie **avant** modification du fichier de suivi. Il ne peut pas vérifier que la réponse vient vraiment du modèle affiché, que les conversations sont indépendantes, que leurs mémoires sont isolées ou que les ressources consommées ont été réellement mesurées.

## Avant toute collecte

Utiliser un environnement privé et conserver le fichier officiel test.jsonl épinglé par EXP-011. Préparer le dossier **une seule fois** :

~~~bash
python -m lab.exp011_manual prepare --source test.jsonl --out-dir .lab-private/exp011
python -m lab.exp011_runbook --source test.jsonl --out-dir .lab-private/exp011
~~~

Ne pas régénérer ou écraser un carnet ou des réponses existants. La clé ANSWER-KEY-PRIVATE.json reste dans .lab-private et **ne doit jamais** être introduite dans ChatGPT. Le guide vérifie les empreintes de la source officielle et le contenu exact des fichiers préparés au démarrage, et n'emploie pas la clé dans ses fonctions de sélection et collecte.

## Session de travail sans API

Afficher le prochain prompt dans l'ordre fixe (calibration avant évaluation), puis l'envoyer **manuellement** dans une nouvelle conversation distincte :

~~~bash
python -m lab.exp011_session_guide --source test.jsonl \
  --out-dir .lab-private/exp011 next
~~~

Enregistrer la sortie **réellement renvoyée** par ce modèle dans un petit fichier UTF-8 local, par exemple .lab-private/exp011/current-reply.txt. Relever la référence effective de cette nouvelle conversation (id ou URL raccourcie de moins de 129 caractères, sans y mêler de secret) et le modèle effectivement sélectionné. Enregistrer le rôle exactement indiqué par la commande next :

~~~bash
python -m lab.exp011_session_guide --source test.jsonl \
  --out-dir .lab-private/exp011 record \
  --task-id gsm8k-test-0013 --policy adaptive --role solver \
  --response-file .lab-private/exp011/current-reply.txt \
  --session 'chat-reference-unique' --model 'model-selectionne'
~~~

Les valeurs ci-dessus illustrent **la syntaxe**, pas une observation. Les noms de tâche, politique et rôle doivent correspondre à la sortie réelle de next. Exécuter ensuite de nouveau next, puis record, etc. Une réponse malformée ou un refus doivent être enregistrés tels quels, sans correction par l'opérateur.

Pour une route parallel, le second prompt **ne contient pas** la réponse du premier. Pour une route review, le second prompt contient **uniquement la réponse du solveur déjà consignée**, pas l'oracle. Chaque rôle nécessite un nouveau chat. Les routes blocked sont automatiquement sautées par le guide, mais restent dans les 64 essais et dans le score final.

Affichage de progression, sans les réponses ni le corrigé :

~~~bash
python -m lab.exp011_session_guide --source test.jsonl \
  --out-dir .lab-private/exp011 status
~~~

Les options facultatives --elapsed-seconds, --input-tokens, --output-tokens peuvent être renseignées **uniquement lors du dernier rôle d'un essai**, pour des totaux manuellement mesurés sur tout l'essai. Si inconnues, elles restent null, et non zéro. Une étiquette de modèle différente est refusée pour maintenir un comparateur nominal identique ; il ne s'agit pas d'une vérification de provenance du modèle.

Après collecte, lancer **séparément** le contrôle EXP-011C puis le score EXP-011 :

~~~bash
python -m lab.exp011_provenance --source test.jsonl \
  --out-dir .lab-private/exp011 \
  --report .lab-private/exp011/provenance-audit.json
python -m lab.exp011_manual score --source test.jsonl \
  --out-dir .lab-private/exp011 \
  --report .lab-private/exp011/score.json
~~~

Les deux rapports restent locaux, privés et non publiés par défaut. Ne jamais coller la clé, la réponse oracle ni les fichiers entiers dans un prompt de rôle.

## Limites et règles de preuve

- Les commandes next, record et status sont **100 % hors ligne** : zéro appel IA, aucun navigateur ouvert, aucune vérification de ChatGPT, aucun agent autonome. Le guidage ne doit pas être présenté comme une expérience complétée.
- Les références de conversation, les étiquettes de modèle, les réponses et les métriques sont **déclarées par l'opérateur**. Un chat unique ne garantit pas l'indépendance du contexte ; utiliser le même modèle dans plusieurs chats n'est pas employer des modèles différents.
- L'outil refuse les duplications de références, les rôles hors ordre, les modifications de réponses existantes et les mutations de politiques. Les écritures sont atomiques dans le fichier privé ; **une seule personne/processus** doit écrire à la fois.
- Le fichier current-reply.txt doit contenir le texte réel de la sortie, limité à 200 caractères par le schéma EXP-011. **Ne pas remplacer** un refus, une sortie malformée ou un cas non exécuté par une réponse inventée ou corrigée.
- Les 16 tâches GSM8K sont publiques et peuvent être connues des modèles. La collecte réelle, si elle a lieu, restera un pilote à faible taille et ne prouvera pas qu'une architecture est meilleure de façon générale.
- Si aucun accès à de vrais chats séparés n'est disponible, l'état scientifique reste : **aucune comparaison réelle** des quatre politiques. [Issue #40](https://github.com/floiaassistant-design/Le-laboratoire-ia/issues/40) reste le chantier de mesure.
