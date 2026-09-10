# SPDX-License-Identifier: MPL-2.0
import json, socket, sys
from decimal import Decimal
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from evals.agent_comparison_experiment import harness
from evals.agent_comparison_experiment import model_adapter as model
from evals.agent_comparison_experiment import pilot

@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def fail(*a,**k): raise AssertionError("network forbidden")
    monkeypatch.setattr(socket.socket,"connect",fail); monkeypatch.setattr(socket,"create_connection",fail); monkeypatch.setattr(socket,"getaddrinfo",fail)

class Client:
    client_id,client_version="test-client","1"
    def __init__(self,first=None): self.calls=[]; self.first=first
    def generate(self,request):
        self.calls.append(request)
        if len(self.calls)==1 and self.first is not None:
            if isinstance(self.first,BaseException): raise self.first
            return self.first(request)
        return model.CompletionReply('{"decision":"EXECUTE","rationale":"fixture"}',request.model_id,len(request.prompt.encode()),20)

def ext(**kw):
    args=dict(mode="external",settings=model.ModelSettings("fixture:snapshot-1","test-client","1"),limits=pilot.Limits(max_reserved_usd="10"),prices=pilot.Prices("1","2","test fixture; not provider pricing"),input_counter=lambda r:len(r.prompt.encode())+10,input_counter_id="fixture/1")
    args.update(kw); return pilot.prepare_pilot(**args)

@pytest.mark.parametrize("raw",['```json\n{"decision":"EXECUTE","rationale":"x"}\n```','{"decision":"EXECUTE","decision":"DEFER","rationale":"x"}','{"decision":"EXECUTE","rationale":"x","extra":1}','{"decision":"execute","rationale":"x"}','[{"decision":"EXECUTE","rationale":"x"}]','{"decision":"EXECUTE","rationale":NaN}'])
def test_parser_rejects_ambiguous_output(raw):
    with pytest.raises(ValueError): model.parse_decision(raw)

def test_adapter_request_is_blind_and_seed_capability_respected():
    packet=harness.AgentPacket("task",17,300,0,ordinary_records=("record",))
    seeded=model.DecisionModelAdapter(model.OfflineMockClient(),model.MOCK_SETTINGS).request(packet)
    assert seeded.sampling_seed==17 and seeded.max_tool_calls==0 and seeded.fresh_session
    unseeded=model.DecisionModelAdapter(model.OfflineMockClient(),model.ModelSettings("x","y","1")).request(packet)
    assert unseeded.sampling_seed is None
    assert "correct_decision" not in seeded.prompt and "structured_plus_tria" not in seeded.prompt

@pytest.mark.parametrize("kwargs",[{"max_calls":44},{"max_prompt_bytes":1},{"max_input_tokens":1},{"max_output_tokens":299}])
def test_preflight_rejects_incomplete_schedule_or_truncation(kwargs):
    with pytest.raises(ValueError): pilot.prepare_pilot(limits=pilot.Limits(**kwargs))

def test_external_requires_counter_pricing_budget_and_exact_approval(tmp_path):
    with pytest.raises(ValueError): ext(input_counter=None)
    with pytest.raises(ValueError): ext(prices=pilot.Prices())
    with pytest.raises(ValueError): ext(limits=pilot.Limits(max_reserved_usd="0"))
    plan=ext(); client=Client()
    with pytest.raises(PermissionError): pilot.run_pilot(plan,output_dir=tmp_path/"run",client=client,approved_plan_sha256="wrong")
    assert not client.calls and not (tmp_path/"run").exists()

def test_offline_preflight_and_run_have_zero_live_claim_and_zero_effect(tmp_path):
    plan=pilot.prepare_pilot(); doc=plan.verify(); assert doc["planned_calls"]==45 and Decimal(doc["total_reservation_usd"])==0
    result=pilot.run_pilot(plan,output_dir=tmp_path/"run")
    assert result["calls_attempted"]==45 and result["live_model_results"]=="not_run" and result["complete_valid_schedule"]
    assert result["paired_accuracy_contrasts"]=={"structured_minus_ordinary":0.0,"tria_minus_structured":0.0}
    assert (tmp_path/"run/.gitignore").read_text()=="*\n"
    events=[json.loads(x) for x in (tmp_path/"run/events.jsonl").read_text().splitlines()]
    previous="0"*64
    for i,event in enumerate(events):
        checksum=event.pop("sha256"); assert event["sequence"]==i and event["previous_sha256"]==previous and pilot.digest(event)==checksum; previous=checksum
    assert previous==result["journal_tail_sha256"]

def test_refusal_is_retained_no_retry_and_suppresses_contrast(tmp_path):
    def refused(r): return model.CompletionReply("{}",r.model_id,len(r.prompt.encode()),10,status="refused")
    plan=ext(); client=Client(refused); result=pilot.run_pilot(plan,output_dir=tmp_path/"run",client=client,approved_plan_sha256=plan.sha256)
    assert len(client.calls)==45 and result["trials"][0]["status"]=="refused" and result["paired_accuracy_contrasts"] is None

def test_usage_unknown_or_overrun_stops_following_calls(tmp_path):
    for kind in ("unknown","overrun"):
        def first(r,kind=kind): return model.CompletionReply('{"decision":"EXECUTE","rationale":"x"}',r.model_id,None if kind=="unknown" else len(r.prompt.encode()),10 if kind=="unknown" else 301)
        plan=ext(); client=Client(first); result=pilot.run_pilot(plan,output_dir=tmp_path/kind,client=client,approved_plan_sha256=plan.sha256)
        assert len(client.calls)==1 and result["status"]=="stopped" and sum(not x["attempted"] for x in result["trials"])==44 and result["paired_accuracy_contrasts"] is None

def test_transport_exception_does_not_log_secret_and_stops(tmp_path):
    secret="SECRET-CREDENTIAL"; plan=ext(); client=Client(RuntimeError(secret)); result=pilot.run_pilot(plan,output_dir=tmp_path/"run",client=client,approved_plan_sha256=plan.sha256)
    assert len(client.calls)==1 and result["status"]=="stopped" and secret not in (tmp_path/"run/events.jsonl").read_text() and secret not in (tmp_path/"run/results.json").read_text()

def test_interruption_has_durable_start_and_no_retry(tmp_path):
    plan=ext(); client=Client(KeyboardInterrupt())
    with pytest.raises(KeyboardInterrupt): pilot.run_pilot(plan,output_dir=tmp_path/"run",client=client,approved_plan_sha256=plan.sha256)
    assert len(client.calls)==1
    events=[json.loads(x) for x in (tmp_path/"run/events.jsonl").read_text().splitlines()]
    assert events[-1]["event"]=="call_started" and not (tmp_path/"run/results.json").exists()

def test_cli_defaults_to_preflight_only(monkeypatch,capsys):
    monkeypatch.setattr(model.OfflineMockClient,"generate",lambda *a,**k:(_ for _ in ()).throw(AssertionError("must not call")))
    assert pilot.main([])==0 and json.loads(capsys.readouterr().out)["status"]=="preflight_only"
