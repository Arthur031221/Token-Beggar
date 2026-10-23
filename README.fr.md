# Token Beggar 🪙 : les mêmes réponses, une facture allégée

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner-dark.svg">
  <img src="assets/banner-light.svg" alt="Token Beggar : les mêmes réponses, une facture allégée. Envoie chaque tâche au modèle le moins cher qui l'exécute correctement." width="100%">
</picture>

<p align="center">
  <a href="https://github.com/Arthur031221/Token-Beggar/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/Arthur031221/Token-Beggar/ci.yml?branch=main&style=flat-square&label=CI" alt="CI"></a>
  <a href="https://github.com/Arthur031221/Token-Beggar/releases"><img src="https://img.shields.io/github/v/release/Arthur031221/Token-Beggar?style=flat-square&label=release" alt="Version"></a>
  <a href="pyproject.toml"><img src="https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square" alt="Python 3.10+"></a>
  <a href="pyproject.toml"><img src="https://img.shields.io/badge/dependencies-zero-brightgreen?style=flat-square" alt="Zéro dépendance"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/Arthur031221/Token-Beggar?style=flat-square" alt="Licence"></a>
</p>

[English](README.md) | [繁體中文](README.zh-TW.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [Português](README.pt-BR.md)

Token Beggar est un plugin pour Claude Code. Avant que le grand modèle ne traite une tâche, il vérifie si un modèle moins cher peut la réaliser tout aussi bien. Les petites tâches restent dans la discussion. Une tâche volumineuse, comme corriger un bug dans un dépôt que vous n'avez pas encore lu, est confiée à un worker moins cher, puis la discussion vérifie l'intégralité du diff et exécute les tests. La conception, l'identification des causes profondes et la réponse finale restent du ressort du modèle que vous avez choisi.

**Sur 18 corrections de bugs réels, il a consommé 1.42x moins de quota et d'argent qu'en travaillant seul, avec la même proportion de tests cachés réussis (69% contre 70%).**

Il s'exécute sur votre machine, dans votre session Claude Code. Il utilise le Claude Code auquel vous êtes déjà connecté, n'envoie aucune donnée vous concernant nulle part et n'écrit que dans son propre dossier. [Ce qu'il fait exactement](docs/on-your-machine.md).

