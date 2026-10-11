**English** · [Русский](DEVELOPMENT.ru.md)

# Developer mode

Keep PlugOnce beside your editor as a compact SD window. Your existing agent builds the port; PlugOnce handles scoped file operations, NRO delivery and the runtime log session.

> **Preview.** The skill is public. Runtime features require a developer-capable PlugOnce build and enabled Agent Access. Check the application before relying on commands in this guide; the current public download may not include them. Installing the skill does not update the app. Physical Switch validation of this implementation is still pending.

## Install in Pi

Review the [skill](skills/plugonce-develop/SKILL.md) and its [log watcher](skills/plugonce-develop/scripts/runtime-watch.py), then install from GitHub:

```fish
pi install git:github.com/foxsetDev/PlugOnce-macOS
```

Start Pi, or run `/reload` in an open session. Invoke the skill with a concrete task:

```text
/skill:plugonce-develop Build this Switch port, inspect the SD destination,
deploy the changed files and collect runtime logs after I prepare netloader.
Preserve existing configs and report the build revision and observed errors.
```

For a project-only installation, add `--local` to the install command. To pin a reviewed revision, append `@COMMIT_SHA` with its actual SHA. See [Pi package installation](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/packages.md).

The skill also works with agents that support the [Agent Skills format](https://agentskills.io/specification). [Manual setup](skills/README.md) covers shared skill folders and Claude Code. For an agent without discovery, provide the path to `skills/plugonce-develop/SKILL.md`.

## Prepare PlugOnce and the console

1. Install PlugOnce on macOS and keep it open. Check its native executable:

   ```fish
   set p /Applications/PlugOnce.app/Contents/MacOS/PlugOnce
   $p --agent capabilities
   ```

   Required developer methods: `app.presentation`, `files.download`, `files.mkdir`, `runtime.status`, `runtime.launch` and `runtime.logs`. The skill reads the app's bundled guide and command help.
2. In **Settings → Agent Access**, enable the bridge and the needed actions. Allow the port's Mac project/output folder and its SD folder. Enable the separate permissions for the operations you want the agent to perform unattended. Runtime launch is off by default and follows the app's licensing checks.
3. Select the installed devkitPro `nxlink` executable and enter the Switch's private IPv4 address. These settings are chosen in PlugOnce, not supplied by an agent command.
4. For SD files, open **DBI → Run MTP responder** and connect over USB. For runtime launch, finish transfers, leave DBI, open hbmenu and activate [netloader with Y](https://switchbrew.org/wiki/Homebrew_Menu#Netloader). Use a trusted local network.
5. For live output, the port must redirect stdout/stderr through [libnx `nxlinkStdio()`](https://switchbrew.github.io/libnx/nxlink_8h.html). A port that only writes SD logs needs a separate file download after returning to DBI.

Folder permissions constrain source and deployment paths. They do not sandbox the running port's own access to the SD card. Run builds trusted for the task.

## Keep a small workspace

Switch between the regular window and **Compact Mode**, pin the compact window above other apps, and expand the agent panel when you need progress or logs. The SD panel supports folder navigation and the existing transfer engine.

An agent can request the same layout without stealing focus:

```fish
$p --agent app.presentation --mode compact --pinned true --agent-expanded true --activate false --api-version 2
```

## A development iteration

| Stage | Agent action | Evidence |
| --- | --- | --- |
| Build | Use the port's documented toolchain and command | Revision, build output, exit code, NRO path |
| Inspect | Read the SD folder and download existing configs | Current paths and a local rollback copy |
| Deploy | Plan and commit only changed artifacts or data | UUID, conflicts, transfer verification |
| Prepare launch | Wait for the user to leave DBI and enable netloader | Configured target; loader readiness remains unverified |
| Run | `runtime.launch` sends a captured NRO under a new name | Operation ID, artifact hash, transport state |
| Diagnose | Page `runtime.logs` and export JSONL | Port output, buffer gaps and session outcome |
| Recover | Query `operation.get` using the original UUID | No blind duplicate write or launch |

The [runtime reference](skills/plugonce-develop/references/runtime.md) contains exact launch/log commands, the logging integration and the watcher invocation.

Useful workflows include editing configs while preserving originals, deploying new build files without recopying game assets, retrieving file/crash logs through DBI, preparing rollback copies and comparing two builds with explicit test criteria.

## What the result tells you

`nxlink` exit codes describe the Mac transport. A completed transfer or log session does not prove a working menu, rendering or gameplay. `operation.cancel` and a timeout stop host collection; the NRO may keep running on Switch. Return to hbmenu before another launch.

Logs are bounded and retained for the latest eight runs in the current app session. Export them before closing PlugOnce. The JSONL watcher records buffer gaps and deadlines; its own deadline does not cancel the port or launch another one.

Automatic return to the loader, input replay, screenshots during execution and runtime metrics need support in the port or a separate console component. The next useful port integration is a build/run ID, `ready` + heartbeat, a small smoke test and a clean exit command.

Port output and downloaded files are diagnostic data. The skill keeps task scope and permissions intact and reports a missing capability or permission explicitly.
