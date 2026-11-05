# EXP-013 — analyser honnêtement les stratégies d'orchestration

**Préenregistrement : 5 novembre 2026, avant toute collecte des 12 réponses
de validation EXP-011.** [Issue #48](https://github.com/floiaassistant-design/Le-laboratoire-ia/issues/48).
EXP-013 est un **analyseur Python hors réseau**. Il n'interroge aucune
IA, ne modifie pas les quatre politiques et ne peut pas démontrer leur
supériorité à lui seul.

## Pourquoi ce protocole supplémentaire ?

Dans EXP-011, le champ historique `observed_accuracy` compte les réponses
correctes parmi les essais terminés, y compris les abstentions. Une politique
qui répond une seule fois correctement sur douze tâches pourrait donc avoir
100 % de précision **conditionnelle**, tout en laissant onze tâches sans
observation. La comparaison resterait trompeuse sans le nombre de tâches
réellement assignées et les essais invalides.

Un second biais est **structurel** : le routeur EXP-010A interdit
`always_parallel` si la tâche est déclarée non parallélisable ;
l'orchestrateur `adaptive` peut alors utiliser `single`.
Un avantage adaptatif contre un **blocage imposé par la règle** ne démontre
pas de meilleur raisonnement d'un modèle.

## Cohortes et critères figés

- **Calibration** : indices GSM8K 13, 37, 59, 81, uniquement descriptifs.
- **Évaluation principale** : 12 indices GSM8K déjà figés par EXP-011
  (103, 158, 202, 271, 349, 418, 503, 611, 704, 826, 943, 1159).
- Politiques : `adaptive`, `always_single`, `always_parallel`,
  `always_review`. Chacune reçoit les **mêmes 12 tâches**.
- Un statut par paire tâche/politique : `correct`, `incorrect`,
  `abstained`, `blocked_by_design`, `malformed_response`,
  `unobserved_or_incomplete`, `missing_model_provenance`,
  `nonindependent_sessions`.
- Le résultat `blocked_by_design` est un échec connu de **livraison**
  au sein de la politique fixée, et **non une erreur du modèle**.
- `correct` donne une réussite connue ; une réponse incorrecte, un refus
  de livraison et une sortie malformée donnent **zéro bonne réponse
  livrée**. Les essais non observés, à provenance manquante ou dont les
  contextes ont été réutilisés sont **inconnus**, jamais une faute
  scientifique automatiquement imputée au modèle.

## Indicateurs avant toute observation

Par politique et séparément par cohorte :

1. Nombre assigné, dénombrement des huit statuts, réponses numériques
   livrées, fréquence de réponse et appels de rôles déclarés.
2. **Justesse conditionnelle des réponses livrées** :
   `correct / (correct + incorrect)`; `null` si aucune réponse livrée.
   Elle ne doit jamais être nommée « précision sur les 12 tâches ».
3. **Bornes déterministes sur la réussite par tâche assignée** :
   `correct / N` en borne inférieure et
   `(correct + nombre de statuts inconnus) / N` en borne supérieure.
   Ce ne sont **PAS des intervalles de confiance**, et une valeur nulle
   en borne inférieure en cas de zéro observation n'est pas un score
   empirique de modèle.
4. Temps et tokens **auto-déclarés** : total seulement si tous les
   essais non bloqués possèdent un relevé, sinon `null`.
   Les appels de rôles ne sont pas des prix API.

Comparaisons descriptives appariées `adaptive` contre chaque témoin :

- Les mêmes 12 identifiants, y compris les cas bloqués, restent présents.
- Compter paires aux résultats opérationnels connus, deux réussites,
  deux non-réussites, réussite adaptative seule ou témoin seul.
- Écart sur les paires connues (descriptif, non extrapolable).
- **Bornes logiques de l'écart sur les 12 tâches** en affectant aux
  sorties inconnues tantôt 0 tantôt 1, sans changer les sorties connues :
  `lower = sum(a_min - b_max) / 12`,
  `upper = sum(a_max - b_min) / 12`.
- Compter explicitement les tâches **bloquées par construction** chez le
  témoin et les victoires adaptatives correspondantes.
- Pas de p-value, pas de prétention à une confiance statistique et
  aucune sélection a posteriori de tâches favorables.

Les quatre questions de calibration EXP-012, malgré leur score 4/4,
n'entrent pas dans la comparaison principale.

## Commandes

Vérification synthétique sans modèle, sans téléchargement :

```bash
python -m lab.exp013_paired preflight --report results/exp013-analysis-preflight.json
python -m unittest discover -s tests -v
```

**Après** des sessions réelles volontairement consignées dans
`.lab-private/exp011/responses.json`, avec l'ensemble des fichiers
officiels préparés par EXP-011 :

```bash
python -m lab.exp013_paired analyze \
  --source test.jsonl \
  --out-dir .lab-private/exp011 \
  --report .lab-private/exp011/paired-analysis.json
```

Le programme vérifie le **blob intégral** de GSM8K contre son empreinte,
puis les questions et l'oracle local contre la source, **recalcule**
les 64 statuts avec `lab.exp011_manual.score` et produit la synthèse.
Il ne prend jamais un rapport chiffré externe pour preuve. La clé
privée ne doit pas être committée, transmise au solveur ou jointe aux
sessions.

## Limites scientifiques

Le corpus est petit, public et susceptible d'être mémorisé ; les coûts
de coordination et paramètres exacts de ChatGPT restent inconnus.
Des identifiants de conversation déclarés différents ne prouvent
ni isolation, ni indépendance statistique des réponses. Une analyse
complète en lignes n'atteste pas leur exécution réelle. Un avantage
descriptif peut venir de l'ordre de passage, des blocages par
conception, de choix de critères ou d'une contamination d'entraînement.

**Situation à la création** : zéro des 12 tâches de validation testé
sur des sessions autonomes et indépendantes. Aucun nouveau résultat
multi-agent n'est enregistré. EXP-008B reste 2/8 selon son ancien
protocole ; les issues #29 et #35 sur les bugs sont distinctes.
