# EXP-015 — routeur candidat à indices de contenu (sans LLM)

**Préenregistrement** : [issue #54](https://github.com/floiaassistant-design/Le-laboratoire-ia/issues/54), créée avant le code et les sorties d'EXP-015. Les six questions et le mécanisme EXP-014 sont **déjà connus** et ont servi à définir ces caractéristiques. Il s'agit d'un audit **rétrospectif de conception**, et non d'une validation indépendante.

## Question

Un routeur utilisant deux indices de contenu extrêmement simples conserve-t-il sa route lorsque les mêmes phrases neutres EXP-014 sont ajoutées ? Où échoue-t-il ?

## Règles figées avant exécution

- Témoin : `lab.exp011_manual.task_profile` puis `lab.exp010a_adaptive.choose` (`adaptive`, budget deux). **Ne pas changer ces modules, EXP-011, ses cohortes, ni les résultats antérieurs**.
- Candidat : analyser la question originale uniquement. Compter les **littéraux numériques écrits en chiffres** (entiers ou décimaux, sans interpréter des mots comme `quarter` ou `twice`). Détecter les mots entiers `then` ou `later`, sans tenir compte de la casse. N'utiliser ni réponse correcte, ni score, ni longueur.
- Profil et route du candidat : si un de ces deux mots apparaît, `uncertainty=2` donc `review`; sinon `uncertainty=0` et `parallelizable=True` seulement lorsque la question a au moins trois littéraux numériques, donc `parallel` ; sinon `single`. Budget fixé à deux appels de rôle. Refuser une question sans chiffres.
- Réutiliser le manifeste `experiments/exp014-neutral-padding-cases.json` et ses `short/medium/long` via `lab.exp014_neutral_padding.variants`. 6 familles × 3 variantes = 18 routes par candidat, sans LLM.
- Contrôle négatif : pour chaque question `short`, ajouter exactement `Then answer with the result.` et mesurer tout changement de route du candidat, **même si aucun nouveau chiffre n'a été introduit**.
- Mesures : nombre de familles dont la route change entre `short` et `long`, distribution des routes, appels de rôle **prévus** par variante, changements du contrôle négatif, et empreinte du manifeste.
- Critères de fonctionnement (attentes déterministes et non tests d'hypothèse statistiques) : route historique 6/6 familles changées; candidat 0/6 familles changées sous remplissage EXP-014; 3 `single` et 3 `review` à chaque variante; contrôle négatif 3/6 familles changées; appels historiques 6/12/12, candidat 9/9/9.

## Interprétation autorisée

Une stabilité pour les phrases exactes testées **ne prouve pas** robustesse face aux reformulations en général. Les indices sont sélectionnés après connaissance des six cas, et une phrase contenant `then` peut tromper le candidat : le contrôle négatif est conçu pour le démontrer. Une tâche avec trois chiffres n'est pas nécessairement plus difficile qu'une avec deux. L'effet des variantes sur la cognition d'un véritable modèle n'est pas mesuré.

Il n'existe **aucune mesure réelle** de qualité de réponse, de temps, de tokens, de coût, d'indépendance d'agents ou de gain par rapport à un modèle seul. Les comptes d'appels ne sont que des estimations mécaniques. Le pilote de quatre réponses EXP-012 demeure un pilote unique non comparatif, les douze questions de validation EXP-011 restent non évaluées, les bugs historiques et leurs scores sont intacts.

## Reproduction prévue

```bash
python -m unittest discover -s tests -v
python -m lab.exp015_content_router --output results/exp015-content-router-audit.json
```

Une synthèse permanente `results/exp015-routing-summary.json` est vérifiée par tests contre le calcul frais. La CI archive le rapport détaillé (éphémère), mais le code, le protocole et la synthèse restent disponibles. Ne pas fusionner avant la fin des jobs de CI sur le SHA final de la PR.
