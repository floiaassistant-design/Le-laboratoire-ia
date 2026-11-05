# EXP-020 — pilote local exploratoire, solveur puis relecteur distinct

**Statut : protocole préparé, non exécuté.** Date de rédaction : 5 novembre 2026, **après** le premier appel réel EXP-019, mais **avant** tout nouvel appel de modèle pour EXP-020. Cette expérience ne fait pas partie du holdout EXP-011, et ne prétend pas tester une hypothèse statistique.

## Question

Peut-on produire deux réponses successives à la même tâche depuis le programme local, en donnant un rôle de résolution à un premier modèle puis un rôle de critique au second, **sans requête de contexte ancien ni clé API classique** ?

## Conditions figées pour le premier pilote

- **Tâche unique en français**, créée spécifiquement pour l'essai, jamais utiliser les 12 tâches de validation EXP-011.
- **Solveur A :** `gpt-6.1-sol`, seul modèle ayant déjà produit une vraie sortie observée à cette date.
- **Relecteur B :** `gpt-6.1-terra`, vu au catalogue, mais sa capacité à répondre reste **à vérifier en pratique**.
- **Plafond strict : deux appels volontaires de modèle au total**, exécutés séquentiellement : un pour A, puis un pour B seulement si A réussit, aucun retry automatique, aucune tâche en parallèle, aucun autre appel implicite.
- Le **témoin « modèle seul »** est la réponse de A, conservée *telle quelle*. La condition « deux modèles » ajoute **uniquement** la réponse critique/corrigée de B ; le résultat n'est donc pas une comparaison à budget égal.
- **A** ne reçoit que la question et la consigne neutre « Donne ta réponse et expose les calculs. »
- **B** reçoit la même question et la **réponse complète de A**, précédées de « Vérifie chaque étape. Signale les erreurs et donne une réponse finale corrigée ou confirme la réponse si elle est juste. » Il ne reçoit **aucun oracle** ni autre conversation.
- Les deux appels doivent provenir de l'interface `requestRole()` du prototype et vérifier le catalogue et la permission. L'appel de B comporte le texte de A **explicitement transmis** dans son prompt ; `prior_context_sent:false` signifie seulement qu'aucune conversation *supplémentaire* n'est réutilisée.
- Aucun nouveau téléchargement de dépendance ou logiciel ne doit être nécessaire si le kit EXP-019 fonctionne. Exécution exclusivement locale, opt-in, après implémentation et tests.

### Énoncé gelé pour l'essai de connectivité

> Une association reçoit 17 cartons contenant chacun 24 cahiers. Elle donne le quart du stock à une école, puis 41 cahiers à un centre social. Elle range les cahiers restants en paquets de 12. Combien de paquets complets peut-elle former et combien de cahiers restent hors des paquets ?

Critère de correction *défini avant observation* (ne **jamais** inclure dans les prompts) : `17 × 24 = 408`, un quart `102`, reste `408 - 102 - 41 = 265`, `265 = 22 × 12 + 1` ; **22 paquets complets et 1 cahier restant**. Noter séparément le résultat final et la qualité des calculs.

## Journal de résultat local à constituer

Pour chacun des deux appels : identifiant de pilote, date locale, rôle, slug réellement retourné, chaîne du prompt (conservée localement), texte complet de la réponse, succès/échec, durée mesurée localement si possible. Indiquer explicitement que les sorties du SDK sont auto-rapportées, qu'aucune conversation UI ChatGPT distincte n'a été créée et que l'isolement interne des modèles n'est pas prouvé.

Ne publier **ni jetons, ni identités, ni journaux privés, ni prompts portant sur des données réelles du compte**. Publier uniquement un bilan anonymisé, après vérification par l'utilisateur. Pour protéger le quota, ne pas lancer sans un accord explicite et ne pas automatiser de lots supplémentaires.

## Conditions d'arrêt et limites

Si B n'est plus dans le catalogue, si le partage du forfait est désactivé ou si la requête A ou B échoue : arrêter et noter la cause générique. Un succès sur un exemple facile prouve surtout que le mécanisme à deux rôles fonctionne ; **il ne démontre pas la supériorité** d'un système multi-agent ni une économie de ressources. Les répétitions, tâches diverses, critères appariés et mesures de coût appartiennent à un protocole ultérieur, relié à [EXP-011](EXP-011-MANUAL-REAL-TASKS.md) et à l'[issue #40](https://github.com/floiaassistant-design/Le-laboratoire-ia/issues/40).
