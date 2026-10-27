#!/usr/bin/env python3
"""Regression tests for ping rsync:// destination support."""

import subprocess
import sys

ping = sys.argv[1]

cases = [
    ("IPv4 rsync URL", "rsync://127.0.0.1/module/", 0),
    ("IPv6 rsync URL", "rsync://[::1]/module/", 0),
    ("Hostname URL", "rsync://localhost/module/", 0),
    ("Normal IPv4", "127.0.0.1", 0),
    ("Missing hostname", "rsync:///", 2),
    ("Explicit port", "rsync://example.org:873/module/", 2),
    ("Username", "rsync://user@localhost/module/", 2),
    ("Unclosed IPv6", "rsync://[::1/module/", 2),
]

failed = 0

for name, target, expected in cases:
    try:
        result = subprocess.run(
            [ping, "-n", "-c", "1", "-W", "1", target],
            capture_output=True,
            text=True,
            timeout=8,
        )
        passed = result.returncode == expected
    except subprocess.TimeoutExpired:
        passed = False

    print(f"{'PASS' if passed else 'FAIL'}: {name}", flush=True)

    if not passed:
        failed += 1
        if 'result' in locals():
            print(result.stdout)
            print(result.stderr)

print(f"\n{len(cases) - failed}/{len(cases)} tests passed")
sys.exit(1 if failed else 0)
