# EXP-018 — couverture et abstention des routeurs sur 24 demandes naturelles

**Préenregistrement** : [issue #62](https://github.com/floiaassistant-design/Le-laboratoire-ia/issues/62) et ce protocole ajoutés avant les questions, les transformations, le code de mesure et les sorties. Les politiques d'EXP-011, EXP-015 et EXP-017 sont **gelées** : aucun changement de leur logique. Toute recherche de correctif après les résultats constituera une expérience séparée.

## Question scientifique, limitée

Sur des demandes nouvelles, écrites naturellement et non au format attendu du candidat EXP-017, quel est le **compromis mécanique entre couverture, abstention et déclenchement de rôles** ? Est-il possible d'identifier des omissions de traitement sur des tâches que l'auteur déclare mathématiques et des traitements proposés sur des demandes que l'auteur déclare non arithmétiques ?

**Ce projet n'observe pas la justesse d'un LLM.** Les étiquettes d'intention sont déclarées par l'auteur, non un oracle d'intention indépendant, et les exemples sont conçus en connaissant les règles. Les comptes de routage sont des constats de code, non des performances scientifiques généralisables.

## Cohorte gelée

Manifeste `experiments/exp018-cases.json`, **24 cas**, regroupés en 6 catégories de 4 :
- `natural_single_digits` (4 demandes mathématiques, prose naturelle, chiffres)
- `natural_multistep_digits` (4 demandes mathématiques en plusieurs étapes, chiffres)
- `number_words_only` (4 demandes mathématiques, chiffres écrits en toutes lettres)
- `implicit_operations_digits` (4 demandes mathématiques avec vocabulaire d'opérations implicites, chiffres)
- `non_arithmetic` (4 demandes non arithmétiques, des nombres peuvent apparaître comme identifiants)
- `math_with_format_digits` (4 demandes mathématiques où le format est intégré à la question)

**20 mathématiques / 4 non arithmétiques (étiquettes d'auteur)**. Questions et paraphrases créées à la main, en **anglais uniquement** ; aucune solution ni réponse attendue, aucune sélection à partir des 12 tâches EXP-011. Provenance : exemples originaux générés pour le protocole, non échantillonnés, ni corpus public. Exclure les tâches contenant plus de 500 caractères ou une instruction d'injection inhabituelle ; les cas sont figés dans le manifeste, pas exclus après résultat.

## Transformations non balisées, figées avant observation

Chaque cas utilise :
1. `base` (question originale).
2. `paraphrase` (une réécriture **explicite fixée dans le manifeste**, auteurs seuls juges de l'équivalence de demande).
3. `polite` : ajouter exactement `Please keep your reply short.` sans nouveau fait quantitatif.
4. `background` : ajouter exactement `This question comes from an everyday conversation.` sans nouveau nombre.
5. `embedded_format` : ajouter exactement `Put your final response in bold text.` comme consigne en langage naturel **sans balise spécifique de l'EXP-017**.

Les **16 cas mathématiques à chiffres** des catégories `natural_single_digits`, `natural_multistep_digits`, `implicit_operations_digits`, `math_with_format_digits` reçoivent également :
6. `number_words` : remplacer chaque chiffre entier de la base par le mot anglais **enregistré dans le manifeste**, sans autre réécriture. Aucune variante `number_words` pour les catégories de base sans chiffres arithmétiques (`number_words_only`, `non_arithmetic`).

Au total : **24 × 5 + 16 = 136 entrées par politique** ; 24 paires pour chacune des quatre premières transformations et 16 paires `number_words`. Ne pas inventer d'autres variantes après résultats. Le changement de format ou la politesse peut affecter le comportement d'un vrai LLM : **aucune invariance cognitive démontrée**.

## Politiques et budget

Exécuter sur toutes les entrées sans modifier les modules existants :
- `baseline_length` via `task_profile` + `choose(adaptive)` EXP-011 ;
- `candidate_content` via `candidate_route` EXP-015 ;
- `candidate_conservative` via `conservative_decision` EXP-017.

Budget **2 appels de rôle prévus**, puis budgets **0/1/2 sur les 24 bases**. Les états `single`, `parallel`, `review`, `needs_review` indiquent une **affectation de rôle possible**, pas un modèle exécuté. Les états `uncertain`, `unsupported`, `invalid_input`, `blocked`, `blocked_by_budget` doivent rester séparés. Une entrée `invalid_input` ne devient pas `blocked` ni un résultat à zéro coût mesuré.

## Indicateurs déclarés avant calcul
- Distributions d'états par variante et groupe, statut et nombre d'appels **prévus** de chaque observation (ou `null` si invalidité de l'entrée pour EXP-015).
- Pour chaque transformation et chaque politique : `total`, `unchanged`, `changed`, `invalid_base`, `invalid_variant`. Les deux types d'invalidité ne doivent pas être comptés dans une stabilité.
- Sur les 24 bases et sur les 136 entrées par politique : **couverture d'affectation** (`single/parallel/review/needs_review`), abstentions `uncertain/unsupported`, erreurs d'entrée et blocages distincts.
- *Proxy d'omission d'affectation* : nombre des **20** cas `author_math_intent=true` dont le routeur n'affecte aucun rôle à la base ; ce n'est pas une erreur de modèle ni une fausse réponse démontrée.
- *Proxy d'engagement non arithmétique* : nombre des **4** `author_math_intent=false` auxquels le routeur affecte un rôle à la base ; ce n'est pas un faux positif observé d'un LLM.
- Comptes de budget 0/1/2 sur chaque politique avec **dénominateur fixe 24** ; l'absence de traitement par manque de budget n'est pas classée comme refus sémantique.
- Résumé permanent contrôlé par égalité complète avec le rapport recalculé, rapport complet dans les artefacts de GitHub Actions.

## Restrictions et limites
Ce sont **des exemples construits pour éprouver des règles déjà connues** ; il n'existe pas d'échantillon aveugle, d'intention annotée indépendamment, d'oracle de raisonnement ou de comparaison de modèles. Réutiliser EXP-018 pour optimiser un futur routeur impose de classer la cohorte **développement**, et de préenregistrer une autre cohorte pour une nouvelle évaluation (EXP-019 au plus tôt).

Les 12 tâches de validation EXP-011 et leurs prompts restent gelés et sans évaluation comparative réelle. Aucune nouvelle donnée ne doit être insérée dans EXP-008B/012/013/014/015/016/017. Aucun appel API payant ni LLM local requis, aucune exécution de logiciel tiers sur l'ordinateur utilisateur, aucune fusion avant **tous les workflows verts sur SHA exact**.

## Exécution
```bash
python -m unittest discover -s tests -v
python -m lab.exp018_natural_coverage --output results/exp018-natural-coverage-audit.json
```
