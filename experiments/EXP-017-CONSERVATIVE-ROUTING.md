# EXP-017 — routeur prudent à grammaire limitée et abstention explicite

**Préenregistrement** : [issue #59](https://github.com/floiaassistant-design/Le-laboratoire-ia/issues/59) et ce protocole, déposés AVANT création des nouveaux cas, exécution du candidat et consultation des sorties.

## Hypothèse limitée
Un routeur conservateur peut accepter une petite grammaire arithmétique exprimée en chiffres **ou** en mots, éviter d'escalader sur un `then` dénué d'opération arithmétique, et **s'abstenir** lorsque l'analyse est insuffisante. Cela peut augmenter la précision de l'étiquette `supported` au prix d'une couverture faible. **Aucune preuve de qualité de réponse de LLM**, d'autonomie ou de rentabilité n'est recherchée.

## Politiques figées
Comparer SANS LES MODIFIER :
1. `baseline_length` : `lab.exp011_manual.task_profile` et `lab.exp010a_adaptive.choose` (`adaptive`, budget 2).
2. `candidate_content` : `lab.exp015_content_router.candidate_route` (budget 2 ; échec sans chiffres compté `invalid_input`).
3. `candidate_conservative` : classificateur input-only expérimental, **sans appel modèle**.

### Grammaire et états du candidat
- Normaliser espaces extérieurs, sans modifier les unités ni les nombres ; longueur de l'entrée bornée à 6000 caractères.
- Lire les chiffres décimaux positifs et un lexique anglais limité aux nombres `zero` à `twenty` et dizaines complètes `thirty` à `ninety`, bornés par mots entiers. **Aucune interprétation libre** (fractions, `hundred`, monnaies, dizaines composées comme `twenty-one`). Les nombres hors vocabulaire restent hors couverture.
- Reconnaître **exclusivement** `Compute` ou `Calculate` suivis de `N plus/minus/times/divided by N` et éventuellement `, then/afterward/next add/subtract/multiply by/divide by N` (deux opérations). Une étape seule donne `single`, deux donnent `needs_review`. **Jamais** `parallel` sur une supposition de parallélisabilité.
- Ignorer comme annotations de présentation **uniquement les phrases supplémentaires explicitement préfixées** `Non-mathematical note:` ou `Formatting instruction:`, placées après l'énoncé complet, avec une longueur bornée. Noter `annotations_ignored`, ne pas prétendre qu'elles sont toujours sémantiquement neutres. Pour toute autre phrase supplémentaire, s'abstenir au lieu de deviner.
- Si hors grammaire mais présence d'indices mathématiques (`compute`, `calculate`, `how many`, `what is`, `total`, `remaining`, `left`, nombres reconnus), rendre `uncertain` (0 appel). Pour les questions manifestement non arithmétiques, rendre `unsupported` (0 appel). Une ambiguïté non résolue n'est pas un échec de modèle.
- Appliquer le budget : `single` requiert 1 rôle, `needs_review` requiert 2 rôles ; budget insuffisant => `blocked_by_budget`, sans rétrogradation silencieuse. Budgets autorisés 0, 1 ou 2 ; réponse `uncertain`/`unsupported` n'engage aucun appel.
- Sortie `status` à valeurs exactes `single`, `needs_review`, `uncertain`, `unsupported`, `blocked_by_budget` avec `calls_planned` entre 0 et 2, `annotation_count`, `reason` dans une énumération fixe. Tous les comptes restent des **plans**, sans exécution.

## Nouvelles données avant résultat
Créer **16 questions inédites** (4 par groupe) dans `experiments/exp017-cases.json`, sans oracle : `explicit_digits`, `explicit_words`, `explicit_two_stage`, `ambiguous_or_nonmath`. Pour chacune, trois entrées : `base`, `tagged_neutral` (ajout de `Non-mathematical note: no extra numbers are given.`), `tagged_format` (ajout de `Formatting instruction: include the word then in the margin.`). 16 × 3 = **48 formulations par politique**. Le dernier groupe comprend deux arithmétiques ambiguës et deux non mathématiques, fixées AVANT route du candidat ; ces étiquettes reflètent uniquement la construction de l'auteur.
Les catégories ont été choisies en connaissant les règles : **pas de holdout aveugle, pas d'estimation de généralisation**.

## Validation et indicateurs
- Dénominateurs fixes : 16 bases, 16 notes neutres, 16 notes de format, 48 lignes par politique, réparties en 4 groupes de 4 ; conserver rejets, abstentions et blocages.
- Pour chaque paire `base`/`variant` compter `unchanged`, `changed`, `invalid_variant` ; compter séparément les refus `uncertain`, `unsupported` et `invalid_input` ; ne pas assimiler couverture faible à robustesse.
- Compter route par groupe et calculer la couverture `single` + `needs_review` du candidat prudent, les abstentions, les **appels de rôle prévus** par politique. Ne pas comparer les coûts financiers, ni prétendre que `needs_review` améliore effectivement une réponse.
- Test supplémentaire : les **16 bases** EXP-016 constituent une régression **publique et réutilisée** : mesurer combien le nouveau candidat classe en `uncertain` ou `unsupported` plutôt que de lui attribuer une qualité arbitraire.
- Budgets 0/1/2 sur les 16 nouvelles bases, et absence d'appel sur les entrées ambiguës.
- Déposer une synthèse JSON permanente vérifiée intégralement contre le calcul déterministe par tests et CI, plus rapport détaillé en artefact GitHub.
- Publication de tous les effets négatifs : le routeur peut n'accepter que des calculs stylisés et s'abstenir massivement sur les problèmes naturels.

## Méthode et risques
Ni indépendance de concepteur, ni échantillon aléatoire, ni oracles mathématiques, ni exécution réelle d'agent ou de LLM. Échantillons écrits par l'auteur en connaissant les règles ; les critères de réussite lexicaux peuvent être artificiellement favorables et ne valent pas qualité hors distribution. L'absence de chiffre dans un texte n'est pas preuve qu'il ne s'agit pas de mathématiques. Les étiquettes `uncertain` et `unsupported` sont des décisions logicielles non validées.

**Interdits** : modifier les modules EXP-011/014/015/016, requalifier EXP-012 4/4 comme avantage multi-agent, transformer les 12 tests GSM8K EXP-011 en validation, faire appel à API payante, exécuter du code tiers sur le PC utilisateur, fusionner sans tous les workflows verts sur le SHA exact.

## Exécution prévue
```bash
python -m unittest discover -s tests -v
python -m lab.exp017_conservative --output results/exp017-conservative-audit.json
```
