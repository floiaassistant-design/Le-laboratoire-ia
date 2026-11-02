# EXP-004B — comparaison exploratoire sur 16 programmes QuixBugs

**Définition des politiques gelée dans la branche avant le run de comparaison ; ne pas modifier les politiques après lecture du résultat.**

## Objectif
Étendre le pilote EXP-004B à 16 nouveaux programmes du corpus QuixBugs, en gardant les quatre programmes pilotes hors du score. QuixBugs a été créé indépendamment du laboratoire, mais les versions défectueuses sont disponibles dans le dépôt et ont pu être vues par l'auteur : **ce n'est pas une étude en double aveugle ni une validation indépendante de la connaissance humaine des défauts**.

## Méthodes
Les entrées sont produites par des générateurs documentés de domaines fonctionnels, indépendants des fixtures de test canoniques. Trois méthodes immuables :
- \`random\` : tirages aléatoires depuis le domaine de la fonction ;
- \`targeted\` : douze cas structurels/limites, pris dans l'ordre déclaré ;
- \`hybrid\` : les trois premiers cas structurels/limites (ou moins si budget inférieur), puis tirages aléatoires.

Budgets maximum par exécution : 1, 3, 6, 12 ; 10 graines fixes par fonction et par budget. Chaque politique dispose des mêmes plafonds de tentatives, chaque oracle consomme une tentative même s'il est invalide. Arrêt au premier défaut détecté. Chaque programme a un sous-processus isolé, arrêté après 45 s maximum. Chaque appel de fonction est limité à 30 ms. Pas de données ni d'API externes au runtime.

## Métriques
- Principal : **nombre de programmes distincts** avec défaut détecté au moins une fois, sur le corpus évalué, pour une politique/budget.
- Secondaires : nombre de programmes détectés à chaque répétition, nombre de tentatives utilisées et taux de tests refusés par l'oracle. Les 10 répétitions par programme ne sont pas 10 bogues indépendants.
- Les anomalies comprennent les exceptions et dépassements de temps du code défectueux seulement lorsque l'oracle corrigé fonctionne.
- Tout échec de processus est publié et le workflow échoue au lieu de supprimer silencieusement le programme.

## Limites et risques de biais
Les politiques ciblées sont construites manuellement et ordonnées ; le tout premier cas est déterminant à budget faible. Le choix des domaines et des distributions est un choix subjectif. La suite doit analyser la robustesse au changement d'ordre des cas, mais ces analyses seront explicitement exploratoires. Pas d'inférence sur des modèles de langage, des agents autonomes ou l'intelligence humaine.

## Reproduire
\`python -m unittest discover -s tests -v\`
\`python -m lab.quixbugs_external\`

Le workflow GitHub Actions archive le JSON brut, publie le résumé et exige un minimum explicite de tests unitaires réellement découverts.
