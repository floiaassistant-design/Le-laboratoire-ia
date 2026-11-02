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

## EXP-004B — résultats externes, 16 programmes (CI #41540117757)

| Budget maximal | Aléatoire | Ciblé | Hybride |
|---:|---:|---:|---:|
| 1 | 94/160 (58.75 %) | 0/160 (0.00 %) | 0/160 (0.00 %) |
| 3 | 131/160 (81.88 %) | 110/160 (68.75 %) | 110/160 (68.75 %) |
| 6 | 150/160 (93.75 %) | 120/160 (75.00 %) | 143/160 (89.38 %) |
| 12 | 154/160 (96.25 %) | 160/160 (100.00 %) | 158/160 (98.75 %) |

- Tous les 16 programmes ont été évalués ; aucun processus n'a échoué ; 0 entrée rejetée par l'oracle dans ces mesures.
- **Programme distinct** : au budget 1, au moins une erreur a été détectée sur 16/16 programmes par les tirages aléatoires, contre 0/16 par les premiers tests ciblés. Au budget 12, au moins un essai détecte le défaut dans les 16 programmes pour chaque stratégie.
- **Interprétation :** aucune politique n'est systématiquement supérieure. Les premiers tests ciblés sont peu informatifs et l'ordre figé pénalise particulièrement les budgets 1 et 3. À budget 12 le ciblé détecte 160/160 essais, l'hybride 158/160 et l'aléatoire 154/160.
- 32 tests unitaires ont été découverts et réussis. Résumé JSON : `results/exp004b-external-summary.json`. Données brutes : artefact `exp004b-external-raw` dans la [run GitHub](https://github.com/floiaassistant-design/Le-laboratoire-ia/actions/runs/41540117757) (durée de conservation temporaire).
- Les dix répétitions par programme sont corrélées ; seules 16 erreurs distinctes ont été étudiées. Les cas avaient été publiquement accessibles avant la conception des politiques : **ce n'est pas une évaluation aveugle**. Aucune IA/agent n'a été comparée.

### Prochain objectif : EXP-005
Évaluer séparément l'**ordre des tests ciblés**, en gardant un budget fixe et en effectuant des permutations sans retoucher les ensembles de cas. Analyser l'effet sur le premier test et sur les budgets 3/6, sur le même corpus comme *analyse exploratoire*. Puis concevoir un protocole réellement nouveau (ou des corpus aveugles) pour vérifier sa généralisation, sans utiliser ces résultats pour choisir une méthode et la valider sur ces mêmes défauts.
