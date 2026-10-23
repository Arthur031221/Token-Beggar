# Token Beggar 🪙: mismas respuestas, una factura más baja

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner-dark.svg">
  <img src="assets/banner-light.svg" alt="Token Beggar: mismas respuestas, una factura más baja. Envía cada tarea al modelo más económico que aún así la resuelve correctamente." width="100%">
</picture>

<p align="center">
  <a href="https://github.com/Arthur031221/Token-Beggar/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/Arthur031221/Token-Beggar/ci.yml?branch=main&style=flat-square&label=CI" alt="CI"></a>
  <a href="https://github.com/Arthur031221/Token-Beggar/releases"><img src="https://img.shields.io/github/v/release/Arthur031221/Token-Beggar?style=flat-square&label=release" alt="Versión"></a>
  <a href="pyproject.toml"><img src="https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square" alt="Python 3.10+"></a>
  <a href="pyproject.toml"><img src="https://img.shields.io/badge/dependencies-zero-brightgreen?style=flat-square" alt="Cero dependencias"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/Arthur031221/Token-Beggar?style=flat-square" alt="Licencia"></a>
</p>

[English](README.md) | [繁體中文](README.zh-TW.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [Português](README.pt-BR.md)

Token Beggar es un plugin para Claude Code. Antes de que el modelo grande realice un trabajo, comprueba si un modelo más económico puede hacerlo igual de bien. Las tareas pequeñas se quedan en el chat. Una tarea grande, como corregir un error en un repositorio que aún no has leído, se envía a un worker más económico, y luego el chat revisa todo el diff y ejecuta las pruebas. El diseño, las causas raíz y la respuesta final se quedan con el modelo que elegiste.

**En 18 correcciones de errores reales costó 1.42x menos cuota y dinero que trabajando solo, con la misma proporción de pruebas ocultas aprobadas (69% frente a 70%).**

Se ejecuta en tu máquina, en tu sesión de Claude Code. Utiliza el Claude Code en el que ya has iniciado sesión, no envía nada sobre ti a ninguna parte y solo escribe en su propia carpeta. [Exactamente lo que hace](docs/on-your-machine.md).

[Instalación](#instalación) · [Inicio rápido](#inicio-rápido) · [Resultados](#resultados) · [Cómo funciona](#cómo-funciona) · [Preguntas frecuentes](#preguntas-frecuentes) · [Documentación](#documentación) · [Registro de cambios](CHANGELOG.md)

<p align="center"><img src="assets/demo.gif" width="760" alt="Terminal recording of the routing card, the compaction guard and the benchmark table"></p>

> [!TIP]
> ¿No estás seguro de si está funcionando? Ejecuta `token-beggar doctor`. Muestra lo que puede detener el enrutamiento de forma silenciosa y sale con código 1 cuando algo está roto.

## Instalación

Requiere Claude Code y Python 3.10 o posterior. Solo utiliza la biblioteca estándar.

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

Reinicia el agente o ejecuta `/reload-plugins`. Más información en [docs/install.md](docs/install.md), incluyendo cómo usar la skill en otro agente que lea skills.

## Inicio rápido

Trabaja como siempre lo haces. En el primer prompt real de una sesión, un hook añade una breve tarjeta de enrutamiento y el modelo de chat dimensiona la tarea. Al final de una respuesta donde algo fue enrutado y se midió un ahorro, obtienes una línea:

```
Token Beggar: about 1.4x less quota than Opus 5.5 high alone, saved about $0.21 (est.) | large task | routed 1: haiku medium x1
```

El multiplicador es la proporción medida del costo a precio de lista sin Token Beggar frente a con él, para tu modelo y effort. Los dólares son el costo propio de la respuesta multiplicado por esa proporción menos uno. Ambos son estimaciones y así lo indican. La línea nunca cuenta tokens, y por debajo de 1.15x no muestra ningún multiplicador, ya que eso queda dentro de la dispersión entre ejecuciones.

Para activarlo en un prompt que no lo activó, escribe `/token-beggar`. Luego confirma que los hooks se ejecutan:

```
token-beggar doctor
```

## Resultados

Dos configuraciones, y solo dos. **Sin Token Beggar** es el modelo de chat trabajando solo, de la forma en que lo usas normalmente. **Con Token Beggar** es la tarjeta distribuida en esta versión, versión 0.3.0. Opus 5.5 con effort high es el modelo de chat. El costo es el precio de lista para el chat y cada worker, caché incluida. Los intervalos son del 95 por ciento.

Las tareas difíciles son 18 pull requests fusionados de 12 proyectos open source en Python (Django, Sphinx, pylint, sympy, click y otros). El chat comienza desde el commit anterior a la corrección con el texto del issue, y es calificado por las pruebas que los mantenedores añadieron, las cuales nunca ve. 3 ejecuciones por tarea, 54 por configuración.

| Configuración | Costo por tarea | Multiplicador | Issues resueltos |
| --- | --- | --- | --- |
| Sin Token Beggar | $0.69 | 1.00x | 70% |
| Con Token Beggar | $0.49 | 1.42x menos (1.33 to 1.51) | 69% |

<p align="center"><img src="assets/chart-hard-cost.svg" alt="Gráfico de barras: veces menos cuota y dinero con Token Beggar que sin él, por tarea difícil. Todas las tareas: 1.42x. Una línea discontinua marca 1.0x, el costo sin Token Beggar."></p>

<p align="center"><em>17 de las 18 tareas costaron menos con Token Beggar. La que costó más (structlog-exception-outside) costó aproximadamente un 10% más.</em></p>

<p align="center"><img src="assets/chart-hard-quality.svg" alt="Gráfico de barras: proporción de incidencias resueltas en las 18 tareas difíciles, 70% sin Token Beggar y 69% con Token Beggar."></p>

<p align="center"><em>Sin Token Beggar se resolvió el 70% de las incidencias y con él el 69%: empate dentro de la dispersión, 54 ejecuciones por configuración.</em></p>

El costo se reduce en un 29 por ciento y la proporción de issues resueltos se mantiene al mismo nivel (69% frente a 70% es un empate dentro de la dispersión). El tiempo también está al mismo nivel (168 segundos frente a 187), no más rápido.

Las tareas pequeñas se midieron solo con una tarjeta anterior, no con 0.3.0. Ahorraron poco allí (1.11x, por debajo de la línea de 1.15x en la que se afirma un ahorro), y se quedan en el chat, por lo que no esperes prácticamente ningún cambio en pequeñas ediciones de un solo archivo.

Detalles completos del benchmark, la lista de tareas y cómo reproducirlo todo: [docs/benchmark.md](docs/benchmark.md). Cada ejecución sin procesar está en [`benchmark/results`](benchmark/results).

> [!IMPORTANT]
> **Dónde ayuda y dónde no.** Ayuda en tareas grandes con Opus 5.5 con effort high (1.42x, medido), y en todos los niveles de effort de Fable 5.1 y Opus en max, donde las tareas pequeñas también registran un ahorro. En Opus con otros niveles de effort y en Sonnet 5.5 mantiene las tareas pequeñas en el chat y envía las grandes a un worker. El ahorro en tareas grandes solo está medido para Opus high, por lo que en Sonnet no está medido y el pie de página indica el costo sin un multiplicador. En Haiku 5.5, el modelo más económico, no hace nada. Si principalmente realizas pequeñas ediciones de un solo archivo, no esperes prácticamente ningún cambio.

## Cómo funciona

1. **Consultar el modo.** El modelo y el effort de tu chat seleccionan uno de tres modos de `data/measured.json`. `full` (el menú completo de modelos, niveles de effort y herramientas externas) donde las tareas pequeñas midieron un ahorro de 1.15x o más, o el modelo nunca se midió. `sized` en todos los demás casos. `off` para el modelo más económico. `token-beggar mode --all` imprime la cuadrícula, y `TOKEN_BEGGAR_MODE=full|sized|off` fuerza uno.
2. **Dimensionar la tarea.** En modo `sized`, la tarjeta indica que pequeño significa hacerlo en el chat, y grande significa enviar a un worker la lista completa de reproducir, explorar, corregir y ejecutar las pruebas. Grande significa un issue en un repositorio que el modelo no ha leído, más de unas 5 llamadas a herramientas, más de un archivo o un ciclo de edición y prueba. Una tarea pequeña que supera unos 5 pasos se convierte en grande.
3. **Revisar el trabajo del worker.** El worker informa en menos de 150 palabras y lista cada sitio que comparte el síntoma. El chat lee todo el `git diff`, ejecuta las pruebas, revisa esa lista y envía de vuelta al mismo worker si falta algo.
4. **Respetar el límite superior.** El modelo y el effort de tu chat limitan lo que reciben los modelos del mismo proveedor. En Sonnet medium, nada va a Opus ni a effort high.
5. **Informar.** El hook Stop añade el pie de página. El modelo no lo escribe, por lo que el número no se puede inventar en prosa.

De dónde provienen los umbrales: 1.15x es aproximadamente la dispersión observada entre ejecuciones repetidas, por lo que una relación menor no se denomina ahorro. La relación de tareas grandes de 1.42x corresponde al benchmark difícil anterior. Detalles en [docs/benchmark.md](docs/benchmark.md#models-and-efforts).

### Cómo encaja todo

- **Skill**: las reglas de enrutamiento que lee el chat. [`skills/token-beggar/SKILL.md`](skills/token-beggar/SKILL.md), explicadas en [docs/usage.md](docs/usage.md).
- **Hooks**: siete hooks pequeños que añaden la tarjeta, mantienen a los workers dentro del límite superior, protegen la compactación y añaden el pie de página. [docs/on-your-machine.md](docs/on-your-machine.md).
- **Worker**: un agente con seis herramientas que realiza el trabajo delegado. [`agents/beggar-worker.md`](agents/beggar-worker.md), ver [docs/architecture.md](docs/architecture.md).
- **CLI**: `token-beggar` para `doctor`, `mode`, `stats`, `inventory`, `ask` y más. [docs/usage.md](docs/usage.md#commands).

También protege las sesiones largas. Detecta el punto donde el host compacta el contexto, le pide al chat que guarde una nota breve antes de ello, puede posponer una compactación automática en medio de un paso y vuelve a colocar la nota después. Ver [docs/architecture.md](docs/architecture.md).

## Qué hace en tu máquina

> [!NOTE]
> Todo lo que figura a continuación también se encuentra en [docs/on-your-machine.md](docs/on-your-machine.md), con la tabla de hooks.

- **Lee**: la transcripción de la sesión actual (para contabilizar el costo y determinar el tamaño del contexto y el modelo), los flags de inicio del proceso de chat mediante `ps`, y los archivos de entorno y configuración para el modelo y el effort. Nada de esto sale de tu máquina.
- **Ejecuta**: siete hooks que llaman a `python3 -m token_beggar hook <name>`. Un hook que falla registra el error y sale con código 0, por lo que nunca interrumpe tu sesión. Los workers se ejecutan bajo tu propia configuración de permisos.
- **Envía**: una descarga semanal de la página pública de modelos del proveedor, para mantener los precios actualizados (`TOKEN_BEGGAR_OFFLINE=1` la detiene). El texto solo se envía a una herramienta de IA externa (`agy`, `gemini`, `codex`) si la tienes instalada y la mencionas o si una lectura es de aproximadamente 100k tokens o más. Se rechazan los nombres de archivos y el texto que parezcan claves.
- **Escribe**: una sola carpeta, `~/.claude/token-beggar`. Sin configuraciones del agente, sin archivos en tu proyecto.
- **Desactivación**: `TOKEN_BEGGAR=off` para una terminal, un archivo llamado `off` en esa carpeta de forma definitiva, o `/plugin uninstall token-beggar`.

## Configuración

No necesitas ninguna. Los valores predeterminados proceden de las mediciones.

| Ajuste | Qué hace |
| --- | --- |
| `TOKEN_BEGGAR=off` | Desactivado para esta terminal |
| `TOKEN_BEGGAR_MODE=full\|sized\|off` | Fuerza un modo en lugar del medido |
| `TOKEN_BEGGAR_EARLY=1` | Sugiere compactación temprana en sesiones largas (se midió que costaba más, por lo que está desactivado) |
| `TOKEN_BEGGAR_OFFLINE=1` | Sin descarga semanal |
| `token-beggar cap agy flash` | Limita una herramienta externa a sus modelos flash |

Todo ello, incluidos prompts como "no gemini": [docs/config.md](docs/config.md).

## Límites

- Las tareas pequeñas ahorran poco. Por debajo de aproximadamente 1.15x no se distingue de ningún ahorro, y el resultado de tareas pequeñas de la tarjeta anterior (1.11x) está por debajo de esa cifra.
- El benchmark difícil cubre un único modelo de chat y effort (Opus 5.5, high) y proyectos de Python. Sonnet, Haiku y Fable en tareas grandes no están medidos.
- 69% frente a 70% de resolución es un empate dentro de la dispersión, y una revisión a ciegas realizada por un modelo pequeño calificó los diffs de v0.3.0 más bajo que trabajando solo (0.94 frente a 1.33 en una escala de 0 a 2), aunque solo coincide débilmente con las pruebas, por lo que no se demuestra que el código sea igual de bueno.
- v0.3.0 no se volvió a ejecutar en las tareas pequeñas.
- No se encontró ningún ahorro con herramientas de IA externas en archivos pequeños, y Gemini no fue medido. Las lecturas grandes no están medidas.
- La compactación temprana costó más en la única sesión larga probada, por lo que es opcional.
- El pie de página se estima a partir de una proporción medida, no de tu tarea. Los hooks no pueden ver el modelo de chat, por lo que se lee de la transcripción, luego de los flags del proceso, del entorno y de la configuración. Si ninguno lo indica, la tarjeta señala que el límite superior es desconocido.
- Los workers cargan el archivo de memoria de tu proyecto como cualquier sesión. Los proyectos del benchmark no tienen ninguno, por lo que ese costo no está en las cifras.

## Preguntas frecuentes

**¿Cambia mis respuestas?** En las tareas difíciles corrigió el 69% de los problemas frente al 70% en solitario, un empate dentro de la dispersión. No afirma que el código sea de igual calidad.

**¿Por qué a veces no hay pie de página?** Solo imprime uno cuando enrutó algo y se midió un ahorro de 1.15x o más para tu modelo, effort y tipo de tarea.

**¿Hace algo en Sonnet o Haiku?** En Haiku nada, porque es el modelo más económico y no hay nada más barato a lo que enviar trabajo. En Sonnet las tareas pequeñas midieron una pérdida (aproximadamente 0.85x), por lo que se quedan en el chat, y las tareas grandes van a un worker, pero el ahorro en tareas grandes no se midió.

**¿Consume mi cuota?** El worker gasta tu cuota habitual de Claude en un modelo más económico. Las herramientas de IA externas gastan su propia cuota y nada de la tuya.

**¿Se envía algo a algún servidor?** Solo la descarga semanal de la página de modelos, que no contiene datos sobre ti, y los archivos que entregues a una herramienta externa que hayas nombrado. Consulta [qué hace en tu máquina](#qué-hace-en-tu-máquina).

**¿Qué otras herramientas se le parecen?** Los proxies de enrutamiento envían solicitudes de API a otros proveedores según el escenario, la variable de modelo de subagente fija un modelo para los subagentes, y medidores como ccusage informan del gasto a posteriori. Token Beggar trabaja dentro de la sesión, califica la tarea y el límite superior, y su multiplicador proviene de un benchmark, no de tu historial. Se combina con prompts más cortos y contextos más pequeños. Si falta alguna herramienta aquí, abre un issue.

## Documentación

| Objetivo | Empieza aquí |
| --- | --- |
| Instalarlo, o probarlo durante una sesión | [docs/install.md](docs/install.md) |
| Aprender qué enruta y los comandos | [docs/usage.md](docs/usage.md) |
| Ver qué hace en tu máquina | [docs/on-your-machine.md](docs/on-your-machine.md) |
| Cambiar una configuración o una regla | [docs/config.md](docs/config.md) |
| Comprender las partes y los modos | [docs/architecture.md](docs/architecture.md) |
| Consultar los números o reproducirlos | [docs/benchmark.md](docs/benchmark.md) |
| Ver qué cambió | [CHANGELOG.md](CHANGELOG.md) |

## Desarrollo

```
python3 -m unittest discover -s tests -t .
cd benchmark && python3 selftest.py
uvx ruff check . && uvx ruff format --check .
```

## Contribuir

Los issues y pull requests son bienvenidos. Cualquier cambio en la tarjeta, la skill o en `data/profiles.json` requiere una ejecución del benchmark antes y después, reportando las pérdidas junto con las ganancias. Consulta [CONTRIBUTING.md](CONTRIBUTING.md).

## Licencia

MIT © Arthur031221

Assisted by Claude/Codex.
