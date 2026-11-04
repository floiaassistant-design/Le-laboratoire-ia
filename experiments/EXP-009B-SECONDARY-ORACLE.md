# EXP-009B — oracle secondaire : protocole préenregistré

**Statut : protocole seulement, aucune mesure sur une nouvelle cohorte.**
Rédigé avant le choix, le gel et l'exécution des prochains bugs. Il NE
réinterprète PAS les résultats 008A/008B/009A. Les quatre bugs réexaminés
pour qualifier le diagnostic sont **contaminés pour toute validation future**.

## Objet, hypothèse et métriques

Question principale du futur lot : lorsque des tests réels ne provoquent
pas d'assertion, un oracle secondaire explicitement défini peut-il reconnaître
un comportement incorrect sans confondre erreur d'exécution et bug source ?

- **Primaire inchangé** : FAIL assertion sur ancien et PASS sur corrigé,
  à identifiant de test inchangé. Ne pas rétro-noter ERROR.
- **Secondaire exploratoire distinct** : preuve reproductible d'une différence
  métier préspécifiée, observée sur ancien et corrigée sur nouveau, reliée au
  correctif et non à un échec de chargement. Les comptes primaires et secondaires
  restent dans des tableaux séparés.
- **Cas invalides** : erreur de collecte/import, dépendance manquante, échec
  du correctif, identité de tests différente, version non épinglée, comportement
  trop instable ou doute sur le symptôme ; noter **bloqué/non attribué**,
  jamais « négatif confirmé ».
- Une simple exception Python, une trame de pile dans le projet, un mot
  « warning » dans stderr ou une anomalie dans le score ne suffisent **pas**.
  Une exception peut être admissible seulement si son **type attendu** et
  sa **sortie/condition métier** ont été préspécifiés pour une entrée fixée
  indépendamment de la lecture des résultats. Ne pas compter un ERROR générique.

## Conception du prochain lot (non encore sélectionné)

Constituer **au moins 12 défauts et 4 dépôts de logiciels distincts**,
hors youtube-dl, Tornado, Cookiecutter, PySnooper, tqdm et QuixBugs si déjà
utilisés pour apprendre les décisions. Geler avant tout résultat :
- dépôt upstream, licence redistribuable et fichier de licence, révisions
  SHA-40 défectueuse/corrigée, preuve de filiation, Python et dépendances ;
- test/entrée, sortie métier attendue pour les deux versions,
  observables autorisés, règles d'exclusion et temps limite ;
- découpage développement/qualification versus validation ; les tests
  post-correctif renseignés sur le bug ne sont **jamais un essai aveugle**.

La liste de 12+ cas sera figée dans un manifeste immuable lié à une PR de
préenregistrement. Pas d'adaptation d'un oracle en fonction du verdict
du même bug ; tout écart sera une analyse post hoc clairement marquée.

## Comparateurs et rapportage

Baselines inchangées : lexical, aléatoire à graine 20261103,
diversité structurelle ; budgets 1, 3, 6, 12 et espérance combinatoire d'une
permutation uniforme. Conserver un même ensemble de tests par version et une
exécution par version. Mesurer temps de collecte/exécution, rang du premier
témoin primaire, témoins secondaires, exclusions, erreurs et cas sans signal.

Dénominateurs par **bug et par projet** ; répétitions et budgets ne sont pas
des observations de défaut indépendantes. Intervalles d'incertitude groupés
par projet uniquement si taille/plan permettent une estimation honnête ; sinon
présenter les proportions brutes et une limite explicite.

## Sécurité et reproductibilité

Ne jamais lancer de code tiers sur le poste utilisateur. Exécution uniquement
dans GitHub Actions isolées, permissions \`contents:read\`, sans jetons
persistants, sans secrets, versions de dépendances épinglées, sorties allowlist
uniquement ; pas de traceback brute, de données personnelles ni de logs
externes dans les artefacts. Tous les cas et blocages doivent être archivés.
**Ce document n'affirme aucun résultat nouveau.**
