# Hardfin plugin for AI agents

This repository is Hardfin's plugin for Claude and for OpenAI's Codex and ChatGPT. It teaches
an agent to read and change the records in a Hardfin organization, such as assets, customers,
items and locations, and connects it to the Hardfin MCP server.

## What it holds

| Path | Holds |
| --- | --- |
| `skills/hardfin-cli/` | The `hardfin-cli` skill: installing and signing in to the Hardfin CLI, finding a command, and changing records safely |
| `.mcp.json`, `mcp.json` | The Hardfin MCP server at `https://api.hardfin.com/mcp`, for Claude and for OpenAI |
| `.claude-plugin/` | The plugin manifest and the marketplace that Claude Code and Codex install from |
| `plugin.json` | The same plugin in the Agent Plugins format, with OpenAI's display settings |

The skill is copied from the Hardfin CLI's npm package, `@hardfin/cli`, so it always matches a
released CLI. A daily workflow opens a pull request here when a release changes it.

## Install

| Tool | Command |
| --- | --- |
| Claude Code | `/plugin marketplace add hardfinhq/skills`, then `/plugin install hardfin@hardfin` |
| Codex | `codex plugin marketplace add hardfinhq/skills` |
| Any agent that reads skills | `npx skills add hardfinhq/skills` |
| claude.ai, ChatGPT | Add `https://api.hardfin.com/mcp` as a custom connector |

While this repository is private, each install needs GitHub access to `hardfinhq`.

## Signing in

The MCP server signs you in through your browser the first time an agent calls it, with your
own Hardfin account. The CLI signs in with `hardfin login`, or takes an API key from
`HARDFIN_API_KEY`.

## What it sends

- The MCP server and the CLI send only the API calls the agent makes, to `api.hardfin.com`,
  with your credential
- The CLI reports its own defects to Hardfin, without your data or flag values. Set
  `DO_NOT_TRACK=1` to turn that off

## More

- The API reference for agents: https://developers.hardfin.com/llms.txt
- The API reference for people: https://docs.hardfin.com
- The CLI: https://www.npmjs.com/package/@hardfin/cli
