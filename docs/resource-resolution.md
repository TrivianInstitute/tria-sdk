# Host-owned external resources

A permission record names a resource; it does not supply that resource's data.
TRIA resolves `claim:<id>` from its claim projection. For other resource names,
construct `Runtime(resource_resolver=resolve)` where `resolve(resource: str)` returns
`ContextItem(resource, value, epistemic_type=None, provenance=())` for exactly that
resource. Unknown resources raise UnknownResourceError instead of returning None.

The host owns the vault/database and authenticates access to it. Runtime invokes
the resolver only after declared requirements pass. The resolver is trusted code;
it must not treat reads as permission to perform extra effects, return unrelated
data, or omit application consent policy. Its value is snapshotted into the context.
ExecutionBridge rechecks after resolution/translation if the callback changes state.

A complete runnable example is [external_context.py](../examples/external_context.py):
`python examples/external_context.py`. It supplies context:profile from a host dict,
declares purpose-bound consent and READ, converts the immutable provider request
with to_transport_payload(), and returns a local mock response without networking.
