#!/usr/bin/env python3
"""Regression tests for rsync:// destinations in ping."""

import subprocess
import sys

ping = sys.argv[1]

# name, destination, expected IP, expected error
cases = [
    ("IPv4 URL", "rsync://127.0.0.1/module/", "127.0.0.1", None),
    ("IPv4 with port", "rsync://127.0.0.1:873/module/", "127.0.0.1", None),
    ("Custom port", "rsync://127.0.0.1:8873/module/", "127.0.0.1", None),
    ("IPv6 URL", "rsync://[::1]/module/", "::1", None),
    ("IPv6 with port", "rsync://[::1]:873/module/", "::1", None),
    ("Hostname with port", "rsync://localhost:873/module/", "127.0.0.1", None),
    ("Plain IPv4", "127.0.0.1", "127.0.0.1", None),
    ("Empty host", "rsync:///", None, "missing host"),
    ("Empty port", "rsync://127.0.0.1:/", None, "invalid rsync port"),
    ("Alphabetic port", "rsync://127.0.0.1:abc/", None, "invalid rsync port"),
    ("Port overflow", "rsync://127.0.0.1:65536/", None, "invalid rsync port"),
    ("Zero port", "rsync://127.0.0.1:0/", None, "invalid rsync port"),
    ("Username", "rsync://user@localhost/module/", None, "invalid rsync URL"),
    ("Unclosed IPv6", "rsync://[::1/module/", None, "invalid rsync URL"),
]

failed = 0
skipped = 0

for name, target, expected_ip, expected_error in cases:
    if expected_ip == "::1":
        probe = subprocess.run(
            [ping, "-n", "-c", "1", "-W", "1", "::1"],
            capture_output=True, text=True, timeout=8
        )
        if probe.returncode != 0:
            print(f"SKIP: {name} (IPv6 loopback unavailable)")
            skipped += 1
            continue

    args = [ping, "-n", "-c", "1", "-W", "1"]

    if name == "Hostname with port":
        args += ["-4"]

    args.append(target)

    try:
        result = subprocess.run(
            args, capture_output=True, text=True, timeout=8
        )
    except subprocess.TimeoutExpired:
        print(f"FAIL: {name} (timeout)")
        failed += 1
        continue

    output = result.stdout + result.stderr

    if expected_ip is not None:
        expected_header = f"PING {expected_ip} ({expected_ip})"
        if expected_ip == "::1":
            expected_header = "PING ::1 (::1)"
        elif name == "Hostname with port":
            expected_header = "PING localhost (127.0.0.1)"

        passed = (
            result.returncode == 0
            and expected_header in result.stdout
        )
    else:
        passed = (
            result.returncode == 2
            and expected_error in result.stderr
        )

    print(f"{'PASS' if passed else 'FAIL'}: {name}")

    if not passed:
        failed += 1
        print(f"  Expected IP: {expected_ip}")
        print(f"  Expected error: {expected_error}")
        print(f"  Exit code: {result.returncode}")
        print(output)

print(f"\n{len(cases) - failed - skipped}/{len(cases)} passed, "
      f"{skipped} skipped, {failed} failed")

sys.exit(1 if failed else 0)
