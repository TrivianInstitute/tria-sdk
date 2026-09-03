# Purpose-bound governance

TRIA distinguishes authorization scope from authorization purpose.

A consent or permission record may optionally bind its authority to an explicit purpose. When a record has a purpose, it may satisfy only a governance requirement declaring that exact purpose. Omitting purpose from the request does not broaden or bypass a purpose-bound record.

A record with `purpose=None` remains unbound and may satisfy a requirement regardless of whether the caller declares a purpose. This preserves backward compatibility while allowing applications to progressively adopt purpose limitation.

TRIA does not infer purpose from action text, resource names, provider payloads, model output, or metadata. Purpose must be supplied explicitly by the application or participant making the governed request.

Examples:

- consent for `persistent_context` with purpose `support` does not authorize `marketing`;
- `READ` permission for `profile:x` with purpose `support` cannot be used for `research`;
- a purpose-bound `DELEGATE` permission may propagate authority only for the same declared purpose;
- runtime requirements carry purpose independently for consent and capability checks.

Purpose limitation does not substitute for scope, capability, lifecycle, policy, or consent checks. All applicable governance boundaries must independently allow the operation.
