# EXP-006C — deuxième projet réel : tqdm, erreur `tenumerate(start)`

**Protocole enregistré avant l'exécution du test sur GitHub Actions.** Phase de calibration sur un défaut *connu*, distinct du projet PySnooper.

## Source, droits et sélection

- Données publiques **BugsInPy** : [dossier `projects/tqdm/bugs/1`](https://github.com/soarsmu/BugsInPy/tree/11c5f1eea954a42132cfd06bf257766a7963e0fd/projects/tqdm/bugs/1), révision figée `11c5f1eea954a42132cfd06bf257766a7963e0fd`. Les droits de redistribution du benchmark dans son ensemble restent à clarifier : **aucun code BugsInPy n'est recopié**.
- Projet réellement exécuté : [tqdm](https://github.com/tqdm/tqdm), licence historique `LICENCE` explicitant des termes MPLv2.0 et MIT (les termes diffèrent selon les fichiers) ; sources récupérées temporairement depuis le dépôt du projet, non redistribuées dans le laboratoire.
- Défectueux `8cc777fe8401a05d07f2c97e65d15e4460feab88` ; corrigé `c0dcf39b046d1b4ff6de14ac99ad9a1b10487512`. Le correctif est un commit enfant direct du commit fautif. Son message indique « fix tenumerate(start) ».
- Le corpus historique indique Python **3.6.9** ; la CI utilise Python **3.8.x** sur Ubuntu 22.04 par disponibilité. Il s'agit d'une reproduction *sur 3.8* ; cela ne garantit pas qu'un environnement Python 3.6 entièrement restauré donne exactement les mêmes résultats.

## Test de régression gelé, avant mesure

La fonction `tqdm.contrib.tenumerate` doit reproduire la sémantique de `enumerate` pour `start=42`. Le mini-probe autonome appelle la vraie fonction upstream avec les trois valeurs `["a","b","c"]` et une classe de progression transparente qui ignore les arguments supplémentaires.

- **Attente version fautive** : index observés `[0,1,2]` (décalage perdu), même si `start=42`.
- **Attente version corrigée** : index observés `[42,43,44]`.
- Les valeurs doivent rester `["a","b","c"]` dans les deux versions, les deux processus doivent **terminer correctement**, et l'import `tqdm` doit provenir explicitement du checkout temporaire.
- Toute erreur d'import/setup, de clonage, de licence ou de sortie inattendue : échec de CI, **pas de bug reproduit**.

Le test sélectionne volontairement le symptôme déjà documenté ; ce n'est **ni une découverte**, ni le test officiel BugsInPy, ni une évaluation à l'aveugle. Il est permis d'utiliser l'information du correctif pour cette *calibration*, mais jamais pour un benchmark de performance sur les mêmes défauts.

## Exécution et confinement

GitHub Actions : nouveau job `independent-reproduction`, sur Ubuntu 22.04 + Python 3.8, accès dépôt en lecture seule et `persist-credentials: false`. Aucun `pip install`, aucun script de build/test source exécuté ; le code upstream `tqdm` est néanmoins **importé et exécuté** en sous-processus avec limite de 20 secondes par commit. Un timeout global borne le job. Les logs et fichiers bruts sont archivés temporairement.

## Conditions de réussite et suite

1. Les métadonnées locales et les nouveaux tests unitaires passent sur Python 3.11.
2. Le code upstream de deux commits figés est testé dans deux états successifs.
3. Ancien résultat faux et nouveau résultat correct sur un cas de régression précis.
4. Deuxième logiciel indépendant validé **uniquement comme infrastructure de reproduction**.
5. **Avant toute recherche comparative :** définir une interface commune pour les cas réels, fixer un corpus plus large de défauts/projets et geler les stratégies sans consulter les résultats de ces nouveaux bugs. Deux défauts connus ne suffisent pas pour prétendre à une validation scientifique.

## Pour reproduire

```sh
python -m unittest discover -s tests -v
python -m lab.tqdm_start_smoke --offline
python -m lab.tqdm_start_smoke --online
```

Aucune API payante, aucun modèle IA, aucune automatisation récurrente.
