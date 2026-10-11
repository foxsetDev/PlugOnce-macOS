#!/usr/bin/env python3
"""Read one PlugOnce runtime session into a new JSONL artifact; never launch or cancel."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid


def read_page(binary, operation_id, cursor, socket, timeout):
    command = [binary, "--agent", "runtime.logs", "--operation-id", operation_id,
               "--offset", str(cursor), "--limit", "100", "--api-version", "2"]
    if socket:
        command += ["--socket", socket]
    result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
    response = json.loads(result.stdout)
    if result.returncode != 0 or response.get("ok") is not True:
        failure = response.get("error") or {}
        raise RuntimeError(f"{failure.get('code', 'CLI_ERROR')}: {failure.get('message', 'runtime.logs failed')}")
    if response.get("v") != 2:
        raise ValueError("Expected PlugOnce CLI response version 2")
    result = response["result"]
    page = result["runtimeLogs"]
    if page["operationId"] != operation_id or type(page["nextCursor"]) is not int or page["nextCursor"] < cursor:
        raise ValueError("Invalid operation/cursor in runtime.logs")
    if not isinstance(page["entries"], list) or type(page["active"]) is not bool or type(page["hasMore"]) is not bool:
        raise ValueError("Invalid runtime log page")
    previous = cursor - 1
    for entry in page["entries"]:
        if type(entry["cursor"]) is not int or entry["cursor"] <= previous or not isinstance(entry["text"], str):
            raise ValueError("Invalid runtime log entry")
        previous = entry["cursor"]
    if previous >= page["nextCursor"]:
        raise ValueError("Runtime log cursor did not advance past its entries")
    return page, result["runtimeRun"]


def watch(args):
    uuid.UUID(args.operation_id)
    # Keep the original spelling: bridge IDs are case-sensitive journal keys.
    operation_id = args.operation_id
    output = Path(args.output).absolute()
    if output.parent.resolve() != output.parent:
        raise ValueError("Output parent must be canonical and contain no symbolic links")
    descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as artifact:
        def write(value):
            artifact.write(json.dumps(value, ensure_ascii=False) + "\n")
            artifact.flush()

        write({"type": "session", "operationId": operation_id})
        deadline = time.monotonic() + args.timeout
        cursor = 0
        dropped_bytes = 0
        try:
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    write({"type": "watcher", "state": "deadline", "nextCursor": cursor})
                    return 2
                page, run = read_page(args.binary, operation_id, cursor, args.socket, min(16, remaining))
                gap = page.get("droppedEntriesBeforeCursor", 0)
                total_dropped = page.get("transportDroppedBytes", 0)
                if gap or total_dropped != dropped_bytes:
                    write({"type": "gap", "entries": gap, "transportDroppedBytes": total_dropped})
                    dropped_bytes = total_dropped
                for entry in page["entries"]:
                    write({"type": "output", **entry})
                cursor = page["nextCursor"]
                if not page["active"] and not page["hasMore"]:
                    write({"type": "result", "runtimeRun": run, "nextCursor": cursor})
                    return 0 if run["phase"] == "finished" else 1
                if not page["hasMore"]:
                    time.sleep(min(args.interval, max(0, deadline - time.monotonic())))
        except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.TimeoutExpired) as error:
            if isinstance(error, subprocess.TimeoutExpired) and time.monotonic() >= deadline:
                write({"type": "watcher", "state": "deadline", "nextCursor": cursor})
                return 2
            write({"type": "watcher", "state": "error", "message": str(error), "nextCursor": cursor})
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", default="/Applications/PlugOnce.app/Contents/MacOS/PlugOnce")
    parser.add_argument("--operation-id", required=True)
    parser.add_argument("--output", required=True, help="New JSONL file; its parent must already exist")
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--interval", type=float, default=1)
    parser.add_argument("--socket", help="Optional existing PlugOnce Unix socket")
    args = parser.parse_args()
    if not 0 < args.timeout <= 3600 or not 0 < args.interval <= 60:
        parser.error("Use a timeout from 0 to 3600 seconds and an interval from 0 to 60 seconds")
    try:
        return watch(args)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
