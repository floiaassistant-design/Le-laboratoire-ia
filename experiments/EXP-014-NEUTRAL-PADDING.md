# EXP-014 — sensibilité du routeur à la longueur sans changement du calcul

**Protocole préenregistré avant exécution de la CI.**
[Issue #51](https://github.com/floiaassistant-design/Le-laboratoire-ia/issues/51).

## Question

Le prototype EXP-010A et le profil EXP-011 choisissent une route selon
deux seuils de longueur de la question (40 et 50 mots), non selon une
mesure directe de difficulté. Un énoncé inchangé quant à ses nombres
et à sa demande arithmétique peut-il emprunter une route différente
simplement parce qu'on ajoute des phrases explicitement neutres ?

Cet audit **ne compare pas plusieurs IA**, ne recherche aucun bug
inconnu et n'utilise aucun modèle. Il mesure une propriété déterministe
du routeur tel qu'il est programmé.

## Conditions décidées avant exécution

Source : [six problèmes écrits pour ce contrôle](exp014-neutral-padding-cases.json),
dont trois annotés par l'auteur comme comportant une opération, et
trois comme comportant plusieurs opérations. Ces annotations **ne sont
ni une échelle validée de difficulté ni un oracle de raisonnement**.

Pour chaque question, conserver intégralement la question initiale,
puis ajouter zéro ou plusieurs répétitions de l'unique phrase :

> No additional quantities or conditions are supplied here.

L'ajout ne comporte aucun nombre et ne présente pas de nouvelle
contrainte de calcul. Le code vérifie que tous les nombres d'origine
restent présents et dans le même ordre, et que la suite ne contient
que cette phrase. Il construit trois versions :

- `short` : moins de 40 mots ;
- `medium` : au moins 40 mots et moins de 50 ;
- `long` : au moins 50 mots.

Appliquer le **vrai** `task_profile` d'EXP-011, suivi du `choose`
d'EXP-010A, toujours avec budget de deux appels et politique
`adaptive`. Aucun seuil n'est modifié.

## Indicateurs prévus

Pour chacun des six problèmes : texte exact, longueur, empreinte,
route obtenue (`single/parallel/review/blocked`), nombre **prévu**
d'appels de rôle. Puis compter combien de familles changent de route
entre les trois variantes et la variation du nombre d'appels autorisés.

**Attente mécanique** : une fois les seuils franchis, le routeur
déclenche respectivement `single`, `parallel` et `review`. Le
changement n'est donc ni une surprise, ni une découverte statistique :
l'intérêt de l'audit est de rendre cette fragilité visible et vérifiable
dans le prototype, y compris avec ses vrais modules et une CI isolée.

## Exécution

```bash
python -m unittest discover -s tests -v
python -m lab.exp014_neutral_padding --output results/exp014-neutral-padding-audit.json
```

GitHub Actions génère et archive le JSON, mais **ne lance aucun modèle**.
L'empreinte du manifeste et les textes sont enregistrés pour permettre
une reproduction. L'archive GitHub Actions a une durée de vie limitée ;
le code, le manifeste et le protocole restent dans le dépôt.

## Conclusions autorisées et limites

- On peut constater une **non-invariance du choix de route** sur les
  questions construites, attribuable directement au comptage de mots.
- Une multiplication par deux des **appels de rôle prévus** entre deux
  variantes ne signifie pas une multiplication mesurée des tokens,
  coûts, temps, énergie ni de la précision d'une IA.
- La neutralité *arithmétique* de la phrase peut être inspectée, mais
  son absence d'effet sur la cognition d'un LLM n'est pas démontrée.
- Les six questions sont conçues par l'auteur précisément pour tester
  un seuil connu, sans échantillonnage indépendant ou aveugle.
- Aucune conclusion d'avantage d'un nouveau routeur n'est autorisée :
  aucun remplaçant n'est testé. La future hypothèse peut être de
  comparer la stabilité d'autres caractéristiques **sans connaître
  l'oracle ni utiliser la longueur comme difficulté**.
- **EXP-011 reste gelé** : aucun changement aux 12 tâches d'évaluation,
  aux 4 calibrations, aux seuils 40/50, à l'oracle ni aux scores
  EXP-012/013. Les expériences historiques de bugs restent séparées.

Aucune API payante, aucun LLM local ou distant, aucune automatisation
récurrente.
