# Token Beggar 🪙: Gleiche Antworten, kleinere Rechnung

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner-dark.svg">
  <img src="assets/banner-light.svg" alt="Token Beggar: Gleiche Antworten, kleinere Rechnung. Sendet jede Aufgabe an das günstigste Modell, das sie noch richtig erledigt." width="100%">
</picture>

<p align="center">
  <a href="https://github.com/Arthur031221/Token-Beggar/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/Arthur031221/Token-Beggar/ci.yml?branch=main&style=flat-square&label=CI" alt="CI"></a>
  <a href="https://github.com/Arthur031221/Token-Beggar/releases"><img src="https://img.shields.io/github/v/release/Arthur031221/Token-Beggar?style=flat-square&label=release" alt="Release"></a>
  <a href="pyproject.toml"><img src="https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square" alt="Python 3.10+"></a>
  <a href="pyproject.toml"><img src="https://img.shields.io/badge/dependencies-zero-brightgreen?style=flat-square" alt="Keine Abhängigkeiten"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/Arthur031221/Token-Beggar?style=flat-square" alt="Lizenz"></a>
</p>

[English](README.md) | [繁體中文](README.zh-TW.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [Português](README.pt-BR.md)

Token Beggar ist ein Plugin für Claude Code. Bevor das große Modell eine Aufgabe ausführt, prüft es, ob ein günstigeres Modell sie genauso gut erledigen kann. Kleine Aufgaben verbleiben im Chat. Eine große Aufgabe, wie das Beheben eines Fehlers in einem noch nicht gelesenen Repository, geht an einen günstigeren Worker, und der Chat prüft anschließend das gesamte Diff und führt die Tests aus. Design, Ursachenanalyse und die finale Antwort verbleiben bei dem von dir gewählten Modell.

**Bei 18 echten Fehlerbehebungen kostete es 1.42x weniger Kontingent und Geld als die Arbeit allein, bei gleichem Anteil bestandener verdeckter Tests (69% gegenüber 70%).**

Es läuft auf deinem Rechner, in deiner Claude-Code-Sitzung. Es nutzt das Claude Code, bei dem du bereits angemeldet bist, sendet nichts über dich irgendwohin und schreibt nur in seinen eigenen Ordner. [Genau das, was es tut](docs/on-your-machine.md).

[Installation](#installation) · [Schnellstart](#schnellstart) · [Ergebnisse](#ergebnisse) · [Funktionsweise](#funktionsweise) · [FAQ](#faq) · [Dokumentation](#dokumentation) · [Changelog](CHANGELOG.md)

<p align="center"><img src="assets/demo.gif" width="760" alt="Terminal recording of the routing card, the compaction guard and the benchmark table"></p>

> [!TIP]
> Nicht sicher, ob es funktioniert? Führe `token-beggar doctor` aus. Es listet auf, was das Routing stillschweigend stoppen kann, und beendet sich mit 1, wenn etwas beschädigt ist.

## Installation

Erfordert Claude Code und Python 3.10 oder neuer. Es verwendet ausschließlich die Standardbibliothek.

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

Starte den Agenten neu oder führe `/reload-plugins` aus. Mehr dazu in [docs/install.md](docs/install.md), einschließlich der Verwendung des Skills in einem anderen Agenten, der Skills liest.

## Schnellstart

Arbeite wie gewohnt. Beim ersten echten Prompt einer Sitzung fügt ein Hook eine kurze Routing-Karte hinzu, und das Chat-Modell schätzt die Aufgabengröße ein. Am Ende einer Antwort, bei der etwas weitergeleitet und eine Ersparnis gemessen wurde, erhältst du eine Zeile:

```
Token Beggar: about 1.4x less quota than Opus 5.5 high alone, saved about $0.21 (est.) | large task | routed 1: haiku medium x1
```

Der Faktor ist das gemessene Verhältnis der Listenpreiskosten ohne Token Beggar zu denen mit Token Beggar für dein Modell und deinen Effort. Der Dollarbetrag entspricht den eigenen Kosten der Antwort multipliziert mit diesem Verhältnis minus eins. Beides sind Schätzungen und weisen dies auch aus. Die Zeile zählt niemals Tokens, und unter 1.15x wird kein Faktor angegeben, da dies innerhalb der Streuung von Durchlauf zu Durchlauf liegt.

Um es für einen Prompt zu aktivieren, der es nicht ausgelöst hat, gib `/token-beggar` ein. Bestätige anschließend, dass die Hooks laufen:

```
token-beggar doctor
```

## Ergebnisse

Zwei Setups, und nur zwei. **Ohne Token Beggar** ist das Chat-Modell, das allein arbeitet, so wie du es normalerweise nutzt. **Mit Token Beggar** ist die mit diesem Release ausgelieferte Karte, Version 0.3.0. Opus 5.5 bei hohem Effort ist das Chat-Modell. Die Kosten entsprechen dem Listenpreis für den Chat und jeden Worker, einschließlich Cache. Intervalle betragen 95 Prozent.

Schwere Aufgaben sind 18 gemergte Pull Requests aus 12 Open-Source-Python-Projekten (Django, Sphinx, pylint, sympy, click und andere). Der Chat startet beim Commit vor dem Fix mit dem Issue-Text und wird anhand der von den Maintainern hinzugefügten Tests bewertet, die er nie zu sehen bekommt. 3 Durchläufe pro Aufgabe, 54 pro Setup.

| Setup | Kosten pro Aufgabe | Faktor | Gelöste Issues |
| --- | --- | --- | --- |
| Ohne Token Beggar | $0.69 | 1.00x | 70% |
| Mit Token Beggar | $0.49 | 1.42x weniger (1.33 to 1.51) | 69% |

<p align="center"><img src="assets/chart-hard-cost.svg" alt="Balkendiagramm: Faktor an weniger Kontingent und Geld mit Token Beggar als ohne, pro schwerer Aufgabe. Alle Aufgaben: 1.42x. Eine gestrichelte Linie markiert 1.0x, die Kosten ohne Token Beggar."></p>

<p align="center"><em>17 der 18 Aufgaben kosteten mit Token Beggar weniger. Die eine, die mehr kostete (structlog-exception-outside), kostete etwa 10% mehr.</em></p>

Die Kosten sinken um 29 Prozent und der Anteil gelöster Issues bleibt gleichauf (69% gegenüber 70% ist ein Gleichstand innerhalb der Streuung). Die Zeit liegt ebenfalls gleichauf (168 Sekunden gegenüber 187), nicht schneller.

Kleine Aufgaben wurden nur mit einer früheren Karte gemessen, nicht mit 0.3.0. Sie sparten dort wenig (1.11x, unter der Schwelle von 1.15x, ab der eine Ersparnis geltend gemacht wird), und sie verbleiben im Chat, rechne also bei kleinen Ein-Datei-Änderungen mit so gut wie keiner Veränderung.

Vollständige Benchmark-Details, die Aufgabenliste und wie sich alles reproduzieren lässt: [docs/benchmark.md](docs/benchmark.md). Jeder Rohdurchlauf befindet sich in [`benchmark/results`](benchmark/results).

> [!IMPORTANT]
> **Wo es hilft und wo nicht.** Es hilft bei großen Aufgaben mit Opus 5.5 bei hohem Effort (1.42x, gemessen) sowie bei jedem Effort von Fable 5.1 und Opus bei max, wo auch bei kleinen Aufgaben eine Ersparnis gemessen wurde. Bei Opus mit anderen Efforts und bei Sonnet 5.5 belässt es kleine Aufgaben im Chat und sendet große an einen Worker. Die Ersparnis bei großen Aufgaben wurde nur für Opus high gemessen; bei Sonnet ist sie daher ungemessen, und die Fußzeile nennt die Kosten dann ohne Faktor. Bei Haiku 5.5, dem günstigsten Modell, tut es nichts. Wenn du überwiegend kleine Ein-Datei-Änderungen durchführst, ist mit so gut wie keiner Veränderung zu rechnen.

## Funktionsweise

1. **Modus nachschlagen.** Das Modell und der Effort deines Chats wählen einen von drei Modi aus `data/measured.json`. `full` (das gesamte Menü an Modellen, Efforts und externen Tools), wenn bei kleinen Aufgaben eine Ersparnis von 1.15x oder mehr gemessen wurde oder das Modell nie gemessen wurde. `sized` überall sonst. `off` für das günstigste Modell. `token-beggar mode --all` gibt das Raster aus, und `TOKEN_BEGGAR_MODE=full|sized|off` erzwingt einen Modus.
2. **Aufgabengröße bestimmen.** Im Modus `sized` besagt die Karte: Klein bedeutet im Chat erledigen, und groß bedeutet, einem Worker die gesamte Liste aus Reproduzieren, Erkunden, Beheben und Ausführen der Tests zu übergeben. Groß bedeutet ein Issue in einem Repository, das das Modell noch nicht gelesen hat, mehr als etwa 5 Tool-Aufrufe, mehr als eine Datei oder eine Schleife aus Bearbeiten und Testen. Eine kleine Aufgabe, die über etwa 5 Schritte hinaus anwächst, wird zu einer großen Aufgabe.
3. **Arbeit des Workers prüfen.** Der Worker berichtet in unter 150 Wörtern und listet jede Stelle auf, die das gleiche Symptom aufweist. Der Chat liest das gesamte `git diff`, führt die Tests aus, prüft diese Liste und schickt denselben Worker zurück, falls etwas fehlt.
4. **Obergrenze einhalten.** Das Modell und der Effort deines Chats deckeln, was Modelle desselben Anbieters erhalten. Bei Sonnet medium geht nichts an Opus oder an high Effort.
5. **Berichten.** Der Stop-Hook fügt die Fußzeile hinzu. Das Modell schreibt sie nicht selbst, sodass die Zahl im Fließtext nicht erfunden werden kann.

Woher die Schwellenwerte stammen: 1.15x entspricht in etwa der bei wiederholten Durchläufen beobachteten Streuung, daher wird ein kleineres Verhältnis nicht als Ersparnis bezeichnet. Das Verhältnis von 1.42x bei großen Aufgaben stammt aus dem obigen schweren Benchmark. Details in [docs/benchmark.md](docs/benchmark.md#models-and-efforts).

### Wie alles zusammenhängt

- **Skill**: Die Routing-Regeln, die der Chat liest. [`skills/token-beggar/SKILL.md`](skills/token-beggar/SKILL.md), erklärt in [docs/usage.md](docs/usage.md).
- **Hooks**: Sieben kleine Hooks, die die Karte hinzufügen, Worker an die Obergrenze binden, die Komprimierung absichern und die Fußzeile anhängen. [docs/on-your-machine.md](docs/on-your-machine.md).
- **Worker**: Ein Agent mit sechs Tools, der die delegierte Arbeit erledigt. [`agents/beggar-worker.md`](agents/beggar-worker.md), siehe [docs/architecture.md](docs/architecture.md).
- **CLI**: `token-beggar` für `doctor`, `mode`, `stats`, `inventory`, `ask` und mehr. [docs/usage.md](docs/usage.md#commands).

Es sichert auch lange Sitzungen ab. Es erkennt den Punkt, an dem der Host den Kontext komprimiert, bittet den Chat davor um eine kurze Notiz, kann eine automatische Komprimierung mitten in einem Schritt aufschieben und fügt die Notiz danach wieder ein. Siehe [docs/architecture.md](docs/architecture.md).

## Was es auf deinem Rechner tut

> [!NOTE]
> Alles Folgende steht zusammen mit der Hook-Tabelle auch in [docs/on-your-machine.md](docs/on-your-machine.md).

- **Liest**: Das Transkript der aktuellen Sitzung (zur Erfassung der Kosten sowie zur Ermittlung der Kontextgröße und des Modells), die Start-Flags des Chat-Prozesses über `ps` sowie die Umgebungs- und Einstellungsdateien für Modell und Effort. Nichts davon verlässt deinen Rechner.
- **Führt aus**: Sieben Hooks, die `python3 -m token_beggar hook <name>` aufrufen. Ein fehlgeschlagener Hook protokolliert den Fehler und beendet sich mit 0, sodass deine Sitzung nie unterbrochen wird. Worker laufen unter deinen eigenen Berechtigungseinstellungen.
- **Sendet**: Einen wöchentlichen Download der öffentlichen Modellseite des Anbieters, um Preise aktuell zu halten (`TOKEN_BEGGAR_OFFLINE=1` stoppt dies). Text geht nur an ein externes KI-Tool (`agy`, `gemini`, `codex`), wenn du es installiert hast und ausdrücklich nennst oder ein Lesevorgang etwa 100k Tokens oder mehr umfasst. Dateinamen und Texte, die wie Schlüssel aussehen, werden verweigert.
- **Schreibt**: Einen einzigen Ordner, `~/.claude/token-beggar`. Keine Agenten-Einstellungen, keine Dateien in deinem Projekt.
- **Deaktivieren**: `TOKEN_BEGGAR=off` für eine Shell, eine Datei namens `off` in diesem Ordner für dauerhaft, oder `/plugin uninstall token-beggar`.

## Konfiguration

Es ist keine erforderlich. Die Standardwerte stammen aus den Messungen.

| Einstellung | Wirkung |
| --- | --- |
| `TOKEN_BEGGAR=off` | Aus für diese Shell |
| `TOKEN_BEGGAR_MODE=full\|sized\|off` | Modus erzwingen statt des gemessenen |
| `TOKEN_BEGGAR_EARLY=1` | Frühe Komprimierung bei langen Sitzungen vorschlagen (kostete bei Messungen mehr, daher aus) |
| `TOKEN_BEGGAR_OFFLINE=1` | Kein wöchentlicher Download |
| `token-beggar cap agy flash` | Externes Tool auf seine Flash-Modelle beschränken |

Alles Weitere, einschließlich Prompts wie "no gemini": [docs/config.md](docs/config.md).

## Grenzen

- Kleine Aufgaben sparen wenig. Unter etwa 1.15x lässt es sich nicht von keiner Ersparnis unterscheiden, und das Ergebnis bei kleinen Aufgaben von der früheren Karte (1.11x) liegt darunter.
- Der schwere Benchmark deckt ein einziges Chat-Modell und einen Effort ab (Opus 5.5, high) sowie Python-Projekte. Sonnet, Haiku und Fable bei großen Aufgaben sind nicht gemessen.
- 69% gegenüber 70% gelösten Aufgaben ist ein Gleichstand innerhalb der Streuung, und ein Blind-Review durch ein kleines Modell bewertete die Diffs von v0.3.0 schlechter als die Arbeit allein (0.94 gegenüber 1.33 auf einer Skala von 0 bis 2), obwohl es nur schwach mit den Tests übereinstimmt, sodass nicht belegt ist, dass der Code gleich gut ist.
- v0.3.0 wurde auf den kleinen Aufgaben nicht erneut ausgeführt.
- Bei kleinen Dateien wurde durch externe KI-Tools keine Ersparnis festgestellt, und Gemini wurde nicht gemessen. Große Lesevorgänge sind ungemessen.
- Frühe Komprimierung kostete in der einen getesteten langen Sitzung mehr, daher ist sie Opt-in.
- Die Fußzeile wird anhand eines gemessenen Verhältnisses geschätzt, nicht anhand deiner konkreten Aufgabe. Hooks können das Chat-Modell nicht einsehen; daher wird es aus dem Transkript, danach aus den Prozess-Flags, der Umgebung und den Einstellungen ausgelesen. Wenn keines davon Aufschluss gibt, meldet die Karte, dass die Obergrenze unbekannt ist.
- Worker laden wie jede Sitzung deine Projekt-Memory-Datei. Die Benchmark-Projekte besitzen keine, daher sind diese Kosten nicht in den Zahlen enthalten.

## FAQ

**Verändert es meine Antworten?** Bei den schweren Aufgaben wurden 69% der Issues behoben gegenüber 70% allein, ein Gleichstand innerhalb der Streuung. Es wird nicht behauptet, dass der Code die gleiche Qualität hat.

**Warum gibt es manchmal keine Fußzeile?** Eine Fußzeile wird nur ausgegeben, wenn etwas weitergeleitet wurde und eine Ersparnis von 1.15x oder mehr für dein Modell, deinen Effort und die Art der Aufgabe gemessen wurde.

**Tut es bei Sonnet oder Haiku etwas?** Bei Haiku nichts, weil es das günstigste Modell ist und es nichts Günstigeres gibt, an das Arbeit delegiert werden könnte. Bei Sonnet ergaben kleine Aufgaben einen Verlust (etwa 0.85x), weshalb sie im Chat verbleiben, und große Aufgaben gehen an einen Worker, aber die Ersparnis bei großen Aufgaben wurde nicht gemessen.

**Verbraucht es mein Kontingent?** Der Worker verbraucht dein normales Claude-Kontingent bei einem günstigeren Modell. Externe KI-Tools verbrauchen ihr eigenes Kontingent und nichts von deinem.

**Wird etwas an einen Server gesendet?** Nur der wöchentliche Download der Modellseite, der keinerlei Daten über dich überträgt, und Dateien, die du einem von dir benannten externen Tool übergibst. Siehe [Was es auf deinem Rechner tut](#was-es-auf-deinem-rechner-tut).

**Welche anderen Tools sind vergleichbar?** Router-Proxys senden API-Anfragen je nach Szenario an andere Anbieter, die Subagent-Modellvariable bindet ein bestimmtes Modell an Subagenten, und Messwerkzeuge wie ccusage melden Ausgaben im Nachhinein. Token Beggar arbeitet innerhalb der Sitzung, stuft die Aufgabe sowie die Obergrenze ein, und sein Faktor stammt aus einem Benchmark, nicht aus deinem Verlauf. Es lässt sich mit kürzeren Prompts und kleineren Kontexten kombinieren. Falls hier ein Tool fehlt, öffne ein Issue.

## Dokumentation

| Ziel | Hier starten |
| --- | --- |
| Installieren oder für eine Sitzung ausprobieren | [docs/install.md](docs/install.md) |
| Weiterleitungsregeln und Befehle kennenlernen | [docs/usage.md](docs/usage.md) |
| Sehen, was es auf deinem Rechner tut | [docs/on-your-machine.md](docs/on-your-machine.md) |
| Eine Einstellung oder Regel ändern | [docs/config.md](docs/config.md) |
| Die Komponenten und Modi verstehen | [docs/architecture.md](docs/architecture.md) |
| Zahlen prüfen oder reproduzieren | [docs/benchmark.md](docs/benchmark.md) |
| Sehen, was sich geändert hat | [CHANGELOG.md](CHANGELOG.md) |

## Entwicklung

```
python3 -m unittest discover -s tests -t .
cd benchmark && python3 selftest.py
uvx ruff check . && uvx ruff format --check .
```

## Mitwirken

Issues und Pull Requests sind willkommen. Eine Änderung an der Karte, dem Skill oder `data/profiles.json` erfordert einen Benchmark-Durchlauf davor und danach, wobei Verluste neben Gewinnen ausgewiesen werden müssen. Siehe [CONTRIBUTING.md](CONTRIBUTING.md).

## Lizenz

MIT © Arthur031221

Assisted by Claude/Codex.
