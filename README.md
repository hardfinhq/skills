# Hardfin plugin for AI agents

This repository is Hardfin's plugin for Claude Code, claude.ai, Codex, ChatGPT, Cursor,
VS Code and GitHub Copilot. It teaches an agent to read and change records in a Hardfin
organization, such as assets, customers, items and locations, import them from spreadsheets,
and connect to the Hardfin MCP server.

## What it holds

The skills are authored here.

| Path | Holds |
| --- | --- |
| `skills/hardfin-cli/` | Read and change records with the Hardfin CLI, sign in and find commands |
| `skills/hardfin-import/` | Import assets, customers, items and locations from spreadsheets and CSV files |
| `skills/hardfin-setup/` | Set up a new Hardfin organization with a company's equipment, customers and sites |
| `skills/hardfin-upgrade/` | Update the Hardfin CLI and its skills |
| `plugin.json` | The plugin in the Agent Plugins format, with OpenAI's display settings |
| `assets/` | The listing icon `plugin.json` names |
| `.claude-plugin/` | The Claude Code plugin manifest and the marketplace also used by Codex |
| `.cursor-plugin/` | The marketplace Cursor uses to import this repository |
| `.mcp.json`, `mcp.json` | The Hardfin MCP server connection and release header for supported agents |
| `hardfin-skills.json` | The release name and version |
| `release/` | The CLI commands and flags this release was written against |
| `scripts/` | The release checker |
| `tests/` | Tests for the release checker and spreadsheet inspector |
| `.github/workflows/` | CI checks and release packaging |

## Install

| Tool | Install command | Update command |
| --- | --- | --- |
| Claude Code | `/plugin marketplace add hardfinhq/skills`, then `/plugin install hardfin@hardfin` | `claude plugin marketplace update hardfin`, then `claude plugin update hardfin@hardfin` |
| Codex | `codex plugin marketplace add hardfinhq/skills`, then `codex plugin add hardfin@hardfin` | `codex plugin marketplace upgrade hardfin` |
| Cursor | Customize, From GitHub Repository, enter `https://github.com/hardfinhq/skills` | Click Refresh |
| GitHub Copilot CLI | `copilot plugin install hardfinhq/skills` | `copilot plugin update hardfin` |
| VS Code | Command Palette: `Chat: Install Plugin From Source`, enter `https://github.com/hardfinhq/skills` | Repeat the install from source for the new release |
| Any agent that reads skills | `npx skills add hardfinhq/skills` | `npx skills update` |
| GitHub CLI 2.90 or later | `gh skill install hardfinhq/skills` | `gh skill update` |
| Manual copy | Copy `skills/*` into `.agents/skills/` for Codex and most agents, or `.claude/skills/` for Claude Code | Copy `skills/*` again from the new release |
| claude.ai, ChatGPT | Add `https://api.hardfin.com/mcp` as a custom connector | The connector uses the current server |

Third-party marketplaces do not update on their own, so run the update command after each release.

`npx skills add`, `gh skill install` and a manual copy install the skills without the MCP server.
The CLI's `hardfin init` command also writes the skills.

## Signing in

The MCP server signs you in through your browser the first time an agent calls it, with your
own Hardfin account. The CLI signs in with `hardfin login`, or takes an API key from
`HARDFIN_API_KEY`.

## What it sends

- The MCP server and the CLI send only the API calls the agent makes, to `api.hardfin.com`,
  with your credential
- The CLI reports its own defects to Hardfin, without your data or flag values. Set
  `DO_NOT_TRACK=1` to turn that off

## Releases

Each release is a tag `vX.Y.Z`. Its GitHub release carries three files:

| File | Holds |
| --- | --- |
| `hardfin-skills-X.Y.Z.tar.gz` | `hardfin-skills.json` and `skills/` at the archive root |
| `hardfin-skills-X.Y.Z.tar.gz.sha256` | The archive's SHA-256 checksum |
| `cli-surface-X.Y.Z.json` | The CLI commands and flags the release was written against, from `hardfin agent-guide --json` |

To make a release, bump every version field in one commit:

- `hardfin-skills.json`: `version`
- `plugin.json` and `.claude-plugin/plugin.json`: `version`
- `.claude-plugin/marketplace.json` and `.cursor-plugin/marketplace.json`: the `hardfin` entry's `version`
- `mcp.json` and `.mcp.json`: `X-Hardfin-Skills`

Merge the commit, then push the matching `vX.Y.Z` tag. The release workflow refuses a tag
that does not match. Claude Code keeps a cached plugin until its manifest version changes.

## Markers

The plugin's MCP configs send `X-Hardfin-Skills: <version>` to the Hardfin MCP server.
`hardfin-skills.json` at the plugin root names the release. These let the CLI and the server
tell which skills an agent has. Neither carries a credential.

## More

- The API reference for agents: https://developers.hardfin.com/llms.txt
- The API reference for people: https://docs.hardfin.com
- The CLI: https://www.npmjs.com/package/@hardfin/cli
