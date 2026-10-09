# Elham Skills

Use [Elham](https://app.elham.ai) from an AI assistant: upload data, train models,
make predictions, monitor results, and manage your account using natural language.

## Install

Give your skill-capable assistant this repository URL and ask it to install the
**elham** skill:

```text
https://github.com/Elham-AI/elham-skills
```

Choose your assistant below. All three use the same skill and Python helper; you
only need one installation method per assistant.

| Assistant | Install | Start using it |
| --- | --- | --- |
| OpenAI Codex | Add this repository as a plugin marketplace, then install `elham` | Ask “Use Elham to list my datasets” |
| Claude Code | Add this repository as a plugin marketplace, then install `elham` | Type `/elham:elham` or ask to use Elham |
| Cursor | Customize → From GitHub Repository → paste this repository URL → install `elham` | Ask “Use Elham to list my datasets” |

**OpenAI Codex** — run in a terminal:

```sh
codex plugin marketplace add https://github.com/Elham-AI/elham-skills
codex plugin add elham@elham-skills
```

Start a new session after installation. For managed ChatGPT workspaces, an admin can
import this repository as a GitHub marketplace and make the plugin available to
members. Availability depends on workspace settings and script/network permissions.
See [OpenAI's plugin packaging guide](https://developers.openai.com/plugins/build/plugins)
and [workspace marketplace management](https://learn.chatgpt.com/docs/enterprise/plugin-management).

**Claude Code** — paste these commands into Claude Code:

```text
/plugin marketplace add https://github.com/Elham-AI/elham-skills
/plugin install elham@elham-skills
```

Or run `claude plugin marketplace add https://github.com/Elham-AI/elham-skills` and
`claude plugin install elham@elham-skills` in a terminal. Start a new session and use
`/elham:elham`. See [Claude's marketplace documentation](https://code.claude.com/docs/en/plugin-marketplaces).

**Cursor** — open **Customize**, choose **From GitHub Repository**, paste
`https://github.com/Elham-AI/elham-skills`, and install the **elham** plugin from the
imported marketplace. This repository includes Cursor's marketplace manifest;
import it as a plugin rather than a remote rule. See
[Cursor's skill installation instructions](https://cursor.com/docs/skills).

**Claude web / desktop skill upload** — download
[elham.zip](https://github.com/Elham-AI/elham-skills/raw/refs/heads/main/downloads/elham.zip),
then open **Customize → Skills → + → Create skill → Upload a skill** and enable it.
This is the skill-only ZIP, not GitHub's whole-repository ZIP. Code execution must be
enabled. See [Claude's custom skill instructions](https://support.claude.com/en/articles/12512180-use-skills-in-claude).
The upload makes the workflow available; live account operations also need outbound
HTTPS and a securely supplied `ELHAM_ACCESS_TOKEN` in the execution environment.
If that environment cannot accept a secret securely, use Claude Code with terminal
sign-in. Never upload a token or password inside the skill ZIP or paste it into chat.

**Alternative for all three** — use the [Skills CLI](https://skills.sh/docs) and select
your installed assistant(s):

```sh
npx skills add Elham-AI/elham-skills --skill elham
```

**Manual installation** — copy the entire `skills/elham` folder, including its scripts
and references, into one of these user-level locations:

| Assistant | Destination |
| --- | --- |
| OpenAI Codex | `~/.agents/skills/elham/` |
| Claude Code | `~/.claude/skills/elham/` |
| Cursor | `~/.cursor/skills/elham/` |

`~` means your user home directory. Start a new assistant session afterward. A copied
`SKILL.md` alone is insufficient because execution needs the bundled helper.

Installation support varies by assistant. This skill needs Python 3.10+ and permission
to run scripts and reach Elham over HTTPS. It uses only Python's standard library.
It does not require configuring an MCP connector, installing an MCP server, or
installing the Elham backend. A chat-only assistant without script execution cannot
run this skill.

After installation, ask: **“Use Elham to help me sign in and list my datasets.”**
The assistant will guide you to a hidden-password sign-in prompt in your terminal.
An Elham account is required. Never paste your password in chat. The helper saves a
short-lived access token in your private `~/.elham-skills/session.json`, not your
password. Sign in again when it expires. For hosted/noninteractive assistants, supply
`ELHAM_ACCESS_TOKEN` using the host's secret settings. SSO-only accounts need that
securely supplied token; browser SSO is not implemented in this helper.

## What you can ask

- “Upload this CSV and explain its data quality issues.”
- “Estimate the cost to train a model that predicts churn.”
- “Train that model within my approved credit budget and show progress.”
- “Predict these rows with my running model.”
- “Show my model's monitoring summary.”
- “Preview a SELECT query from my database before importing it.”
- “Check my credits and list my team's models.”

The bundle covers datasets and column metadata, training and model lifecycle,
predictions, monitoring and labels, credits, teams, API keys, databases, and external
data sources. It calls the same hosted tools as the Elham MCP integration through a
bundled HTTP client. The MCP service still needs to be available; the skill removes
client configuration, not the hosted service dependency. Live tool discovery preserves
the server's current capabilities and permissions without copying backend logic.

Prediction API keys (`ELHAM_API_KEY`) authorize only predictions and their input
schema. Account management and cost estimation need a full signed-in session. The
skill estimates costs before asking to spend credits; installing it does not grant
permission to delete data, change teams, send invitations, or spend money.

## Helper commands

Paths below are relative to the repository; after installation the assistant resolves
them relative to the installed skill folder.

```sh
python skills/elham/scripts/elham.py login
python skills/elham/scripts/elham.py status
python skills/elham/scripts/elham.py tools
python skills/elham/scripts/elham.py describe train_model
python skills/elham/scripts/elham.py call list_datasets
python skills/elham/scripts/elham.py call get_model --args-file arguments.json
python skills/elham/scripts/elham.py logout
```

`arguments.json` contains a JSON object such as `{"model_id":"YOUR_MODEL_ID"}`.
Use `--args-file -` for stdin. Secret fields and URLs are redacted from normal output;
`--private-output NEW_FILE` saves the raw result to a user-only file for uploads or
credential handoff. Remove temporary files after use. On Windows the helper uses
`icacls`; on Unix it uses file permissions. Storage protection failures stop the
operation. Treat local files as sensitive even with these access restrictions.

HTTP success alone is insufficient: tool errors also produce a nonzero exit code.
The helper never automatically retries calls, because a lost response can represent
a completed operation or credit charge. `logout` removes only the locally saved
token; it does not revoke server sessions or unset environment credentials.

## Development

```sh
python -m unittest discover -s tests -v
python scripts/package_skill.py
```

The ZIP builder includes only the reviewed skill files. Rebuild the archive after
changing any skill resource; tests reject an archive whose contents differ from the
source. Native manifests for all three assistants reference the same `skills/` tree.

Tests use a simulated HTTP transport and require no credentials or credit spending.
To check availability against production without signing in, run `tools` and
`describe`. Do not run paid or mutating tools as an installation test.

See [the skill](skills/elham/SKILL.md) for the workflows and safety boundaries.
