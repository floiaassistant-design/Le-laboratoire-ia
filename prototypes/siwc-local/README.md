# EXP-019 — prototype local « Sign in with ChatGPT », sans clé API

**Nature : prototype technique opt-in, pas un essai EXP-011.** Préenregistré dans [l'issue #73](https://github.com/floiaassistant-design/Le-laboratoire-ia/issues/73), avant tout code et observation de modèle. Le prototype teste la possibilité d'effectuer **une requête Responses réelle** avec la permission facultative « ChatGPT plan usage » d'un compte éligible. Il ne crée pas de conversation dans l'interface ChatGPT et ne lit pas les anciens chats.

## Sources et éligibilité vérifiées le 5 novembre 2026

- [Sign in with ChatGPT — quickstart](https://developers.openai.com/siwc/quickstart)
- [Open source / local token-sharing](https://developers.openai.com/siwc/token-sharing-open-source)
- [Guide officiel d'intégration](https://developers.openai.com/cookbook/articles/sign-in-with-chatgpt)
- [DevKit officiel](https://github.com/openai/sign-in-with-chatgpt-devkit) : révision gelée **0a36fefeb913055c8c7a1a29b63d82b96b2e841a**, licence **non commerciale**, à consulter avant usage.

Les applications open source et personnelles exécutées **localement** peuvent demander l'autorisation. L'éligibilité du compte, les modèles proposés et les limites de consommation ne sont pas garantis. Les applications hébergées ou payantes nécessitent un accès approprié. **Ce prototype n'est pas un site web ou serveur MCP**, et il ne donne pas accès aux conversations de ChatGPT.

## Architecture et sécurité

1. Le lanceur lab-siwc.mjs fonctionne uniquement avec **Electron sur le PC**, jamais dans GitHub Actions. Le navigateur d'authentification ouvre exclusivement auth.openai.com ; l'utilisateur doit consentir explicitement à l'accès.
2. Le **DevKit officiel** @siwc/local effectue l'OAuth et les appels à l'API Responses. Le lanceur exige le chiffrement des jetons par le trousseau système Electron safeStorage. Linux avec stockage basic_text est refusé.
3. Les profils et jetons restent locaux dans le dossier sécurisé de l'application Electron. Le kit externe est cloné dans .lab-private/, déjà ignoré par Git. Ne jamais publier les jetons, fichiers de profil ou sorties privées.
4. L'adaptateur refuse l'inférence tant que le compte n'est pas connecté, que le partage du forfait n'est pas autorisé, qu'aucun modèle n'est effectivement proposé ou qu'un prompt est invalide.
5. Une requête role envoie **seulement** le prompt actuel et ne transmet aucun identifiant de réponse précédente ; cela **ne démontre pas** l'absence de mémoire interne ni l'indépendance des agents.

## Prérequis

PC Windows/macOS/Linux avec interface graphique et trousseau sûr ; Git et **Node.js 22.12 ou plus récent**. Les commandes suivantes sont à exécuter **sur ton ordinateur**, jamais depuis ce chat, et uniquement après vérification du code et de la licence.

### Préparation PowerShell sous Windows

Exécuter depuis le dossier local Le-laboratoire-ia :

~~~powershell
git clone https://github.com/openai/sign-in-with-chatgpt-devkit.git .lab-private/siwc-devkit
Set-Location .lab-private/siwc-devkit
git checkout 0a36fefeb913055c8c7a1a29b63d82b96b2e841a
npm ci
npm run build -w @siwc/local
Copy-Item ../../prototypes/siwc-local/lab-siwc.mjs ./lab-siwc.mjs
Copy-Item ../../prototypes/siwc-local/adapter.mjs ./lab-adapter.mjs
.\node_modules\.bin\electron.cmd .\lab-siwc.mjs login
~~~

Si le kit officiel change ou ne s'installe pas à cette révision, ne pas modifier artificiellement l'authentification ni utiliser des cookies ChatGPT. Le résultat du login doit déclarer la permission de partage active avant toute inférence.

### Contrôle après consentement

~~~powershell
.\node_modules\.bin\electron.cmd .\lab-siwc.mjs status
.\node_modules\.bin\electron.cmd .\lab-siwc.mjs models
# Une seule vraie requête volontaire, qui consomme du forfait :
.\node_modules\.bin\electron.cmd .\lab-siwc.mjs smoke
~~~

Si login réussit mais que plan_usage_enabled est false, aucune requête n'est envoyée. Si models ne propose aucun modèle, l'expérience est bloquée. Si smoke renvoie real_request_completed:true et un texte non vide, une seule requête technique a abouti **sur cette machine**. Aucun test réel de ce type n'a été réalisé ou enregistré au moment d'écrire le protocole.

### Un prompt de rôle, à exécuter séparément

Choisir un modèle réellement renvoyé par models. Préparer un petit fichier contenant **uniquement** la question/prompts, sans réponse oracle, puis :

~~~powershell
.\node_modules\.bin\electron.cmd .\lab-siwc.mjs role NOM_DU_MODELE CHEMIN_DU_PROMPT.txt
~~~

Une seule réponse est affichée sous forme de JSON. Garder ce texte localement dans .lab-private/ et ne pas l'envoyer automatiquement à GitHub. Les limites d'entrée sont de 8 000 caractères. Chaque appel est explicite ; aucun lot de 64 essais n'est lancé sans permission.

## Tests de CI et limites de conclusion

~~~sh
node --test prototypes/siwc-local/adapter.test.mjs
~~~

Les tests utilisent des clients **fictifs** et ne font **aucun** appel à un modèle réel. Ni connexion, ni permission, ni quota du compte ne peuvent être vérifiés dans GitHub Actions. Une requête réussie prouvera seulement la faisabilité de la connexion ; elle ne démontrera aucun gain de qualité multi-agent. L'[issue #40](https://github.com/floiaassistant-design/Le-laboratoire-ia/issues/40) demeure nécessaire pour les véritables expériences comparatives.
