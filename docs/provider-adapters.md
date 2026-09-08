# Provider adapters and transport handoff

Adapters translate authorized plans and normalize response metadata. They do not
own credentials, network clients, streaming, retries or provider SDK instances.
Use ExecutionBridge.execute for the final authority check; direct translate does
not refresh a plan. Live provider compatibility is not certified by these examples.

`ProviderRequest.payload` is deeply frozen. Use the public
`request.to_transport_payload()` method to get a detached dict/list JSON structure.
It recursively converts nested containers and rejects non-JSON host values with
ProviderTranslationError. A shallow `dict(payload)` is insufficient.

Run `python examples/external_context.py` for a complete no-network resolution,
translation, JSON conversion, execution and result example.

## Supported options

| Adapter | Trusted host configuration accepted |
|---|---|
| OpenAIResponsesAdapter | max_output_tokens, temperature, top_p, seed, store |
| AnthropicMessagesAdapter | max_tokens (positive integer), temperature, top_p, top_k, stop_sequences |

`model` is an explicit required argument. Treat all configuration as trusted host
input. Prompt/context replacement through input, instructions, messages, system,
or arbitrary other keywords is rejected, not silently merged. No dangerous
prompt-override escape hatch is provided. Validate values against the real provider
contract when adding a network executor. Do not pass a user/model-generated options
dictionary directly. These translators are not exhaustive provider SDKs.

OpenAI-style normalization requires a response identifier plus recognized status to
report COMPLETED or FAILED. Missing/unknown data is UNKNOWN_EFFECT. Anthropic-style
normalization requires an identifier and recognized stop reason. Result references
are evidence of a reported response, not proof of truth or remote effect integrity.
