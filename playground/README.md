# TRIA Playground v0.1

**See what changes when relationship becomes part of the architecture.**

This directory contains a browser-only educational prototype for exploring selected TRIA concepts without model credentials, network calls, or a backend.

## Scenarios

1. **Consent & Revocation** — inspect how current consent and READ permission affect a proposed use of relational context.
2. **Contested Reality** — preserve an observation, an interpretation derived from it, and a participant dispute without silently collapsing them into one fact.
3. **Agentic Action** — inspect current action consent and ACT authority before a simulated consequence.

## Important boundary

The v0.1 page is a deterministic visualization, not a second implementation of the TRIA SDK. It intentionally mirrors selected documented concepts so a visitor can understand the architecture before installing Python.

It does **not** provide host authentication, network execution, production authorization, security certification, empirical validation, or a claim of complete SDK conformance. The canonical executable behavior remains the Python package and its tests.

A later playground phase may add a small server-side adapter that invokes the actual SDK and returns sanitized diagnostic/audit output. That should be designed so browser users never receive trusted-host objects or administrative capabilities.

## Run locally

Open `index.html` in a modern browser. No build step or external dependency is required.

## Publishing

The static directory is suitable for GitHub Pages or another static host after review. Do not enable public hosting merely to test this branch; review the copy, behavior, accessibility, and public/private product boundary first.

## Commercial boundary

This public playground demonstrates what selected TRIA relational primitives mean. It is not intended to become the enterprise deployment console. Fleet observability, organizational policy management, managed integrations, enterprise analytics, and proprietary augmentation can remain separate Trivian Technologies product surfaces.

## License

Software in this directory follows the repository software license unless a file states otherwise. Documentation follows the repository documentation license. See the repository root licensing files for controlling terms.