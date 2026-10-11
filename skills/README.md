# PlugOnce agent skills

`plugonce-develop/` is a portable [Agent Skills](https://agentskills.io/specification) folder for an existing terminal-capable agent. It contains instructions, the runtime reference and a Python standard-library log watcher. No vendor SDK or extra agent process is needed. The installed PlugOnce application enforces permissions independently of the skill.

The public package lives at `foxsetDev/PlugOnce-macOS` → `skills/plugonce-develop`. It includes the skill and its self-contained helpers; the PlugOnce application is distributed separately.

The [license](../LICENSE) permits installing and running the skill unmodified with PlugOnce. Modifications and redistribution require written permission. Report bugs or suggest features in [GitHub Issues](https://github.com/foxsetDev/PlugOnce-macOS/issues); pull requests are not accepted.

## Install in Pi from GitHub

```fish
pi install git:github.com/foxsetDev/PlugOnce-macOS
```

Start Pi or run `/reload`, then invoke `/skill:plugonce-develop`. Add `--local` to the install command for project-only setup. The root `package.json` explicitly exposes this skill; it declares no extensions or dependencies.

For a reviewed revision, use `git:github.com/foxsetDev/PlugOnce-macOS@COMMIT_SHA` with the actual commit SHA. [Developer setup](../DEVELOPMENT.md) lists the required application capabilities.

## Install from a checked-out repository

Review the skill and helper, then copy the whole `plugonce-develop` folder into your agent's skills directory. Examples use fish and assume the target does not already exist:

```fish
# Pi and other agents supporting the shared Agent Skills location:
mkdir -p ~/.agents/skills
cp -R skills/plugonce-develop ~/.agents/skills/plugonce-develop

# Or scope it to the current port project:
mkdir -p .agents/skills
cp -R /absolute/PlugOnce-macOS/skills/plugonce-develop .agents/skills/plugonce-develop

# Claude Code can use its own directory:
mkdir -p ~/.claude/skills
cp -R skills/plugonce-develop ~/.claude/skills/plugonce-develop
```

Use the destination supported by your agent; do not run all three copies. Existing installations should be reviewed and updated deliberately. Restart/reload skill discovery as required by the agent. In Pi, invoke `/skill:plugonce-develop` or describe a Switch port iteration using PlugOnce. For an agent without skill discovery, give it the absolute path to `plugonce-develop/SKILL.md` and ask it to read that file.

The repository/path pair is `foxsetDev/PlugOnce-macOS` + `skills/plugonce-develop`. An installer accepting GitHub skill paths can use `https://github.com/foxsetDev/PlugOnce-macOS/tree/main/skills/plugonce-develop`; a branch or commit SHA can pin a tested revision.

The application must report `runtime.launch` and `runtime.logs` in `--agent capabilities`; an older released application cannot acquire those capabilities by installing a skill. The bundled [runtime reference](plugonce-develop/references/runtime.md) describes setup, capture and device-side limits.

Primary compatibility reference: [Pi skill discovery](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/skills.md), [Claude Code skills](https://code.claude.com/docs/en/skills).
