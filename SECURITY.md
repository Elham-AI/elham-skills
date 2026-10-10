# Security, privacy, and service access

For security reports or publisher support, contact **faris@elham.ai**. Do not put
credentials or customer datasets in a public issue. General product support is
available at [Elham Contact](https://elham.ai/contact).

## What runs

An assistant runs the readable Python helper bundled with the skill. It needs
Python 3.10+ and uses only the standard library. No dependency installation,
background process, shell hook, browser extension, or MCP connector is installed.
On Windows it runs `whoami` and `icacls` to restrict newly written secret files.

## Network destinations and data

- HTTPS requests to `https://app.elham.ai/api/elham-mcp/mcp` carry tool names,
  arguments, and the user's Elham authentication credential. Dataset/model IDs,
  prediction rows, labels, team invitations, SQL, and external-source configuration
  are sent only as needed for requested operations. Elham enforces account scope.
- Dataset uploads send the selected file to the HTTPS storage URL returned by
  Elham. That URL can belong to Elham's storage infrastructure or cloud storage
  provider. The upload uses a separate HTTP client without Elham auth headers.
  Signed URLs are sensitive and must not be shared.
- Source tests/imports can cause Elham's backend to contact the external data
  provider the user configured. The assistant should explain that data transfer
  before an authorized import. Do not provide credentials for unrelated systems.

The helper does not add analytics or send data to a third-party telemetry service.
The assistant platform may process prompts, tool output, and uploaded files under
its own policies. Hosted Elham processing is governed by Elham's
[privacy policy](https://elham.ai/Elham-Privacy-Policy.html) and
[terms](https://elham.ai/Elham-terms-and-condition.html). This document describes
the integration's behavior; it does not replace those policies or promise a
particular retention period.

## Credentials and permissions

Interactive sign-in sends the email and hidden password to Elham, then saves only
the returned short-lived access token in a user-only session file. The helper never
reads ambient environment credentials. Noninteractive use requires a private file
explicitly selected with `--credential-file`. Its endpoint must match Elham exactly;
it may contain one access token or one prediction API key, never both.

Use the execution host's secure provisioning mechanism for that file. Never paste
passwords or tokens into chat, skill files, command arguments, issue reports, ZIPs,
or Git. Windows host-provisioned files must have a user-only ACL; on Unix the helper
rejects credentials with group/other permissions. `logout` removes the helper's
saved session, but does not delete a supplied file or revoke remote sessions.

API keys cannot manage the account or estimate costs. The server checks ownership
and team permissions. The helper refuses redirect forwarding, verifies TLS, redacts
common secret fields, and never automatically retries a failed operation.

## Spending and changes

Training and prediction can spend credits. The skill calls the estimator and
requires spending authorization. Estimates may differ from actual charges. Deleting
resources, sending invitations, and changing team roles require user authorization.
A timed-out request may have completed; inspect state before another submission.

## Supported environments

Local Python execution supports terminal sign-in. Hosted assistants must permit
outbound HTTPS and offer secure credential-file provisioning; installing a skill
alone supplies neither. Browser OAuth and automatic token refresh are not currently
implemented. Test authenticated workflows in the target environment before listing
that environment as fully supported. Never work around a host security restriction.
