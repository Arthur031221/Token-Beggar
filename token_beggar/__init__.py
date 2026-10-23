"""Token Beggar: route each task to the cheapest model and effort that still does it right."""

import sys

if sys.version_info < (3, 10):  # noqa: UP036 a clear line instead of a TypeError from the first annotation
    raise SystemExit(f"token-beggar needs Python 3.10 or newer, found {sys.version.split()[0]}. Put a newer python3 first on PATH.")

__version__ = "0.3.0"
