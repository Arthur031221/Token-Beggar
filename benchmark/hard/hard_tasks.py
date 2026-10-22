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
        "id": "click-format-filename",
        "repo": "pallets/click",
        "pr": 2553,
        "issue": 2395,
        "install": "-e . pytest",
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
    {
        "id": "structlog-exception-outside",
        "repo": "hynek/structlog",
        "pr": 680,
        "issue": 634,
        "install": "-e .[dev] pytest",
        "tests": ["tests"],
        "run": ["tests"],
    },
    {
        "id": "rich-inspect-methods",
        "repo": "Textualize/rich",
        "pr": 2294,
        "issue": 2284,
        "install": "-e . pytest attrs",
        "tests": ["tests"],
        "run": ["tests"],
    },
    {
        "id": "packaging-extras-marker",
        "repo": "pypa/packaging",
        "pr": 888,
        "issue": 885,
        "install": "-e . pytest pretend",
        "tests": ["tests"],
        "run": ["tests"],
    },
]

