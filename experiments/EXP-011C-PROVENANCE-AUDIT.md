# EXP-011C — audit de provenance des sessions EXP-011B

**Préenregistrement :** [issue #66](https://github.com/floiaassistant-design/Le-laboratoire-ia/issues/66), ouverte avant l'implémentation. Cette étude n'a appelé **aucun modèle** ; elle ne recueille ni scores de qualité ni coûts observés.

## Problème vérifiable

Le carnet EXP-011B contient 16 questions GSM8K × 4 politiques = 64 essais, avec des références de conversations manuellement saisies. Le score EXP-011 sait repérer une même référence de conversation *dans un essai*, mais ne vérifie pas une éventuelle réutilisation **entre essais**. Réutiliser le même chat entre plusieurs tentatives peut contaminer les réponses. **Un identifiant unique ne garantit jamais une session indépendante ; un doublon signale seulement un risque de réutilisation.**

## Mise en œuvre

Commande hors réseau, **après** la préparation et la génération du carnet EXP-011B :

```bash
python -m lab.exp011_provenance --source test.jsonl \
  --out-dir .lab-private/exp011 \
  --report .lab-private/exp011/provenance-audit.json
```

Le programme vérifie les fichiers préparés contre le corpus GSM8K épinglé, contrôle le carnet avec `make_runbook`, conserve les 64 essais (même ceux bloqués ou non réalisés) et examine uniquement les réponses et références **auto-déclarées**. Il exige un enregistrement par tâche/politique, des rôles cohérents avec les routes gelées, des références appariées aux sorties, des métriques numériques valides et aucune réponse pour un rôle non choisi.

Il distingue : `blocked_by_design`, `unobserved`, `partial`, `missing_model_label`, `reused_session_reference` et `complete_self_reported`. Le rapport donne les nombres par partition/politique, les références de sessions dupliquées **en compte uniquement** (ni valeurs de référence ni textes de réponses), les tentatives affectées, la présence ou l'absence des métriques et la diversité des étiquettes de modèle.

Les fichiers privés restent dans `.lab-private`, ignoré par Git. La commande refuse d'écraser un rapport existant. **La clé oracle est vérifiée pendant le précontrôle local de l'origine, mais n'entre jamais dans la fonction d'audit et n'est ni exportée ni utilisée pour juger les réponses.**

## Critères et interprétation

- Le rapport est un **contrôle d'ingénierie**, pas un benchmark ; les tests utilisent des sorties **fictives**.
- Les déclarations d'identifiants, de modèles et de coûts restent invérifiables hors produit. L'ordre chronologique effectif, le partage de mémoire, l'identité du modèle, l'usage d'outils et l'isolation réelle ne sont **pas** certifiés.
- Les valeurs de métriques non disponibles restent `null` et ne deviennent ni zéro ni des économies imputées à l'architecture. Aucune sortie non enregistrée ne devient un succès.
- La comparaison équitable des quatre stratégies reste **à réaliser sur de vraies sessions distinctes** conformément à l'[issue #40](https://github.com/floiaassistant-design/Le-laboratoire-ia/issues/40) et à EXP-011/011B. L'audit ne modifie ni les 16 tâches, ni les politiques, ni le score préexistant.
- Fusion uniquement après l'ensemble des workflows verts sur le SHA final ; documenter honnêtement tout blocage.
