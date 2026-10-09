# Account, credits, and teams

`get_credit_balance` returns the effective balance, which can belong to the team
owner. Use `get_credit_history` with pagination for transaction history. Never imply
that each team member has an independent budget. Skills do not purchase credits or
change payment state; direct the user to Elham for purchases.

Use `get_team` before changing a team. Discover live schemas for `create_team`,
`rename_team`, `delete_team`, `invite_member`, `accept_invite`, `decline_invite`,
`remove_member`, `update_member_role`, and `leave_team`. Invitations send messages;
membership and role changes affect access. Resolve the exact team/person and obtain
authorization appropriate to the requested action. Server permissions remain final.

`create_api_key`, `list_api_keys`, and `delete_api_key` manage prediction credentials.
Create/revoke only when requested. Results may contain secret API-key values: the
helper redacts them by default. If the user needs a newly created key, use
`--private-output` and direct the user to that protected local file or their secret
manager without showing the key in chat. Do not create a replacement simply because
the first result was redacted. Delete temporary secret files once securely transferred.
