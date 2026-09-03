# Execution Bridge

Build 006 composes TRIA Runtime authorization with provider translation and caller-owned execution.

The bridge deliberately does not own API keys, HTTP clients, retries, streaming transports, or provider SDK instances. A caller supplies an executor function or object that accepts a generic `ProviderRequest` and returns a provider-native response. TRIA then normalizes that response through the selected adapter and records the resulting generic `InvocationResult` in the relationship event stream.

## Flow

```text
InvocationRequest
      ↓
TRIA Runtime
      ↓ governance / context filtering
InvocationPlan
      ↓
ProviderAdapter
      ↓
ProviderRequest
      ↓
caller-owned executor / network
      ↓
provider-native response
      ↓
ProviderAdapter.normalize_response
      ↓
InvocationResult
      ↓
relationship event stream
```

A blocked plan never reaches the executor. This keeps authorization upstream of provider execution and preserves the Core/Runtime/provider boundary.
