# EXP-004B : pilote 4 programmes, avant comparaison sur 16

**Protocole gelé dans la branche avant lecture des résultats du pilote.** Le dépôt utilise 20 fonctions de QuixBugs, source fixe au SHA \`4257f44b0ff1181dedaedee6a447e133219fcebf\`.

## Séparation
Pilote seulement : \`bitcount\`, \`gcd\`, \`find_first_in_sorted\`, \`bucketsort\`. Les 16 autres cas de QuixBugs sont réservés et ne sont PAS évalués par le module pilote. Ce corpus n'est pas un véritable test aveugle humain, puisque les versions défectueuses restent dans le dépôt et nous avons pu les lire avant ce protocole. Ne pas prétendre que la future comparaison est indépendante d'une connaissance humaine des défauts ; le préciser systématiquement.

## Génération d'entrées et méthodes
Les méthodes dépendent des **contrats d'entrée** (types/domaines) et non des cas canoniques \`json_testcases\`, qui ne servent qu'à l'étalonnage EXP-004A.
- \`random\` : générer uniquement des entrées valides selon un tirage pseudo-aléatoire pré-déclaré.
- \`targeted\` : utiliser la liste statique de douze cas de frontières/structure pour la fonction (définie dans \`domain_probes\`).
- \`hybrid\` : trois premiers cas ciblés de cette liste et le complément aléatoire. Pour les budgets inférieurs à trois, utiliser \`min(3, budget)\` cas ciblés.

Budgets 1, 3, 6 et 12, 40 répétitions pour chaque programme, méthode et budget, graines fixées. Chaque essai s'arrête dès la première différence, avec **maximum** \`budget\` entrées essayées ; les entrées invalides consomment quand même le budget. Une entrée n'est acceptée que si la fonction corrigée fonctionne ; exceptions et expirations de la version erronée comptent comme anomalie. Délais : 30 ms/appel et 40 secondes maximum par programme. Toutes les sorties sont conservées par programme et méthode.

### Mesures
- Premier signal : nombre de programmes sur quatre détectés au moins une fois ; pas une mesure statistiquement puissante.
- Secondaire : répétitions ayant détecté le défaut, nombre d'appels réellement utilisés, expirations et invalidités.
- Une répétition n'est **pas** un nouveau bogue indépendant. Ne jamais analyser \`40 × 4\` comme 160 bogues différents.

### Critères de suite
Les quatre fonctions doivent fonctionner hors réseau et les tests unitaires doivent passer. Si les méthodes plafonnent toutes à 100 %, cette expérience ne permet pas de départager les stratégies ; ne pas en inventer de classement. Le futur protocole devra se concentrer sur la difficulté et le budget, sur un corpus mieux indépendant, avec budgets égaux, sans utiliser les résultats du lot final pour optimiser.

Exécution : \`python -m lab.quixbugs_pilot\`. Sortie : \`results/exp004b-pilot.json\`.

Aucun agent IA n'est invoqué. Ne pas assimiler ce pilote à une comparaison de modèles ou à une découverte algorithmique.
