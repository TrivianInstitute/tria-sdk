# Provider adapters

Provider adapters sit above the TRIA Runtime boundary. They translate an already-authorized `InvocationPlan` into a provider-specific request shape and normalize provider responses back into generic `InvocationResult` objects.

Adapters MUST NOT:

- bypass Runtime authorization;
- expose context not present in the authorized plan;
- introduce provider concepts into TRIA Core;
- perform implicit persistence of raw provider traffic;
- treat provider output as relational truth.

The reference adapters are dependency-free translators. Applications remain responsible for credentials, network execution, retries, rate limits, and provider SDK lifecycle.

## Flow

```text
Relationship state
      ↓
TRIA Runtime authorization
      ↓
InvocationPlan
      ↓
ProviderAdapter.translate(...)
      ↓
provider request payload
      ↓
application-owned network execution
      ↓
ProviderAdapter.normalize_response(...)
      ↓
InvocationResult
      ↓
TRIA Runtime record_result(...)
```

The first reference translators target OpenAI Responses-style and Anthropic Messages-style request shapes. They intentionally import neither provider SDK.
