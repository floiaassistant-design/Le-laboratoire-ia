# EXP-009B — lot indépendant de 12 candidats (préqualification de métadonnées)

**Statut au 4 novembre 2026 : candidats seulement ; aucun nouveau test exécuté.**

Ce préinventaire est distinct des précédentes cohortes QuixBugs, PySnooper,
tqdm, youtube-dl, Tornado et Cookiecutter. Source : métadonnées BugsInPy au
commit immutable \`11c5f1eea954a42132cfd06bf257766a7963e0fd\`.
Aucun code du corpus n'est recopié.

Quatre dépôts publics : \`psf/black\` (3 candidats), \`fastapi/fastapi\` (3),
\`httpie/cli\` (3), \`nvbn/thefuck\` (3). Leurs noms précédents dans les
métadonnées BugsInPy peuvent être des alias GitHub historiques. Les douze
commits corrigés ont été consultés dans GitHub le 4 novembre : chacun
possède pour premier et seul parent le commit fautif déclaré. Le premier
commit corrigé de chaque projet a aussi été contrôlé pour la présence et
l'intitulé de sa licence (trois projets MIT ; HTTPie BSD-3-Clause).

Le manifeste \`experiments/exp009b-candidates.json\` conserve les SHA,
fichiers de tests annoncés par BugsInPy, versions Python historiques et
provenance. Le script \`python -m lab.exp009b_candidates\` vérifie **hors
réseau** leur structure : 12 ID distincts, 4 projets, SHA-40,
filiation déjà vérifiée, chemins sûrs, pas de score ou résultat enregistré.

## Travaux obligatoires avant de geler le lot

1. Contrôler **chaque** licence aux révisions pertinentes et vérifier que
   les fichiers de tests existent effectivement dans chaque commit corrigé.
2. Qualifier versions exactes Python et dépendances de chaque projet.
   Les métadonnées indiquent 3.8.3 pour Black/FastAPI, 3.7.3 pour HTTPie,
   3.7.0 pour TheFuck ; ces versions ne sont pas automatiquement disponibles
   sur tous les runners actuels.
3. Choisir et fixer les tests, données métier, oracles, exclusions et coûts
   **avant d'observer toute issue d'exécution**.
4. Vérifier la reproductibilité isolée de chaque banc sans importer de code
   tiers sur l'ordinateur utilisateur. Tout cas impossible à exécuter reste
   inscrit et signalé comme bloqué ; n'en retenir uniquement les réussites
   invaliderait le protocole.
5. Créer la vraie cohorte gelée avec séparation explicite qualification /
   validation. La présence de tests post-correctif impose une lecture
   rétrospective non aveugle.

**Aucun gain de politique, aucune découverte de bug nouveau, aucune
validation indépendante ne sont revendiqués par ce préinventaire.**


## Étape de qualification des sources — contrôle répété et CI (PR suivante)

Sur les 12 couples de versions, contrôle de **36 ressources publiques** en
lecture seule le 4 novembre 2026 : 24 licences (\`buggy\` et \`fixed\`) et
12 fichiers de tests de la version corrigée. Les fichiers étaient présents,
et leurs textes de licences conformes aux familles MIT ou BSD-3-Clause
annoncées. **Cette inspection manuelle ne prouve pas la compatibilité des
dépendances, ni la qualité ou la détectabilité d'un bug.**

Pour rendre ce constat reproductible, \`python -m
lab.exp009b_source_preflight --project <project>\` exécute uniquement des
requêtes GET vers \`api.github.com\`, avec les projets explicitement allowlistés.
Il vérifie pour chacun des 3 cas du projet :

- le commit corrigé possède **exactement un parent**, qui est le SHA fautif
  du manifeste ;
- la licence annoncée existe dans **les deux versions** et contient ses
  marqueurs textuels de famille ;
- le fichier de tests de la révision corrigée existe et possède un SHA Git ;
- les 4 contrôles de chacun des 3 candidats sont présents dans le JSON,
  y compris en cas d'échec, sans logs bruts, source recopiée, traceback,
  URL contenant un jeton ou message d'exception externe.

La CI isolée crée un rapport JSON par projet (4 jobs) et vérifie
indépendamment la **disponibilité** des interpréteurs Python 3.7 et 3.8
(2 jobs), **sans installer de dépendances tiers ni exécuter les tests**.
La version exacte du correctif historique (3.7.0/3.7.3/3.8.3) n'est pas
automatiquement celle mise à disposition par \`setup-python\`. L'installation
et la compatibilité des dépendances restent à traiter dans une étape
distincte avant de qualifier le nouveau corpus expérimental.

**Statut des preuves ci-dessus :** la réussite du nouveau contrôle automatisé
doit être confirmée dans GitHub Actions sur le commit de la PR puis sur
\`main\` ; ne pas confondre la présence du code avec sa validation.
