# Quickstart

TRIA is a Python governance and history layer for ongoing relationships. It can
check declared consent and resource permissions before your application calls an
executor. It does not provide an AI model, agent orchestration, authentication,
credentials, networking, or proof that a deployment's consent is legitimate.

Requirements: Python 3.11 or 3.12 and Git. The file-backed tutorial currently uses
POSIX process locks (Linux/macOS). Other platforms can use InMemoryEventStore;
file-backed SQLite raises UnsupportedStoreError where process locks are unavailable.

```bash
git clone https://github.com/TrivianInstitute/tria-sdk.git
cd tria-sdk
# Select the remediation branch while reviewing this prerelease.
git checkout remediation/clean-room-p0-p1
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
python -m pytest -q
python examples/governed_assistant.py
```

Windows activation is `.venv\Scripts\Activate.ps1` in PowerShell; the file-backed
tutorial is POSIX-only for this prerelease. Do not silently disable process locking.
For importing TRIA only, the distribution is **tria-core**, the namespace is
**tria**, and the repository is **tria-sdk**. No runtime dependencies are required.

The tutorial prints `executor_calls: 1`, two denial reasons, `reopened: true`,
and an integrity summary plus chronological event statuses. It uses no network,
API credentials, provider SDK, creator knowledge, or research repository.

Continue with [the complete application](complete-governed-application.md).
