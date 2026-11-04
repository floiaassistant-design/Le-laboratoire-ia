# EXP-009D-B — analyse post hoc du blocage TheFuck

**Nature de l'étude : explicitement POST HOC.** Le sondage préenregistré
EXP-009D a observé un téléchargement groupé impossible de roues binaires
TheFuck sous Python 3.7. La première observation est conservée sans aucune
réécriture dans \`results/exp009d-wheel-summary.json\` et dans les
artefacts du run #41804523888. Les trois cas \`thefuck-1/2/3\` restent
dans le dénominateur de douze défauts.

Nous cherchons uniquement à déterminer si le blocage provient d'au moins
une **roue directe indisponible** ou s'il apparaît pendant la résolution
des dépendances transitives. Aucune cause ne doit être déduite d'un code
d'erreur pip isolé : réseau, index, architecture et compatibilité Python
peuvent également expliquer un échec.

## Procédure et engagements

Les quatre contraintes sont exactement celles de la première sonde :
\`psutil==5.6.7\`, \`pyte==0.8.0\`, \`pytest==5.4.3\`,
\`pexpect==4.8.0\`. Les sonder **séparément** dans un job isolé
Python 3.7, via \`pip download --only-binary=:all: --no-deps\`, dans des
répertoires temporaires indépendants. Aucune installation, build source,
import ou test du logiciel historique. Le jeton GitHub et les variables
secrètes ne sont pas transmis au processus pip.

Enregistrer **les quatre résultats**, avec nom du paquet, statut
\`single_wheel_downloaded\` ou \`blocked\`, code d'échec expurgé,
nom/hachage/poids de la roue en cas de réussite, ainsi que les trois
IDs de bugs conservés. Aucun stderr brut, URL d'authentification,
stacktrace ou jeton ne figure dans l'artefact.

Si une roue directe manque, une autre pin éventuelle devra être
proposée avec version, licence, justification technique et **nouveau
protocole** ; cela ne rend pas le sondage initial réussi rétroactivement.
Si les quatre roues directes existent, le blocage est probablement dans
les transitives/la résolution groupée, **sans preuve encore de causalité**.

Les scores EXP-008B restent 2/8, aucun bug nouveau testé, aucune
comparaison de stratégies modifiée et aucun modèle évalué.
