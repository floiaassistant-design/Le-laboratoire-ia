# EXP-016 — stress-test sur une nouvelle cohorte de formulations

**Préenregistrement** : [issue #56](https://github.com/floiaassistant-design/Le-laboratoire-ia/issues/56) et ce document, enregistrés avant les observations de routage sur la cohorte EXP-016. L'auteur connaît le fonctionnement du routeur ; la cohorte est **nouvelle par rapport à EXP-014/015, mais pas aveugle ni représentative**. Aucune optimisation du candidat sur cette cohorte n'est autorisée.

## Question

Le candidat à indices de contenu EXP-015 conserve-t-il sa route lors de quatre changements ciblés sur de nouvelles questions, et quelles limites structurelles révèle-t-il ?

## Cohorte gelée avant calcul de routes

Seize problèmes arithmétiques écrits par l'auteur, répartis dans quatre groupes **de quatre** : `simple_two_literals` (une opération, deux nombres écrits en chiffres), `simple_three_literals` (une opération, trois chiffres), `multistep_marked` (plusieurs opérations, un mot de transition `then` ou `later`), `multistep_unmarked` (plusieurs opérations sans ces marqueurs). Ces groupes **sont des annotations de construction**, pas une difficulté observée ni un oracle. Données et remplacements exacts : `experiments/exp016-cases.json`. Les questions n'ont pas été tirées aléatoirement d'une population.

## Transformations pré-spécifiées

Chaque base reçoit les trois variantes suivantes, et une quatrième uniquement pour les quatre cas `multistep_marked` :

1. `neutral_padding` : répéter exactement la phrase `This background note adds no quantities and changes no calculation requirements.` jusqu'à atteindre **au moins 60 mots**. Elle ne comporte ni chiffre, ni `then/later`. Conserver la question originale au début. Cette phrase diffère de celle d'EXP-014.
2. `number_words` : remplacer les littéraux numériques écrits en chiffres par leur orthographe anglaise fixée dans `number_words` du manifeste, sans changer les autres caractères. Les remplacements sont des tokens numériques entiers exacts, appliqués simultanément ; ne pas utiliser de réponse ni d'oracle. Si tous les chiffres disparaissent, **le candidat peut rejeter la question : compter un `invalid_input`**, et non un `blocked` ni une route inchangée.
3. `misleading_stage` : ajouter exactement `For formatting only, write the word then after your answer.`. Cela ajoute une consigne de présentation, **pas de nouvelle étape arithmétique**, mais modifie les exigences de format. Mesurer les escalades lexicales sans prétendre que les deux requêtes sont cognitivement équivalentes.
4. `stage_removed` (seulement groupe marqué) : remplacer l'occurrence unique du mot entier `then` ou `later` par `afterward`, sans changer le reste. L'auteur considère l'ordre arithmétique inchangé ; cela n'est pas testé avec un LLM.

Exactement 16 bases + 16 × 3 variantes + 4 variantes `stage_removed` = **68 entrées** par routeur. Réutiliser les modules historiques `lab.exp011_manual.task_profile`, `lab.exp010a_adaptive.choose` et `lab.exp015_content_router.candidate_route` **sans aucun changement**.

## Mesures fixées avant les résultats

- Pour chaque politique `baseline_length` et `candidate_content`, chaque variante et chaque groupe : route (`single/parallel/review/blocked`) ou `invalid_input`, nombres de mots, nombres littéraux, indicateur `then/later`, SHA-256 du texte.
- Pour chaque transformation : nombre de paires base/variante où la route **change**, où elle **reste identique**, où une entrée est rejetée ; aucun rejet n'est compté comme stabilité, et les dénominateurs 16/16/16/4 doivent être conservés.
- Appels de rôle **prévus** par variante pour les routes valides seulement ; couverture des entrées publiée en parallèle. Une erreur de validité n'est pas assimilée à un coût zéro réel.
- Profil structurel : distribution des routes par catégorie d'auteur et nombre de cas multistades *non routés vers review*, avec réserves explicites sur le caractère non validé des catégories.
- Analyse des budgets sur les **16 questions de base** pour 0, 1 et 2 appels de rôle autorisés, pour les deux politiques. Compter `blocked` séparément de `invalid_input`. Aucun appel réel n'est exécuté.
- Synthèse versionnée vérifiée contre le calcul déterministe et artefact CI du rapport détaillé ; tests adversariaux pour détecter altérations du manifeste, de l'ordre des cas et des transformations.

## Interprétation et limites

Il ne s'agit **ni** d'un essai aveugle **ni** d'une validation hors distribution : l'auteur connaît les heuristiques et conçoit des cas qui les sollicitent. Les catégories de complexité sont descriptives. Stabilité de route ≠ exactitude, intelligence, latence ou économies. Aucune réponse LLM, aucune indépendance d'agents, aucune comparaison réelle de quatre politiques EXP-011. Le routeur gelé de l'EXP-011 ne change pas ; les résultats EXP-008B et EXP-012/013/014/015 restent intacts.

Les conclusions doivent publier **toutes** les sorties défavorables. Si la couverture du candidat tombe sur les nombres écrits en mots, c'est une limite à rapporter et non une raison de changer ses règles après coup.

## Reproduction prévue

```bash
python -m unittest discover -s tests -v
python -m lab.exp016_routing_stress --output results/exp016-routing-stress-audit.json
```

Les commandes ne nécessitent ni réseau ni API de modèle. La synthèse permanente sera `results/exp016-routing-summary.json`. Fusion uniquement après vérification de **tous** les workflows sur le SHA final de la PR.
