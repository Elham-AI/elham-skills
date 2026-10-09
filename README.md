# Elham Skills

Use [Elham](https://app.elham.ai) from an AI assistant: upload data, train models,
make predictions, monitor results, and manage your account using natural language.

## Install

Give your skill-capable assistant this repository URL and ask it to install the
**elham** skill:

```text
https://github.com/Elham-AI/elham-skills
```

For assistants supported by the [Skills CLI](https://skills.sh/docs):

```sh
npx skills add Elham-AI/elham-skills --skill elham
```

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
```

Tests use a simulated HTTP transport and require no credentials or credit spending.
To check availability against production without signing in, run `tools` and
`describe`. Do not run paid or mutating tools as an installation test.

See [the skill](skills/elham/SKILL.md) for the workflows and safety boundaries.
