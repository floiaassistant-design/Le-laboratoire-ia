# EXP-010A — routeur adaptatif multi-agents, prototype hors ligne

**État : prototype d'orchestration, pas de véritable agent IA appelé.**
Ce travail est une piste d'architecture parallèle aux issues #29 et #35
(préparation de 12 bugs historiques), qui restent ouvertes et prioritaires
pour de nouvelles mesures de détection.

## Hypothèse (non encore vérifiée)

Un coordinateur fondé sur des caractéristiques de tâche définies **avant**
d'observer les réponses (incertitude, décomposabilité, risque et budget)
pourrait consommer moins de ressources qu'une collaboration systématique
sans réduire la qualité. Ce n'est pas un constat expérimental.

## Règles prédéfinies du prototype

- Single : un solveur ; coût synthétique = 1 appel de rôle.
- Parallel : deux solveurs indépendants ; le second ne reçoit pas le
  résultat du premier. Coût = 2 ; toute divergence reste sans conclusion
  automatique.
- Review : solveur suivi d'un critique pouvant approuver ou rejeter ;
  coût = 2. La critique n'est pas une preuve de vérité.
- Blocked : tâche non couverte par le budget ou par les exigences de
  revue. Les cas bloqués ne sont ni effacés ni comptés comme des échecs
  de raisonnement.

Pour la politique adaptive, une revue est choisie si obligatoire ou si
incertitude >= 2 ; sinon le parallèle est choisi seulement lorsque la
tâche est parallélisable ; sinon le solveur unique. Une tâche qui
impose une revue n'est **jamais** rétrogradée en mode single. La
dégradation faute de budget n'est autorisée que sans revue obligatoire.

Trois politiques de comparaison sont implémentées : always_single,
always_parallel, always_review. Les politiques impossibles sont marquées
blocked. Aucun seuil n'est appris par le pilote.

## Exécution de vérification (aucune API)

    python -m unittest tests.test_exp010a_adaptive -v
    python -m lab.exp010a_adaptive --output results/exp010a-smoke.json

Six scénarios purement simulés couvrent : simple, parallèle, critique,
budget insuffisant, désaccord, rejet. Ce sont des essais de flux de
contrôle avec des réponses fictives. Ils n'évaluent **ni la capacité
d'un modèle, ni la qualité des réponses, ni un progrès scientifique**.
L'unité de budget est un **appel de rôle abstrait**, ni tokens ni euros.

## Prochaine vraie expérience à préenregistrer séparément

1. Sélectionner un corpus de tâches indépendant, avec réponses vérifiables
   et catégories fixées *avant* l'évaluation, sans connaissance préalable
   du succès de telle ou telle architecture.
2. Comparer single, parallel, review et adaptive avec le **même modèle**,
   les mêmes outils, contextes et plafonds de dépenses, sur des tâches
   identiques. Inclure le coût du routage et de la critique, le temps
   d'attente, les cas bloqués et le taux d'escalade.
3. Évaluer la réussite par tâche, le coût réel, le désaccord, la
   dégradation en mode économique et le bénéfice marginal. Séparer
   entraînement/calibration et jeu de validation.
4. Archiver aussi les résultats négatifs et les cas ambigus. Ne pas
   transformer les tests synthétiques en validation indépendante.
5. Ne brancher un modèle externe ou local qu'après choix explicite
   des ressources et des permissions, jamais implicitement.

## Sécurité et périmètre

Le module reçoit un callback Python injecté par l'appelant, et ne
télécharge rien, n'appelle aucune API, n'exécute pas de code historique
tiers et ne lance pas de programme planifié. Les rôles simulés ne sont
pas des modèles IA. Aucune découverte de bug ni aucun résultat nouveau
sur la cohorte EXP-009B/009E n'est revendiqué. Une évaluation portant
sur des décisions sensibles nécessiterait un oracle fiable et une
supervision humaine.
