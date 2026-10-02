---
name: hardfin-cli
description: Read and change records in a Hardfin organization with the Hardfin CLI (`hardfin`) - assets, customers, items, locations, files, ownership and moves. Use when the person asks to look up, import, create, update, move, scrap or archive Hardfin data, to sign in to Hardfin, or to check what the CLI is connected to. Not for writing application code that calls the Hardfin API over HTTP; read https://docs.hardfin.com for that.
---

# Hardfin CLI

The `hardfin` command reads and changes the records in one Hardfin organization through the
Hardfin API. Every API operation is a command, named `hardfin <noun> <verb>`.

This skill gives the patterns. The installed CLI is the authority on exact commands and
flags, so check `--help` before relying on a flag this skill does not show.

## 1. Make sure the CLI is installed

```sh
hardfin --version || npm install -g @hardfin/cli
```

It needs Node 20 or later. If `npm install -g` is refused, run commands as
`npx -y @hardfin/cli <command>` instead.

## 2. Make sure it is signed in

```sh
hardfin status --offline --json
```

`credential.kind` is `none` when nobody is signed in. Then sign in one of three ways.

| Situation                                                  | Do this                                          |
| ---------------------------------------------------------- | ------------------------------------------------ |
| You run on the person's own machine                        | Run `hardfin login` in the foreground            |
| You run in a cloud sandbox, away from the person's browser | Run `hardfin login --device`                     |
| The person gave you an API key                             | Pass `--api-key <key>`, or set `HARDFIN_API_KEY` |

`hardfin login` writes one JSON line on stderr before it waits:

- `{"event": "sign_in_url", "url": …, "browserOpened": …}`: show the person `url`, and say
  whether a browser tab opened
- `{"event": "device_code", "userCode": …, "verificationUri": …}`: show the person the code
  and where to enter it

It then waits up to `waitSeconds` (300) for the person to approve. Give the command that
long to finish. Do not run it in the background and move on.

Never write an API key into a file in the repository, and never echo it back.

## 3. Find the command

```sh
hardfin --help                    # the nouns
hardfin asset --help              # what you can do with assets
hardfin asset create --help       # every flag that command takes
hardfin agent-guide               # every command, flag, exit code and error code, as Markdown
```

| Noun               | Holds                                                                              |
| ------------------ | ---------------------------------------------------------------------------------- |
| `asset`            | Physical assets, with their accounting, events, files, moves, ownership and status |
| `customer`         | The customers assets are sold or leased to                                         |
| `item`             | The catalogue of item types an asset is an instance of                             |
| `location`         | Warehouses, sites and their zones                                                  |
| `file`, `url-link` | Attachments, and links to records elsewhere                                        |
| `token`            | What the current credential is                                                     |
| `api`              | Any endpoint directly, when no command fits                                        |

## 4. Keys and IDs

A record has both, and they are not interchangeable.

|     | Looks like                                      | Used for                                                                             |
| --- | ----------------------------------------------- | ------------------------------------------------------------------------------------ |
| Key | `ast_4f9xk2mq7plr8stz`, `item_V1StGXR8Z5jdHi6B` | The positional argument of `get`, `update` and nested commands                       |
| ID  | `0192f7d4-3b6a-7c1e-9f2d-5a8b4c6e7d70`          | A field that points at another record, such as `--customer-id` or `--move assetId=…` |

A list or get answers with both. Take the one the next command asks for.

## 5. Read

```sh
hardfin asset list --limit 20 --search-query "RX-200"
hardfin asset get ast_4f9xk2mq7plr8stz
hardfin customer list --page 2 --limit 100
```

Output is JSON on stdout whenever stdout is not a terminal, so pipe it to `jq` or parse it.
A list holds at most 100 records a page. Fetch every page before saying how many there are.

## 6. Change

Before any change:

1. Read the record you are about to change, and work from what it says now
2. For more than a few records, or anything that deletes, scraps or archives, tell the person
   what will change and wait for them to agree
3. Make the change
4. Read the record back to confirm it

Set fields with one flag each, or send the whole body as JSON with `--input`:

```sh
hardfin customer create --name "Acme"
echo '{"name": "Dock 4, north side"}' | hardfin location create --input -
hardfin asset accounting update ast_4f9xk2mq7plr8stz --unset useful-life
```

A flag given with `--input` replaces that field of the body. A value with a comma in it
must go through `--input`, because a `key=value` flag cannot carry one.

## 7. When a command fails

The exit code says what kind of failure it was.

| Exit code | Means                             | Do this                                        |
| --------- | --------------------------------- | ---------------------------------------------- |
| 0         | It worked                         |                                                |
| 1         | The API or the network refused it | Read the error's `code`                        |
| 2         | The command was called wrongly    | Run the command with `--help` and fix the call |
| 4         | No usable credential              | Sign in, as in step 2                          |

The error is JSON on stderr. Branch on its `code`, never on the message.

| `code`                                              | Do this                                                          |
| --------------------------------------------------- | ---------------------------------------------------------------- |
| `not_signed_in`, `unauthorized`                     | Sign in again                                                    |
| `invalid_flag`, `missing_flag`, `invalid_arguments` | Read `--help` for that command                                   |
| `not_found`                                         | Check you passed a key, not an ID, where the command wants a key |
| `bad_request`, `invalid_request`, `conflict`        | Read `errors`, which names the field                             |
| `rate_limited`                                      | Wait a minute, then retry once                                   |
| `unreachable`, `server_error`                       | Tell the person, and include `requestId` if there is one         |

`hardfin agent-guide` lists every code.
