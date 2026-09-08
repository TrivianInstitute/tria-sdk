# Current alpha release gate

0.1.0a4 is an experimental remediation prerelease, not a production designation.
The controlling license remains PolyForm Noncommercial License 1.0.0, as stated in
LICENSE.md and pyproject.toml. Commercial use requires a separate written license.
No licensing change, release publication or main-branch merge is part of this phase.

Required gates: original suite with explicit new-version expectations; permanent
frozen-witness regressions; neighboring attacks; public examples and tutorial;
clean editable installation; sdist/wheel build; clean wheel-only application;
SQLite close/reopen; documentation-only revalidation in a fresh environment.

Package/version/constants, README, changelog, compatibility notes, manifest and
schemas must agree. Preserve the original audit and raw witnesses. An original
assertion may terminate by the newly specified safe exception; record this
separately from an unchanged assertion passing. Never suppress a failure without
an explained contract change and direct safety regression.

Passing proves only the tested local behavior and onboarding path. It does not
establish production certification, security, legal compliance, scientific
validation, legitimate consent or deployment safety. Deferred operational work
and the exact tested commit belong in the remediation report.
