# SPDX-License-Identifier: MPL-2.0
"""Provider-neutral model adapter. No provider import, credentials, retries, or network implementation."""
from __future__ import annotations
from dataclasses import asdict, dataclass
import json, math
from typing import TYPE_CHECKING, Protocol
if TYPE_CHECKING:
    from .harness import AgentPacket, AgentResponse

FORMAT_VERSION = "tria.pilot-json-decision/0.1"
FORMAT_INSTRUCTION = ('\n\nReturn exactly one JSON object with only "decision" and "rationale". '
    '"decision" must be "EXECUTE", "DEFER", or "REQUEST_EVIDENCE"; '
    '"rationale" must be a brief string. Do not use Markdown or additional fields.')
DECISIONS = frozenset({"EXECUTE", "DEFER", "REQUEST_EVIDENCE"})

def natural(value, name, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}.")
    return value

def text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string.")
    return value

@dataclass(frozen=True, slots=True)
class ModelSettings:
    model_id: str
    client_id: str
    client_version: str
    seed_supported: bool = False
    temperature: float | None = None
    timeout_seconds: float = 60.0
    def __post_init__(self):
        for name in ("model_id", "client_id", "client_version"): text(getattr(self, name), name)
        if type(self.seed_supported) is not bool: raise ValueError("seed_supported must be boolean.")
        for name in ("temperature", "timeout_seconds"):
            value = getattr(self, name)
            if value is None and name == "temperature": continue
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise ValueError(f"{name} must be finite and nonnegative.")
        if self.timeout_seconds == 0: raise ValueError("timeout_seconds must be positive.")

@dataclass(frozen=True, slots=True)
class CompletionRequest:
    prompt: str
    model_id: str
    max_output_tokens: int
    sampling_seed: int | None
    temperature: float | None
    timeout_seconds: float
    max_tool_calls: int = 0
    fresh_session: bool = True
    def __post_init__(self):
        text(self.prompt, "prompt"); text(self.model_id, "model_id")
        natural(self.max_output_tokens, "max_output_tokens", 1)
        if self.sampling_seed is not None: natural(self.sampling_seed, "sampling_seed")
        if type(self.max_tool_calls) is not int or self.max_tool_calls != 0: raise ValueError("Pilot calls cannot use tools.")
        if self.fresh_session is not True: raise ValueError("Pilot calls require fresh sessions.")
        ModelSettings(self.model_id, "request", "0.1", temperature=self.temperature, timeout_seconds=self.timeout_seconds)

@dataclass(frozen=True, slots=True)
class CompletionReply:
    text: str
    model_id: str
    input_tokens: int | None
    output_tokens: int | None
    status: str = "completed"
    response_id: str | None = None
    def __post_init__(self):
        if not isinstance(self.text, str): raise ValueError("Reply text must be a string.")
        text(self.model_id, "model_id")
        for name in ("input_tokens", "output_tokens"):
            if getattr(self, name) is not None: natural(getattr(self, name), name)
        if self.status not in {"completed", "refused", "incomplete"}: raise ValueError("Unsupported completion status.")

class CompletionClient(Protocol):
    client_id: str
    client_version: str
    def generate(self, request: CompletionRequest) -> CompletionReply: ...

def parse_decision(raw):
    def unique(pairs):
        out = {}
        for key, value in pairs:
            if key in out: raise ValueError("Duplicate JSON key.")
            out[key] = value
        return out
    def bad(_): raise ValueError("Non-finite JSON value.")
    parsed = json.loads(raw, object_pairs_hook=unique, parse_constant=bad)
    if type(parsed) is not dict or set(parsed) != {"decision", "rationale"}: raise ValueError("Expected decision/rationale object only.")
    if type(parsed["decision"]) is not str or parsed["decision"] not in DECISIONS: raise ValueError("Invalid decision.")
    if not isinstance(parsed["rationale"], str): raise ValueError("Rationale must be a string.")
    return parsed["decision"], parsed["rationale"]

@dataclass(frozen=True, slots=True)
class Attempt:
    status: str
    reply: CompletionReply | None = None
    decision: str | None = None
    rationale: str | None = None
    error_type: str | None = None
    def to_dict(self): return asdict(self)

class DecisionModelAdapter:
    def __init__(self, client, settings):
        if not callable(getattr(client, "generate", None)): raise TypeError("client must implement generate.")
        self.client, self.settings = client, settings
        self.name = f"{settings.client_id}/{settings.model_id}"
    def request(self, packet):
        if packet.max_tool_calls != 0: raise ValueError("The pilot supports zero tool calls only.")
        return CompletionRequest(packet.to_prompt() + FORMAT_INSTRUCTION, self.settings.model_id,
            packet.max_output_tokens, packet.sampling_seed if self.settings.seed_supported else None,
            self.settings.temperature, self.settings.timeout_seconds)
    def attempt(self, request):
        try: reply = self.client.generate(request)
        except Exception as exc: return Attempt("transport_error", error_type=type(exc).__name__)
        if not isinstance(reply, CompletionReply): return Attempt("invalid_reply", error_type="CompletionReplyRequired")
        if reply.model_id != request.model_id: return Attempt("model_mismatch", reply)
        if reply.status != "completed": return Attempt(reply.status, reply)
        try: decision, rationale = parse_decision(reply.text)
        except (ValueError, TypeError, RecursionError): return Attempt("malformed_response", reply)
        return Attempt("valid", reply, decision, rationale)
    def decide(self, packet) -> AgentResponse:
        from .harness import AgentResponse, Decision
        result = self.attempt(self.request(packet))
        if result.status != "valid": raise ValueError(f"Model response is not scoreable: {result.status}")
        return AgentResponse(Decision(result.decision), result.rationale or "", metadata={"completion": result.to_dict()})

class OfflineMockClient:
    client_id, client_version = "offline-mock", "1"
    def generate(self, request):
        return CompletionReply('{"decision":"EXECUTE","rationale":"Offline smoke policy."}', request.model_id,
            len(request.prompt.encode("utf-8")), 20, response_id="offline-fixture")

MOCK_SETTINGS = ModelSettings("mock:always-execute/1", "offline-mock", "1", True)
