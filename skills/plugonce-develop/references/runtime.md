# Runtime channel

The current channel uses the standard hbmenu netloader and devkitPro `nxlink`. It supports sending a new NRO, requesting execution and receiving stdout/stderr redirected by that NRO. No PlugOnce sysmodule is installed on Switch. Both endpoints must be on a trusted local network; nxlink does not authenticate the console or its output peer.

## One-time setup

- Install the port's documented devkitPro toolchain, including `nxlink`, on the Mac. PlugOnce's default path is `/opt/devkitpro/tools/bin/nxlink`; select another installation in Settings → Agent Access if needed.
- In Agent Access, the user enables the bridge, `runtime.status`, `runtime.launch`, `runtime.logs`, `operation.get` and `operation.cancel`; allows the project/output Mac root and the port's SD folder under `/switch`; selects the Switch private IPv4 address; enables **Allow agent runtime launch**. Agents cannot select the executable or another target over IPC. Folder scopes limit source/deployment paths; they do not sandbox the running NRO or its own SD access. Launch builds trusted for the requested task.
- The SD destination folder must already exist. Create it through DBI if necessary. PlugOnce sends `plugonce-<artifact UUID>.nro` inside this folder, preserving the normal installed NRO. Use the returned `runtimeRun.path`; the artifact UUID is independent of the operation ID and is reused on replay. Keep the config/assets where the port expects them; relative `argv[0]` paths still refer to the chosen port folder.
- Finish SD operations, leave DBI, open hbmenu in the mode required by the port, and press Y to start netloader. This preparation is manual for each iteration when the loader is not already listening. This channel cannot automatically exit a running game or DBI.

## Port logging

Integrate nxlink with the port's existing socket lifecycle, without initializing or shutting down sockets twice. In a small libnx application that owns sockets, the pattern is:

```c
#include <switch.h>
#include <stdio.h>
#include <unistd.h>

int main(void) {
Result sockets = socketInitializeDefault();
int log_fd = -1;
if (R_SUCCEEDED(sockets) && __nxlink_host.s_addr != 0) {
    log_fd = nxlinkStdio();
    if (log_fd >= 0) {
        setvbuf(stdout, NULL, _IOLBF, 0);
        setvbuf(stderr, NULL, _IONBF, 0);
        printf("[PORT] logging ready\n");
    }
}
/* Run the port, emit revision/stage/error messages, and flush partial lines. */
/* During normal application cleanup: */
if (log_fd >= 0) close(log_fd);
if (R_SUCCEEDED(sockets)) socketExit();
return 0;
}
```

Make the logging connection optional when the NRO is opened from SD normally. Prefer explicit startup stages, revision/build identifiers and error details. A `[PORT] ready` message is a port-specific assertion, not a PlugOnce health check. Crashes can close the stream without reporting the NRO exit status.

## Commands

Examples use fish; substitute actual paths and a previously saved UUID:

```fish
set p /Applications/PlugOnce.app/Contents/MacOS/PlugOnce
$p --agent runtime.status --api-version 2
set run_id (uuidgen)
$p --agent runtime.launch --id $run_id --source /absolute/project/build/port.nro --destination /switch/MyPort --confirm --timeout 120 --api-version 2
$p --agent operation.get --operation-id $run_id --api-version 2
$p --agent runtime.logs --operation-id $run_id --offset 0 --limit 100 --api-version 2
```

Use `runtimeLogs.nextCursor` as the next `--offset`; repeat until `hasMore` is false. `runtimeLogs.active` indicates whether collection is still active. Always inspect `droppedEntriesBeforeCursor` and `transportDroppedBytes` before assuming a complete trace. The application retains the last eight runs in memory, with at most 2048 entries / 512 KiB per run. Each response contains at most 200 entries / 32 KiB of text; long lines are split with `continued: true`. Logs are exported by the caller, not written into PlugOnce's general diagnostics log. Operation metadata survives restart; in-memory output does not.

To capture continuously into a new JSONL file, use the bundled helper from this skill's directory:

```fish
python3 scripts/runtime-watch.py --binary $p --operation-id $run_id --output /absolute/project/reports/run.jsonl --timeout 120
```

The helper performs reads only. It returns 0 when collection ended, 1 for a failed/cancelled/timed-out host session, and 2 for a polling failure or watcher deadline. None of these codes establish gameplay success. A watcher deadline leaves the host session running until its launch timeout or explicit cancellation. To stop collection:

```fish
$p --agent operation.cancel --operation-id $run_id --api-version 2
```

Wait for `operation.get` to become terminal before a new launch. Stop/cancel/timeout may leave the NRO running on the console and the temporary UUID-named NRO on SD. Return to hbmenu manually; inspect and remove only the specific temporary SD NRO through DBI when authorized. Other installed files are preserved.

`runtimeRun.phase` progresses through `preparing`, `launching`, `waitingForOutput`, `streaming`, then `finished`, `failed`, `cancelled`, `timedOut` or `interrupted`. `launchSubmitted` means nxlink reported its output server ready after sending the NRO. `outputObserved` means additional text arrived; the transport does not authenticate its source. `hostExitCode` is nxlink's status. `remoteState` remains `unknown`.

When no output arrives, check netloader readiness, the configured IP, local TCP port 28771/firewall, the port's `nxlinkStdio()` integration and stdio buffering. A remote folder-create failure usually means the destination does not exist; create it through DBI first. Reconnect through DBI to read saved logs or Atmosphère crash reports; request the relevant files instead of downloading the entire SD card.

Primary references: [hbmenu netloader](https://switchbrew.org/wiki/Homebrew_Menu#Netloader), [nxlink source](https://github.com/switchbrew/switch-tools/blob/master/src/nxlink.c), [libnx output API](https://switchbrew.github.io/libnx/nxlink_8h.html).