[Installation](#installation) · [Démarrage rapide](#démarrage-rapide) · [Résultats](#résultats) · [Fonctionnement](#fonctionnement) · [FAQ](#faq) · [Documentation](#documentation) · [Changelog](CHANGELOG.md)

<p align="center"><img src="assets/demo.gif" width="760" alt="Terminal recording of the routing card, the compaction guard and the benchmark table"></p>

> [!TIP]
> Vous n'êtes pas certain qu'il fonctionne ? Exécutez `token-beggar doctor`. Cela liste ce qui peut interrompre discrètement le routage et renvoie le code de sortie 1 si quelque chose ne va pas.

## Installation

Nécessite Claude Code et Python 3.10 ou supérieur. Utilise uniquement la bibliothèque standard.

```
# From the marketplace in this repository (inside Claude Code)
/plugin marketplace add Arthur031221/Token-Beggar
/plugin install token-beggar@token-beggar
```

```
# Try it for one session without installing
git clone https://github.com/Arthur031221/Token-Beggar
claude --plugin-dir ./Token-Beggar
```

```
# From a shell, the same two steps as the first block
claude plugin marketplace add Arthur031221/Token-Beggar
claude plugin install token-beggar@token-beggar
```

Redémarrez l'agent ou lancez `/reload-plugins`. Pour en savoir plus, consultez [docs/install.md](docs/install.md), notamment pour utiliser le skill dans un autre agent qui lit les skills.

## Démarrage rapide

Travaillez comme vous le faites toujours. Au premier prompt réel d'une session, un hook ajoute une brève fiche de routage, et le modèle de discussion évalue la taille de la tâche. À la fin d'une réponse où un élément a été routé et où une économie a été mesurée, vous obtenez une ligne :

```
Token Beggar: about 1.4x less quota than Opus 5.5 high alone, saved about $0.21 (est.) | large task | routed 1: haiku medium x1
```

Le multiple est le rapport mesuré du coût au tarif catalogue sans Token Beggar sur celui avec lui, pour votre modèle et niveau d'effort. Le montant en dollars est le coût propre de la réponse multiplié par ce rapport moins un. Tous deux sont des estimations et l'indiquent. La ligne ne compte jamais les tokens, et en dessous de 1.15x elle n'indique aucun multiple, car cela se situe dans la dispersion entre les exécutions.

Pour l'activer sur un prompt qui ne l'a pas déclenché, écrivez `/token-beggar`. Vérifiez ensuite que les hooks s'exécutent :

```
token-beggar doctor
```

## Résultats

Opus 5.5 au niveau d'effort high comme modèle de discussion. Le coût correspond au tarif catalogue pour la discussion et chaque worker, cache inclus. Les intervalles sont à 95 pour cent. Une économie n'est revendiquée qu'à partir de 1.15x avec l'intervalle entier au-dessus de 1.0x.

Une version désigne ici une publication étiquetée de ce dépôt. **Sans Token Beggar (Without Token Beggar)** correspond au modèle de discussion travaillant seul. **v0.3.0 (cette version) (v0.3.0 (this release))** est cette version. **v0.2.0 (version précédente) (v0.2.0 (previous release))** est celle d'avant. Le benchmark difficile compare par rapport à **Main avant v0.3.0 (Main before v0.3.0)**, la fiche sur la branche main juste avant cette version, car v0.2.0 elle-même n'a pas été exécutée dessus.

### Tâches difficiles : corrections de bugs réels

18 pull requests fusionnées issues de 12 projets Python open source (Django, Sphinx, pylint, sympy, click et d'autres). La discussion part du commit antérieur au correctif avec le texte du ticket, et est notée par les tests ajoutés par les mainteneurs, qu'elle ne voit jamais. 3 exécutions par tâche, 54 par configuration.

| Configuration | Coût par exécution | Multiple vs Sans Token Beggar | Résolus |
| --- | --- | --- | --- |
| Sans Token Beggar | $0.69 | 1.00x | 70% |
| Main avant v0.3.0 | $0.45 | 1.54x (1.46 to 1.64) | 65% |
| v0.3.0 (cette version) | $0.49 | 1.42x (1.33 to 1.51) | 69% |

<p align="center"><img src="assets/chart-hard-cost.svg" alt="Graphique à barres : facteur de réduction de quota et d'argent par rapport à Sans Token Beggar sur les tâches difficiles, par tâche. Toutes les tâches : 1.54x pour Main avant v0.3.0 et 1.42x pour v0.3.0. Une ligne en pointillés marque 1.0x, aucune économie."></p>

<p align="center"><em>17 des 18 tâches difficiles coûtent moins cher avec Token Beggar, et la seule ayant coûté plus cher (structlog-exception-outside) a coûté environ 10% de plus.</em></p>

<p align="center"><img src="assets/chart-hard-quality.svg" alt="Graphique à barres : part des tâches difficiles où le problème a été corrigé, par tâche. Toutes les tâches : 70% Sans Token Beggar, 65% Main avant v0.3.0, 69% v0.3.0."></p>

<p align="center"><em>La part de problèmes corrigés reste proche du travail en solitaire, confirmant que l'économie ne se paie pas sur la qualité.</em></p>

Le coût diminue d'environ un tiers et la proportion de problèmes corrigés reste équivalente. Main avant v0.3.0 était encore plus économique mais en résolvait moins, et sur click-format-filename il s'est arrêté après 2 tours avec une mauvaise correction (0 sur 3, contre 3 sur 3 seul). v0.3.0 réinvestit une partie de cette économie dans la lecture du diff complet avant de répondre. C'est pour cette raison qu'elle est livrée.

Ce que cela ne montre pas : une qualité de code égale. Une évaluation à l'aveugle par un petit modèle a moins bien noté les diffs de v0.3.0 (0.94 sur une échelle de 0 à 2, contre 1.33 seul), et elle ne concorde que faiblement avec les tests cachés. Le temps passé est équivalent au travail en solitaire (168 secondes contre 187), pas plus rapide.

### Tâches simples

28 tâches simples réparties en 7 classes, 3 exécutions chacune, 84 exécutions par configuration. 21 ont servi à l'ajustement et 7 ont été réservées. Ce benchmark a été exécuté avant que v0.3.0 n'existe, sa dernière colonne est donc Main avant v0.3.0. Les tâches simples restent dans la discussion dans les deux fiches, v0.3.0 devrait donc donner des résultats similaires, mais elle n'a pas été réexécutée.

| Groupe | Sans Token Beggar | v0.2.0 (version précédente) | Main avant v0.3.0 | Main avant v0.3.0 vs sans |
| --- | --- | --- | --- | --- |
| Ensemble des 28 tâches | $0.148 | $0.139 | $0.134 | 1.11x (1.08 to 1.14) |
| Les 7 tâches réservées | $0.134 | $0.136 | $0.129 | 1.04x (0.99 to 1.11) |
| Plusieurs fichiers | $0.260 | $0.194 | $0.185 | 1.40x (1.27 to 1.55) |
| Code de routine | $0.152 | $0.149 | $0.132 | 1.15x (1.09 to 1.22) |

<p align="center"><img src="assets/chart-small-cost.svg" alt="Graphique à barres : facteur de réduction de quota et d'argent par rapport à Sans Token Beggar sur les tâches simples, par classe, pour v0.2.0 et Main avant v0.3.0. Une ligne en pointillés marque 1.0x, aucune économie."></p>

<p align="center"><em>Sur les tâches simples, seule la catégorie multifichier permet une économie nette ; le reste se tient près de la ligne en pointillés.</em></p>

<p align="center"><img src="assets/chart-small-quality.svg" alt="Graphique à barres : qualité moyenne sur les tâches simples par classe. Toutes les tâches simples : 0.96 Sans Token Beggar, 0.96 v0.2.0, 0.99 Main avant v0.3.0."></p>

<p align="center"><em>La qualité des réponses sur les tâches simples n'a diminué dans aucune configuration.</em></p>

Les tâches simples permettent peu d'économies. Les cinq autres classes (modifications mécaniques, lecture, débogage, conception, revue) se situent entre 0.97x et 1.09x, dans la marge de bruit. Le résultat mixte (1.11x) reste sous la barre des 1.15x, il n'est donc pas considéré comme une économie, et sur les tâches réservées il s'inscrit dans la dispersion du travail en solitaire. Un coût initial d'environ $0.10 par worker représente la majeure partie d'une tâche à $0.15, ce qui explique pourquoi les tâches simples restent dans la discussion. La qualité des réponses n'a baissé dans aucune configuration.

> [!IMPORTANT]
> **Où cela aide et où cela n'aide pas.** Cela aide sur les tâches volumineuses avec Opus 5.5 à effort high (1.42x, mesuré), ainsi qu'à tous les efforts de Fable 5.1 et Opus au maximum, où les tâches simples enregistrent aussi une économie. Sur Opus à d'autres niveaux d'effort et sur Sonnet 5.5, il conserve les tâches simples dans la discussion et confie les tâches volumineuses à un worker. L'économie sur les tâches volumineuses n'est mesurée que pour Opus high, donc sur Sonnet elle n'est pas mesurée et le pied de page indique le coût sans multiplicateur. Sur Haiku 5.5, le modèle le moins cher, il n'intervient pas. Si vous réalisez principalement de petites modifications sur un seul fichier, attendez-vous à un résultat quasiment inchangé.

Les tableaux, la liste des tâches, les leviers essayés puis abandonnés (lecture groupée avec un outil externe, compactage précoce) et la procédure pour tout reproduire se trouvent dans [docs/benchmark.md](docs/benchmark.md). Chaque exécution brute est archivée dans [`benchmark/results`](benchmark/results).

## Fonctionnement

1. **Déterminer le mode.** Le modèle et l'effort de votre discussion sélectionnent un des trois modes depuis `data/measured.json`. `full` (l'ensemble des modèles, efforts et outils externes) lorsque les tâches simples ont mesuré une économie de 1.15x ou plus, ou lorsque le modèle n'a jamais été évalué. `sized` partout ailleurs. `off` pour le modèle le moins cher. `token-beggar mode --all` affiche la grille, et `TOKEN_BEGGAR_MODE=full|sized|off` en force un.
2. **Évaluer la taille de la tâche.** En mode `sized`, la fiche indique que « small » signifie de la traiter dans la discussion, et « large » d'envoyer à un unique worker l'ensemble reproduire, explorer, corriger et exécuter les tests. Large désigne un problème dans un dépôt que le modèle n'a pas lu, plus d'environ 5 appels d'outils, plus d'un fichier ou une boucle d'édition et de test. Une tâche simple qui grandit au-delà d'environ 5 étapes devient large.
3. **Vérifier le travail du worker.** Le worker fait un compte-rendu en moins de 150 mots et énumère chaque endroit partageant le symptôme. La discussion lit le `git diff` complet, lance les tests, vérifie cette liste et renvoie le même worker s'il manque quelque chose.
4. **Respecter le plafond.** Le modèle et l'effort de votre discussion plafonnent ce qui peut être attribué aux modèles du même fournisseur. Sur Sonnet medium, rien ne part vers Opus ni vers un effort high.
5. **Rendre compte.** Le hook Stop ajoute le pied de page. Le modèle ne l'écrit pas, le chiffre ne peut donc pas être inventé dans le texte.

D'où viennent les seuils : 1.15x correspond à peu près à la dispersion observée lors d'exécutions répétées, un ratio inférieur n'est donc pas qualifié d'économie. Le ratio de 1.42x sur les tâches volumineuses provient du benchmark difficile ci-dessus. Détails dans [docs/benchmark.md](docs/benchmark.md#models-and-efforts).

### Articulation d'ensemble

- **Skill** : les règles de routage lues par la discussion. [`skills/token-beggar/SKILL.md`](skills/token-beggar/SKILL.md), expliquées dans [docs/usage.md](docs/usage.md).
- **Hooks** : sept petits hooks qui insèrent la fiche, maintiennent les workers sous le plafond, protègent le compactage et ajoutent le pied de page. [docs/on-your-machine.md](docs/on-your-machine.md).
- **Worker** : un agent doté de six outils qui effectue le travail délégué. [`agents/beggar-worker.md`](agents/beggar-worker.md), voir [docs/architecture.md](docs/architecture.md).
- **CLI** : `token-beggar` pour `doctor`, `mode`, `stats`, `inventory`, `ask` et plus encore. [docs/usage.md](docs/usage.md#commands).

Il sécurise aussi les longues sessions. Il repère le moment où l'hôte compacte le contexte, invite la discussion à sauvegarder une brève note avant, peut différer un compactage automatique au milieu d'une étape, et réintègre la note après. Voir [docs/architecture.md](docs/architecture.md).

## Ce qu'il fait sur votre machine

> [!NOTE]
> Tout ce qui suit est également détaillé dans [docs/on-your-machine.md](docs/on-your-machine.md), avec le tableau des hooks.

- **Lit** : la transcription de la session en cours (pour évaluer le coût et obtenir la taille du contexte ainsi que le modèle), les drapeaux de lancement du processus de discussion via `ps`, et les fichiers d'environnement et de paramètres pour le modèle et l'effort. Rien de tout cela ne quitte votre machine.
- **Exécute** : sept hooks qui appellent `python3 -m token_beggar hook <name>`. Un hook qui échoue consigne l'erreur et se termine par 0, ne bloquant ainsi jamais votre session. Les workers s'exécutent selon vos propres règles de permissions.
- **Envoie** : un téléchargement hebdomadaire de la page publique des modèles du fournisseur, afin de garder les tarifs à jour (`TOKEN_BEGGAR_OFFLINE=1` l'interrompt). Aucun texte n'est transmis à un outil d'IA externe (`agy`, `gemini`, `codex`) sauf si vous l'avez installé et le nommez expressément, ou si une lecture atteint environ 100k tokens ou plus. Les noms de fichiers et textes ressemblant à des clés secrètes sont refusés.
- **Écrit** : un unique dossier, `~/.claude/token-beggar`. Aucun paramètre d'agent, aucun fichier dans votre projet.
- **Désactivation** : `TOKEN_BEGGAR=off` pour un shell, un fichier nommé `off` dans ce dossier de façon permanente, ou `/plugin uninstall token-beggar`.

## Configuration

Vous n'avez besoin d'aucune configuration. Les valeurs par défaut découlent des mesures.

| Paramètre | Description |
| --- | --- |
| `TOKEN_BEGGAR=off` | Désactivé pour ce shell |
| `TOKEN_BEGGAR_MODE=full\|sized\|off` | Force un mode à la place de celui mesuré |
| `TOKEN_BEGGAR_EARLY=1` | Propose un compactage précoce sur les longues sessions (mesuré comme plus cher, donc inactif) |
| `TOKEN_BEGGAR_OFFLINE=1` | Pas de téléchargement hebdomadaire |
| `token-beggar cap agy flash` | Restreint un outil externe à ses modèles flash |

L'ensemble des réglages, y compris des consignes comme « no gemini » : [docs/config.md](docs/config.md).

## Limites

- Les tâches simples permettent peu d'économies. En dessous d'environ 1.15x, il est impossible de faire la différence avec l'absence de gain, et le résultat mixte des tâches simples (1.11x) se situe en dessous.
- Le benchmark difficile ne couvre qu'un modèle de discussion et effort (Opus 5.5, high) et des projets Python. Sonnet, Haiku et Fable sur des tâches volumineuses ne sont pas mesurés.
- Une résolution de 69% contre 70% correspond à une égalité dans la marge de variation, et l'évaluation à l'aveugle a moins bien noté les diffs de v0.3.0. Il n'est pas démontré que le code soit aussi bon.
- La version v0.2.0 publiée n'a pas été exécutée sur les tâches difficiles, et v0.3.0 n'a pas été réexécutée sur les tâches simples.
- Aucune économie provenant d'outils d'IA externes n'a été constatée sur les petits fichiers, et Gemini n'a pas été mesuré. Les lectures volumineuses ne sont pas mesurées.
- Le compactage précoce a coûté plus cher dans l'unique longue session testée, il est donc facultatif.
- Le pied de page est estimé à partir d'un ratio mesuré, et non de votre tâche. Les hooks ne pouvant pas voir le modèle de discussion, celui-ci est déduit de la transcription, puis des drapeaux du processus, de l'environnement et des paramètres. Si aucun ne l'indique, la fiche mentionne que le plafond est inconnu.
- Les workers chargent le fichier de mémoire de votre projet comme n'importe quelle session. Les projets du benchmark n'en possèdent aucun, ce coût ne figure donc pas dans les chiffres.

## FAQ

**Cela modifie-t-il mes réponses ?** Sur les tâches difficiles, il a corrigé 69% des problèmes contre 70% seul, une égalité dans la marge de variation. Il ne prétend pas que le code soit d'une qualité équivalente.

**Pourquoi n'y a-t-il parfois aucun pied de page ?** Il n'en affiche un que lorsqu'un élément a été routé et qu'une économie de 1.15x ou plus a été mesurée pour votre modèle, votre effort et le type de tâche.

**Pourquoi ne fait-il rien sur Sonnet ou Haiku ?** Haiku est le modèle le moins cher, il n'y a donc rien de moins cher à qui confier du travail. Sur Sonnet, les tâches simples ont mesuré une perte (environ 0.85x), elles restent donc dans la discussion, et l'économie sur les tâches volumineuses n'a pas été mesurée.

**Consomme-t-il mon quota ?** Le worker utilise votre quota Claude habituel sur un modèle moins cher. Les outils d'IA externes consomment leur propre quota et rien du vôtre.

**Quelque chose est-il envoyé à un serveur ?** Uniquement le téléchargement hebdomadaire de la page des modèles, qui ne transporte aucune donnée sur vous, et les fichiers confiés à un outil externe nommé. Voir [ce qu'il fait sur votre machine](#ce-quil-fait-sur-votre-machine).

**Quels autres outils sont comparables ?** Les proxys de routage envoient des requêtes d'API à d'autres fournisseurs selon le scénario, la variable de modèle de sous-agent fixe un modèle unique aux sous-agents, et les compteurs comme ccusage rapportent les dépenses a posteriori. Token Beggar opère au sein de la session, évalue la tâche et le plafond, et son multiple provient d'un benchmark, non de votre historique. Il se combine avec des prompts plus courts et des contextes plus réduits. Si un outil manque ici, ouvrez une issue.

## Documentation

| Objectif | Point de départ |
| --- | --- |
| L'installer ou l'essayer pour une session | [docs/install.md](docs/install.md) |
| Découvrir ce qu'il route et les commandes | [docs/usage.md](docs/usage.md) |
| Voir ce qu'il fait sur votre machine | [docs/on-your-machine.md](docs/on-your-machine.md) |
| Modifier un paramètre ou une règle | [docs/config.md](docs/config.md) |
| Comprendre les composants et les modes | [docs/architecture.md](docs/architecture.md) |
| Vérifier les chiffres ou les reproduire | [docs/benchmark.md](docs/benchmark.md) |
| Voir les nouveautés | [CHANGELOG.md](CHANGELOG.md) |

## Développement

```
python3 -m unittest discover -s tests -t .
cd benchmark && python3 selftest.py
uvx ruff check . && uvx ruff format --check .
```

## Contribution

Les issues et pull requests sont les bienvenues. Toute modification apportée à la fiche, au skill ou à `data/profiles.json` requiert une exécution de benchmark avant et après, avec mention des pertes à côté des gains. Voir [CONTRIBUTING.md](CONTRIBUTING.md).

## Licence

MIT © Arthur031221

Assisted by Claude/Codex.
