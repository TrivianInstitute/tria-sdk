# Hosted TRIA Playground

Status: proposed deployment architecture. No public SDK-backed service is represented as deployed by this document.

The public static Playground demonstrates selected TRIA concepts. A future hosted mode may allow a visitor to run the same bounded scenarios through the canonical TRIA SDK without installing the repository locally.

## Purpose

The hosted Playground should reduce adoption friction while preserving the trust boundary established by the SDK. Its first public form should remain a constrained demonstration service, not a general-purpose TRIA API.

```text
browser
  ↓
public edge / abuse controls
  ↓
scenario API
  ↓
allowlisted scenario dispatcher
  ↓
canonical TRIA SDK
  ↓
sanitized result projection
  ↓
browser
```

## Initial public scope

The initial hosted service should expose only the bounded scenarios already represented in the Playground:

- Consent & Revocation
- Contested Reality
- Agentic Action

A request may select a known scenario and a documented scenario option. It should not accept arbitrary Python, shell commands, URLs, provider credentials, model prompts, resource identifiers, executors, or host-administration operations.

Each evaluation should begin from fresh ephemeral relationship state unless a later, separately reviewed feature explicitly requires persistence.

## Required gates before public deployment

A hosted service should not be treated as launch-ready until the following properties are demonstrated and reviewed.

### Request boundary

- strict request schema and allowlist
- small request-body limit
- content-type enforcement
- rejection of unknown fields and values
- no arbitrary executor, resource, action, or network target supplied by the browser

### Runtime isolation

- ephemeral scenario state
- least-privilege service identity
- no provider credentials required for the bounded scenarios
- no shell or subprocess execution path
- no unrestricted outbound network requirement
- resource and execution limits appropriate to the host

### Abuse resistance

- edge rate limiting
- request timeouts
- concurrency limits
- bounded response size
- operational mechanism to disable the service without changing SDK semantics

### Privacy and logging

- do not solicit personal or sensitive information for the bounded demonstration
- minimize request logging
- do not log raw relational payloads when aggregate operational data is sufficient
- document retention behavior before collecting telemetry
- distinguish optional product analytics from security/availability telemetry

### Response boundary

Public responses should remain safe projections. They should not expose trusted-host objects, administrative capabilities, stores, raw event payloads, integrity secrets, credentials, stack traces, filesystem paths, or internal deployment metadata.

### Verification

Before deployment, tests should cover at minimum:

- every public scenario and option
- malformed and oversized requests
- unknown fields and values
- content-type failures
- response-schema stability
- HTML/script injection attempts against rendered fields
- executor-call invariants after revocation
- concurrency and timeout behavior
- failure behavior when the SDK raises unexpectedly

The existing SDK test suite remains necessary but is not sufficient evidence of hosted-service security or operational readiness.

## Epistemic labeling

The interface should identify which mode produced a result:

- **Illustrative** means browser-only deterministic demonstration.
- **SDK-backed** means the result was produced through the canonical TRIA SDK.

Neither label implies production certification, scientific validation, legal compliance, or deployment safety.

## What remains out of scope for the initial hosted service

The initial public service should not provide arbitrary model conversations, user accounts, persistent user histories, organization administration, fleet observability, policy administration, enterprise analytics, external action execution, or proprietary augmentation.

Those capabilities create different trust, privacy, security, and product boundaries and should be evaluated separately rather than growing implicitly out of the public demonstration endpoint.

## Deployment-neutral service contract

The hosted boundary should remain portable across infrastructure providers. The browser should depend on a small versioned HTTP contract rather than provider-specific behavior. Infrastructure configuration, secrets, domains, and environment-specific controls should live outside the core SDK semantics.

A deployment implementation should document its own threat model, data flow, operational ownership, incident response path, and rollback procedure before public use.

## Relationship to the local adapter

`playground/adapter.py` is a local demonstration adapter and should remain loopback-oriented. A hosted service may reuse the safe scenario-dispatch concepts and canonical SDK scenario behavior, but it should not be created by simply binding the local adapter to a public interface.

The hosted boundary is a deployment surface of its own and requires independent review.