# EXP-009B — diagnostic des exceptions, phase 1

**Préenregistrement (avant toute nouvelle exécution historique).** Cette phase améliore
l'observabilité des tests et ne change PAS la définition d'une détection d'EXP-008B.
Les scores historiques au budget 12 restent 2/8 pour chacune des trois politiques.
Les trois transitions ERROR→PASS d'EXP-009A sont **non attribuées**.

## Hypothèse et protocole

Une catégorie d'erreur plus précise (type d'exception Python, phase
setup/call/teardown, frames dans le projet concerné) pourrait aider à distinguer
les pannes d'environnement des symptômes fonctionnels. **L'exception seule ne
prouve jamais le lien causal au bug.** Le diagnostic doit d'abord passer les
tests entièrement synthétiques hors réseau.

Le module \`lab.exception_diagnostics\` accepte les résultats de \`unittest\` ou
\`pytest\` et ne sérialise que des champs explicitement autorisés :

- \`exception_type\` : uniquement l'identifiant ASCII court de la classe, jamais
  le message, les arguments, la chaîne, les objets ou les variables locales ;
- \`phase\` : \`setup\`, \`call\`, \`teardown\`, ou \`unknown\` pour les cas
  \`unittest\` non classables sans hypothèse ;
- \`project_frames\` : au plus 4 trames situées sous le chemin du projet,
  **chemins relatifs**, nom de fonction nettoyé et numéro de ligne seulement ;
- comptes de tests, états par test **seulement pour les identifiants autorisés**
  dans le rapport synthétique \`redacted_view\`.

La collecte \`pytest\` fournit directement la phase d'exécution. Pour
\`unittest\`, elle est déduite des frames de \`setUp\`/\`test_*\`/\`tearDown\`
et peut demeurer \`unknown\`. Les noms sensibles inscrits dans les identifiants
de tests pourraient exister : ne transmettre que des IDs explicitement
préqualifiés. **Pas de trace brute, stdout, stderr ni identifiant de machine.**

### Étapes suivantes, non encore évaluées

1. Lancer dans GitHub Actions isolées les tests de versions historiques **figées**
   de youtube-dl-4, tornado-2, cookiecutter-1 (ERROR→PASS) et tornado-3
   (PASS→PASS). Vérifier les IDs déjà connus contre EXP-009A, conserver aussi
   les blocages et divergences. Si les statuts diffèrent, ne pas corriger
   rétrospectivement les observations d'EXP-008B.
2. Examiner les symptômes métier et les correctifs upstream sans confondre
   exception, environnement ou causalité. Classer \`source_bug_candidate\`,
   \`environment_candidate\` ou \`unattributed\` avec justification et
   niveau d'incertitude. La classification ne change aucun score.
3. **Avant toute nouvelle mesure**, figer un oracle secondaire distinct :
   test/entrée définis à l'avance, comportement fautif attendu dans
   la version antérieure, comportement attendu corrigé, pas d'erreur
   d'installation/collecte, environnement reproductible, rejet sinon.
4. Préqualifier puis geler **12 bugs ou plus sur 4 projets ou plus**,
   différents de EXP-006/008/009 : SHA-40 des deux révisions, relation
   de parenté, licence, Python/dépendances, test et exclusions. Ces bugs
   historiques et leurs tests post-correctif ne sont pas une validation
   aveugle. Rapporter les cas nuls, bloqués et les coûts, avec regroupement
   statistique par bug et par projet.

### Sécurité, limites et baselines

Exécuter du code tiers exclusivement dans des runners GitHub Actions isolés
\`contents:read\`, sans secrets persistants, jamais sur le PC utilisateur.
Ne pas faire de \`pip install\` ni exécuter de scripts tiers hors sandbox.
Les ordres \`lexical\`, \`seeded_random\` et \`structural_diversity\` sont
gelés comme baselines, avec budgets 1/3/6/12 et espérance de permutation
uniforme. Aucun modèle IA/API payante/automatisation périodique.
