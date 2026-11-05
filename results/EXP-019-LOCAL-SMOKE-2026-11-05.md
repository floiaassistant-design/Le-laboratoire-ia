# EXP-019 — premier essai local réel, rapporté le 5 novembre 2026

## Provenance et portée

**Nature :** observation transmise par l'utilisateur depuis PowerShell sur son PC Windows, après installation manuelle du DevKit officiel `openai/sign-in-with-chatgpt-devkit` épinglé à `0a36fefeb913055c8c7a1a29b63d82b96b2e841a`, connexion OAuth volontaire et correctif du blocage Electron [PR #76](https://github.com/floiaassistant-design/Le-laboratoire-ia/pull/76). **Ce n'est pas un essai réalisé par GitHub Actions**, ni une attestation indépendante du compte. Ne pas archiver de jetons, d'adresse e-mail, de profil OAuth ni de fichiers privés.

Les commandes et sorties transmises par l'utilisateur :

1. `electron ... lab-siwc.mjs status` avant connexion : `{"connected":false,"plan_usage_enabled":false}`.
2. `electron ... lab-siwc.mjs models` après connexion : catalogue de **8 entrées**, avec les slugs `gpt-6.1-sol`, `gpt-6-astra`, `gpt-6.1-terra`, `gpt-6-sol`, `gpt-6-luna`, `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`. Ces noms sont ceux **rapportés par le catalogue local à cet instant**, pas une garantie d'accès permanent ni une preuve de génération pour chaque modèle.
3. `electron ... lab-siwc.mjs smoke` : sortie rapportée :
   ```json
   {"model":"gpt-6.1-sol","output":"Laboratory connection works.","real_request_completed":true,"historical_chat_access":false}
   ```

**Ce que cela établit :** un premier appel volontaire `Responses` via le lanceur JavaScript/Electron a produit la phrase attendue avec `gpt-6.1-sol`. Le catalogue indique que l'autorisation de partage du forfait était active au moment de la liste, car `eligibleModels()` vérifie `getSession().sharing === true`. L'indicateur `historical_chat_access:false` décrit l'architecture du prototype ; ce n'est pas une preuve expérimentale globale sur les accès du fournisseur.

**Ce que cela n'établit pas :** aucun deuxième modèle n'a été testé en inférence ; aucune collaboration, comparaison avec un témoin, reproductibilité, latence, coût, précision, isolement inter-rôles ou gain d'orchestration n'a été mesuré. Les expériences EXP-011 comparatives restent à exécuter. Aucun mécanisme Python n'est encore connecté à cette preuve JavaScript.

## Suite prioritaire — protocole à préparer avant appels supplémentaires

Préparer un **pilote exploratoire préenregistré** distinct des 12 tâches de validation EXP-011 : même problème fourni à (A) un modèle seul et (B) un solveur puis un relecteur distinct, sans oracle dans les prompts. Choisir tâches, modèles, ordre, formats, critère de correction, provenance et plafond d'appels **avant** toute sortie. Aucun appel supplémentaire n'est déclenché par ce document. Conserver les réponses brutes localement dans `.lab-private/`, jamais sur GitHub. Un seul essai ne doit pas être présenté comme une supériorité statistique ; une comparaison robuste nécessitera répétitions et témoins appariés.

## Sécurité et suivi

La session et les jetons OAuth restent dans le stockage local chiffré du DevKit ; la CI n'a jamais accès à ces secrets. Trois vulnérabilités modérées `glob` / `minimatch` / `@electron/asar` subsistaient dans l'audit npm local après application des correctifs non cassants ; les quatre alertes « high » avaient disparu. Ne pas lancer `npm audit fix --force` par automatisme. Vérifier les dépendances avant élargissement des usages.
