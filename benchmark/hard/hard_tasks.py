"""Real open source tasks for the hard task benchmark: a closed issue, fixed by a merged pull request that added or changed tests.

Each task: the repository, the pull request, the issue (its text is the prompt), the merge commit of the fix (its first parent is the
commit the agent starts from), the test directories that are hidden from the agent and restored for scoring, the install command
and the test command. `hard.py prepare` fills in everything else (the issue text and the reference test results).
"""

PYTEST = "-m pytest -q -rA --no-header -p no:cacheprovider"

TASKS = [
    {
        "id": "md-footnote-order",
        "repo": "Python-Markdown/markdown",
        "pr": 1546,
        "issue": 1367,
        "exclude": ["by_definition"],
        "install": "-e . pytest pyyaml",
        "tests": ["tests"],
        "run": ["tests"],
    },
    {
        "id": "md-backslash-smarty",
        "repo": "Python-Markdown/markdown",
        "pr": 1272,
        "issue": 1131,
        "install": "-e . pytest pyyaml",
        "tests": ["tests"],
        "run": ["tests"],
    },
    {
        "id": "md-codespan-html",
        "repo": "Python-Markdown/markdown",
        "pr": 1072,
        "issue": 1066,
        "install": "-e . pytest pyyaml",
        "tests": ["tests"],
        "run": ["tests"],
    },
    {
        "id": "click-completion-close",
        "repo": "pallets/click",
        "pr": 2800,
        "issue": 2644,
        "install": "-e . pytest",
        "tests": ["tests"],
        "run": ["tests"],
    },
    {
        "id": "click-format-filename",
        "repo": "pallets/click",
        "pr": 2553,
        "issue": 2395,
        "install": "-e . pytest",
        "tests": ["tests"],
        "run": ["tests"],
    },
    {
        "id": "toml-array-remove",
        "repo": "sdispater/tomlkit",
        "pr": 409,
        "issue": 408,
        "install": "-e . pytest pyyaml",
        "tests": ["tests"],
        "run": ["tests"],
    },
    {
        "id": "toml-dotted-key",
        "repo": "sdispater/tomlkit",
        "pr": 162,
        "issue": 160,
        "install": "-e . pytest pyyaml",
        "tests": ["tests"],
        "run": ["tests"],
    },
    {
        "id": "werkzeug-rule-methods",
        "repo": "pallets/werkzeug",
        "pr": 3109,
        "issue": 3105,
        "install": "-e . pytest pytest-timeout ephemeral-port-reserve watchdog cryptography",
        "tests": ["tests"],
        "run": ["tests/test_routing.py"],
    },
    {
        "id": "jinja-namespace-tuple",
        "repo": "pallets/jinja",
        "pr": 1664,
        "issue": 1413,
        "install": "-e . pytest trio",
        "tests": ["tests"],
        "run": ["tests"],
    },
]

