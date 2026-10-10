# Marketplace submission guide

Publisher: **Elham AI**. Publisher contact: **faris@elham.ai**.
Website: https://elham.ai. Code license: MIT. Brand use: see [BRANDING.md](BRANDING.md).

The repository contains the provider manifests and shared skill. Local installation
or validator success does not mean a provider has approved or listed the plugin.
No public-directory submission or approval is claimed by this document.

## Packages and listing copy

Run `python scripts/package_skill.py` and `python scripts/validate_submission.py`.

| Destination | What to supply |
| --- | --- |
| OpenAI public plugin submission | `downloads/elham-plugin.zip`: complete plugin with manifests, logo, license, documentation and skill |
| Claude public plugin directory | Public repository `https://github.com/Elham-AI/elham-skills`, plugin path `.` |
| Cursor marketplace | Public repository `https://github.com/Elham-AI/elham-skills`, plugin `elham` |
| Claude personal skill upload | `downloads/elham.zip`: skill-only archive; not the full plugin submission |

ZIPs are generated build/release assets rather than files in the plugin's source
folder. This avoids packaging archives inside an installed plugin.

Use the following listing text; do not add unverified claims about accuracy,
compliance, approvals, or hosted sign-in:

- Name: **Elham AutoML**
- Subtitle: **Train models from your data**
- Description: Work with tabular datasets and machine-learning models in Elham.
  Inspect data quality, estimate training costs, train models, make predictions,
  monitor results, and manage authorized account workflows from your assistant.
  Requires an Elham account, Python execution, and HTTPS access. Paid operations use
  Elham credits. Sign-in uses a private terminal prompt or an explicitly supplied
  private credential file; browser OAuth is not included.
- Category: **Productivity** for OpenAI; select the closest data/AI category offered
  in other portals.
- Website: https://elham.ai
- Support: https://elham.ai/contact
- Privacy: https://elham.ai/Elham-Privacy-Policy.html
- Terms: https://elham.ai/Elham-terms-and-condition.html

The bundled square logo is the existing Elham website logo. The complete package
includes it, and provider manifests point to it.

## OpenAI

1. Sign in at https://platform.openai.com/plugins using the organization that should
   own the listing. Select the correct project and verify the Elham publisher identity.
   An owner or a member with Apps Management Write must submit.
2. Upload the complete plugin ZIP and inspect all metadata and skill findings.
3. Select the actual supported execution surfaces. This package has no registered
   MCP connector; its Python client calls the hosted MCP endpoint. Disclose that
   dependency and authentication behavior. If review requires a registered remote
   connector instead, implement the required OAuth integration before submitting
   that variant; never label the protected service as anonymous.
4. Resolve blocking findings and provide truthful attestations. Submit for review;
   publish only after approval. A skills-only package may have additional eligibility
   requirements. Account verification and provider review happen outside this repo.

Reference: [OpenAI submission](https://developers.openai.com/plugins/deploy/submission).

## Claude

1. Sign in at https://claude.ai/directory/manage. A paid account and the appropriate
   organization role are needed; the portal shows whether the account is eligible.
2. Choose Submit new → Plugin bundle, enter the public repository and root path,
   then run Validate against the intended commit.
3. Address every blocking finding; explain any review holds. The helper reads only
   credentials explicitly provisioned for Elham and discloses all destinations.
   If the portal requires `userConfig` integration for a specific execution surface,
   implement and test its supported injection path before claiming that surface.
4. Complete listing and review fields and submit. This directory is distinct from
   Anthropic's curated `claude-plugins-official` marketplace.

Reference: [Claude submission checks](https://claude.com/docs/plugins/pre-submission-checklist).

## Cursor

1. Sign in at https://cursor.com/marketplace/publish.
2. Complete publisher access if requested and submit the public repository link.
3. Provide the publisher contact, description, and existing logo; review the actual
   publisher terms and attestations in the portal before accepting them.
4. Track the review; importable repository packaging does not imply marketplace approval.

Reference: [Cursor plugin reference](https://cursor.com/docs/reference/plugins).

## Reviewer verification

Local checks cover transport, credential scope, redaction, file permissions, ZIP
contents, metadata bounds, and plugin installation. They do not prove authenticated
end-to-end behavior on every host. Before submitting claims about account operations,
use a dedicated sample account supplied privately through the portal:

1. Sign in and list the sample datasets; verify names/IDs and permissions.
2. Inspect dataset quality and column metadata.
3. Estimate training cost without submitting training or spending credits.
4. With an explicitly authorized test budget, train a sample model and inspect its
   returned ID and progress; do not mark a submitted job complete prematurely.
5. With spending authorization, inspect a Running model's input schema and predict
   sample rows; verify the result and actual charge.
6. Verify an API key cannot list/delete datasets and that a cross-account resource
   is inaccessible. Do not use another customer's data for this check.
7. Verify malformed arguments, ambiguous IDs, and insufficient permissions produce
   visible errors or clarification rather than hidden retries or fabricated success.

Keep reviewer credentials out of this repository and its release assets. Record
actual results, skips, and provider feedback; never describe these scenarios as
already executed merely because they are documented here.
