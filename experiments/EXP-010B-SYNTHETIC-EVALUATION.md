# EXP-010B — comparaison des architectures sur témoins simulés

**Cette expérience ne mesure pas les performances de modèles d'IA.**
Elle caractérise EXP-010A sur **16 tâches symboliques faites à la main**.
Le manifeste experiments/exp010b-synthetic-cases.json a été commité
avant le premier script de comparaison dans cette PR. La cohorte
n'est pourtant ni indépendante, ni représentative, ni aveugle.

## Hypothèse exploratoire, non confirmée

Le routeur adaptatif peut éviter des appels abstraits et choisir
une revue lorsque le besoin est déclaré. Mais des agents indépendants
peuvent produire la même erreur, et un critique peut approuver une
mauvaise réponse ou rejeter une réponse correcte.

## Protocole fixe

- 16 cas fictifs, avec réponses symboliques A/B/C et budgets de rôle.
- 4 politiques sur chaque cas : adaptive, always_single,
  always_parallel et always_review ; **64 évaluations**.
- Chaque rôle retourne une réponse déterministe prédéfinie par cas,
  identique entre politiques ; le second solveur n'observe pas
  la première réponse, le critique l'observe.
- Blocages, abstentions et réponses incorrectes sont des catégories
  distinctes et aucun cas n'est supprimé du dénominateur.
- Mesures : vrais positifs mécaniques, fausses réponses, abstentions,
  blocages, appels de rôle, faux consensus et erreurs du critique.
- Les politiques impossibles restent bloquées, même si elles
  semblent désavantagées. Les contraintes de revue obligatoire
  ne sont jamais supprimées pour améliorer artificiellement le score.

## Vérification

    python -m unittest tests.test_exp010b_benchmark -v
    python -m lab.exp010b_benchmark --output results/exp010b-synthetic-report.json

Seuil CI porté à **311 tests**. Le rapport de la CI archive les
64 résultats ainsi que les totaux par politique.

## Portée réelle

Le coût est **une invocation de rôle fictive**, pas des tokens,
du temps CPU ou des euros. L'oracle est connu car inventé par
les auteurs du banc ; il n'existe aucun modèle, ni tâche externe,
ni apprentissage, ni recherche autonome dans cette expérience.

Ces résultats ne démontrent aucune supériorité d'une architecture.
Une validation future doit utiliser des tâches et oracles externes,
un modèle identique pour toutes les politiques, budgets de tokens
et temps comparables, et un jeu de validation non utilisé pour
choisir les règles. Les cas négatifs doivent être conservés.

Les issues historiques #29 et #35 restent ouvertes ; cette PR ne
modifie aucun des 12 bugs BugsInPy non exécutés ni aucun score antérieur.
