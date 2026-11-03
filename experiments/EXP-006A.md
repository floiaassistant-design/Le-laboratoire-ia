# EXP-006A — priorité par diversité des entrées (pilote)

**Protocole fixé avant mesure des performances.** Date : 3 novembre 2026.

## Hypothèse

Il peut être plus utile d'exécuter d'abord des cas présentant des structures d'entrées différentes que de simplement suivre une liste arbitraire. L'hypothèse testée est **exploratoire** : un ordre construit par diversité d'entrées peut détecter davantage de bugs parmi les 4 cas pilotes de QuixBugs à budget 1, 3 ou 6.

Aucun modèle IA, agent ni connexion API n'est nécessaire. Cette approche relève de l'optimisation de l'ordre de tests : les heuristiques de diversité et la traversée « farthest-first » sont **connues** dans la littérature ; ne pas les appeler découverte originale.

## Règle déterministe, gelée avant les résultats

Pour chaque programme pilote (`bitcount`, `gcd`, `find_first_in_sorted`, `bucketsort`) :

1. Ne prendre que les **12 entrées ciblées existantes** d'EXP-004B, sans générer de nouvelles valeurs.
2. Extraire des étiquettes de surface : nombre d'arguments, types, classe de valeur d'entiers, longueurs, structure imbriquée, ordre des listes, présence de zéros et quelques éléments de forme ; aucune donnée d'exécution.
3. Mesurer la distance de Jaccard entre les ensembles d'étiquettes.
4. Choisir le cas le plus atypique en moyenne, puis choisir gloutonnement le cas dont la distance au plus proche déjà retenu est maximale. Pour les égalités, maximiser la distance moyenne puis utiliser l'ordre lexical du contenu d'entrée. Pas de paramètre appris ni de lecture de la version buguée.
5. **Après** avoir fixé cet ordre, évaluer chaque entrée une fois avec oracle corrigé puis version défectueuse, isolée par processus et limitée à 30 ms/appel.
6. Comparer la couverture à budgets 1/3/6/12 avec l'ordre original et avec la **probabilité exacte** de couverture d'un ordre uniformément aléatoire des 12 mêmes entrées.

Le coût du sélecteur est borné par O(n²) comparaisons de paires, avec n=12 cas seulement. Il n'est pas inclus dans le nombre de requêtes oracle ; si nous évaluons un usage réel, il faudra comparer le coût de sélection et le temps d'exécution.

## Interprétation

Le pilote compte seulement **4 erreurs** ; chaque programme est une unité distincte. Une espérance fractionnaire pour une permutation uniforme n'est pas un nombre d'erreurs réellement observées. À budget 12, l'ordre ne peut pas influer sur la couverture.

La référence est un corpus **déjà connu** ; les signatures de ces fonctions et les 12 cas originaux ont été examinés. Il ne s'agit pas d'un holdout, d'un test aveugle, ni d'une comparaison avec des agents IA.

Les résultats ne seront pas utilisés pour modifier l'algorithme en cours de test. Un résultat négatif sera archivé comme tel. Toute conclusion de généralisation doit attendre un nouveau benchmark réellement indépendant, avec règles figées avant le scoring.

## Exécution

```bash
python -m unittest discover -s tests -v
python -m lab.quixbugs_diversity
```

Les résultats détaillés sont stockés dans `results/exp006a.json` et archivés en artefact GitHub Actions. Sans API, modèle local ou tâche planifiée.
