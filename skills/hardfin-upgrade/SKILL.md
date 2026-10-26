---
name: hardfin-upgrade
description: >
  Update the Hardfin CLI and its skills. Use when the CLI says it is outdated (`isOutdated:
  true`, an `update_available` or `api_version_outdated` event, or a `cli_outdated` error), the
  person asks to update the CLI or the skills, or `hardfin update` fails with
  `update_unavailable`.
---

# Update the Hardfin CLI and skills

Hardfin changes its API in ways an older CLI cannot follow, so update when told to:

- `hardfin update --check --json` answers `isOutdated: true`
- stderr carries a JSON line with `"event": "update_available"` or `"event": "api_version_outdated"`
- A command fails with the code `cli_outdated`

## 1. Update

If the person asks only to refresh the skills, go to step 2.
Otherwise, run `hardfin update --yes --json`.

It fails with `update_unavailable` when it cannot update this copy itself, and its message
ends with the command that does. Then:

- When the command starts with `npx -y`, nothing is installed. Rerun what failed with that
  command in place of `hardfin`, such as `npx -y @hardfin/cli@latest asset list`
- Otherwise, never run the command without asking the person first. Show them the command
  and wait for their answer
- When the message says the copy is a dependency of a project, tell the person the command
  rewrites that project's `package.json` and lockfile
- Never run the update, or the command it names, with `sudo`. If the command is refused for
  permissions, tell the person and stop

## 2. Refresh the skills and retry

After installing, `hardfin update` runs `hardfin init --skills-only` with the new version
when the working directory holds the skill `hardfin init` wrote. That brings the skill up
to date and leaves `AGENTS.md` and the MCP configs alone. Run `hardfin init --skills-only`
in any other project you set up, after an approved manual update, or when the person asks
to refresh the skills.

Read the `hardfin-cli` skill again afterwards. Retry what failed once.
