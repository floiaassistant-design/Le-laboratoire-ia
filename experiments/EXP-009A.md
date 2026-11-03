# EXP-009A — audit des oracles sans modifier les scores

Mission #21 du laboratoire, après la PR #20 / EXP-008B. Résultats établis à partir des trois fichiers bruts authentiques du run GitHub Actions #41690471790, obtenus par téléchargement des artefacts, sans exécuter de nouveau le code tiers.

## Découverte de l'audit

Le score primaire EXP-008B exigeait FAIL (assertion) sur le programme ancien et PASS sur le correctif, jamais ERROR. Sur les quatre cas dépourvus de ce témoin primaire, trois possèdent pourtant un statut ERROR sur l'ancien et PASS sur le nouveau :

| Défaut | Statuts de la version fautive | Version corrigée | Test avec transition |
|---|---|---|---|
| youtube-dl-4 | 11 PASS, 1 ERROR | 12 PASS | TestJSInterpreter.test_call |
| tornado-2 | 51 PASS, 1 ERROR | 52 PASS | HTTPClientCommonTestCase.test_redirect_put_without_body |
| tornado-3 | 48 PASS | 48 PASS | Aucune transition |
| cookiecutter-1 | 10 PASS, 1 ERROR | 11 PASS | test_generate_context_decodes_non_ascii_chars |

**ERROR -> PASS n'est pas une preuve automatique d'un bug produit**. Un défaut logiciel peut causer une exception, mais une erreur de dépendance, d'installation, de fixture ou de plateforme peut produire le même statut. Le fichier brut EXP-008B enregistrait les statuts mais pas les traces exactes de ces exceptions. Il serait erroné de reclasser trois cas rétrospectivement en bugs détectés.

## Contrôle des correctifs upstream

- youtube-dl-4 : le commit 189935f15960300d316e8b07108b076ac6c2186a ajoute le test test_call et corrige les appels JavaScript sans arguments. Référence : https://github.com/ytdl-org/youtube-dl/commit/189935f15960300d316e8b07108b076ac6c2186a
- tornado-2 : le commit 4f486a4aec746e9d66441600ee3b0743228b061c ajoute une régression sur la redirection PUT sans corps. Référence : https://github.com/tornadoweb/tornado/commit/4f486a4aec746e9d66441600ee3b0743228b061c
- tornado-3 : le commit aa622e724f80e0f7fcee369f75d69d1db13d72f2 contient un test de message d'erreur lors de la destruction d'un client HTTP, lancé dans un sous-processus. Ce test a bien été collecté, mais est PASS dans les deux versions au cours de notre exécution. Le comportement original de destruction est reconnu comme subtil et peut dépendre du runtime. Référence : https://github.com/tornadoweb/tornado/commit/aa622e724f80e0f7fcee369f75d69d1db13d72f2
- cookiecutter-1 : le commit 7f6804c4953a18386809f11faf4d86898570debc corrige l'encodage du contexte UTF-8 sous Windows et ajoute un test non ASCII. Notre exécution Linux a produit ERROR sur la version ancienne, PASS sur la corrigée ; la cause exacte de cette erreur n'est pas établie sans trace. Référence : https://github.com/cookiecutter/cookiecutter/commit/7f6804c4953a18386809f11faf4d86898570debc

Les quatre commits ont modifié le fichier de tests examiné. Absence de FAIL strict ne signifie donc pas absence de régression conçue par les mainteneurs.

## Archivage et reproduction

La synthèse permanente est results/exp009a-oracle-audit.json. Elle conserve les huit cas, les comptes PASS/FAIL/ERROR/SKIP par version, les identifiants de tests dont le statut change, et les empreintes SHA-256 des cartes de statuts originales. Source : artefacts exp008b-youtube-dl-raw (ID 13257003490), exp008b-tornado-raw (ID 13257512471), exp008b-cookiecutter-raw (ID 13256907777), run 41690471790.

Le module lab.oracle_audit vérifie la cohérence entre comptes, identifiants, FAIL primaires et ERROR non comptés. Il ne fait ni classement, ni scoring nouveau, ni import de code tiers. Après récupération des trois fichiers bruts :

python -m lab.oracle_audit --input results/exp008b-youtube-dl-raw.json --input results/exp008b-tornado-raw.json --input results/exp008b-cookiecutter-raw.json --output results/exp009a-audit.json --require-complete

Les exécutions GitHub Actions habituelles d'EXP-008B archiveront également un audit séparé par projet ; toute instabilité entre anciennes et nouvelles exécutions devra être documentée, pas masquée.

## Interprétation

**Les scores EXP-008B demeurent inchangés : budget 12 = 2/8 défauts pour les trois politiques.** EXP-009A a montré que trois cas de plus possèdent des différences de statut potentiellement pertinentes, non utilisables automatiquement comme preuve de défaut. Un quatrième cas (Tornado-3) n'a pas été reproduit sous les conditions mesurées, malgré le test de régression.

Prochaine hypothèse, pour une expérience séparée sur de nouveaux cas : un oracle secondaire préenregistré pourrait examiner type exact de l'exception, phase setup/call/teardown, sorties attendues et logs nettoyés, avec exclusion explicite des erreurs d'environnement. Ne jamais changer les critères après lecture d'un bug et appeler cela une validation aveugle.

Aucun modèle d'IA, aucune API facturée, aucune tâche persistante et aucune découverte de bug inédit dans EXP-009A.
