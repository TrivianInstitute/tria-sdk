# SPDX-License-Identifier: MPL-2.0
"""Frozen-plan pilot runner. CLI is offline-only; external execution requires caller injection and exact plan approval."""
from __future__ import annotations
import argparse, hashlib, json, os, random, time, uuid
from collections import Counter
from dataclasses import asdict, dataclass
from decimal import Decimal, ROUND_CEILING
from pathlib import Path
from . import harness
from .model_adapter import CompletionRequest, DecisionModelAdapter, FORMAT_VERSION, MOCK_SETTINGS, ModelSettings, OfflineMockClient, natural, text
ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
PLAN_SCHEMA, RESULT_SCHEMA = "tria.pilot-plan/0.1", "tria.pilot-results/0.1"

def canonical(v): return json.dumps(v, sort_keys=True, separators=(",", ":"), allow_nan=False)
def digest(v): return hashlib.sha256(canonical(v).encode()).hexdigest()
def money(v, name):
    if not isinstance(v, str): raise ValueError(f"{name} must be an exact decimal string.")
    try: amount = Decimal(v)
    except ArithmeticError as exc: raise ValueError(f"Invalid {name}.") from exc
    if not amount.is_finite() or amount < 0 or amount > Decimal("1000000000"): raise ValueError(f"Invalid {name}.")
    return amount

@dataclass(frozen=True, slots=True)
class Limits:
    max_calls: int = 45
    max_input_tokens: int = 20000
    max_output_tokens: int = 300
    max_prompt_bytes: int = 100000
    max_reserved_usd: str = "0"
    def __post_init__(self):
        for n in ("max_calls", "max_input_tokens", "max_output_tokens", "max_prompt_bytes"): natural(getattr(self,n), n, 1)
        money(self.max_reserved_usd, "max_reserved_usd")

@dataclass(frozen=True, slots=True)
class Prices:
    input_usd_per_million: str = "0"
    output_usd_per_million: str = "0"
    reference: str = "offline mock; not provider pricing"
    def __post_init__(self):
        money(self.input_usd_per_million,"input price"); money(self.output_usd_per_million,"output price"); text(self.reference,"reference")
    def bound(self, i, o):
        value=(i*Decimal(self.input_usd_per_million)+o*Decimal(self.output_usd_per_million))/Decimal(1000000)
        return value.quantize(Decimal("0.000000001"), rounding=ROUND_CEILING)

def source_hashes():
    paths=list((REPO/"src/tria").rglob("*.py"))+[ROOT/n for n in ("harness.py","DECISION_RUBRIC.md","experiment.schema.json","model_adapter.py","pilot.py")]
    paths += [REPO/"schemas/tria-diagnostic-report.v0.1.schema.json", REPO/"pyproject.toml"]
    return {str(p.relative_to(REPO)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}

@dataclass(frozen=True, slots=True)
class PilotPlan:
    serialized: str
    sha256: str
    @property
    def document(self): return json.loads(self.serialized)
    def verify(self):
        doc=self.document
        if digest(doc)!=self.sha256 or doc.get("schema")!=PLAN_SCHEMA: raise ValueError("Pilot plan integrity check failed.")
        if source_hashes()!=doc["source_hashes"]: raise ValueError("Source changed after planning; prepare and approve a new plan.")
        return doc

def prepare_pilot(*, settings=MOCK_SETTINGS, limits=Limits(), prices=Prices(), mode="offline_mock", repetitions=1, seed=20260910, scenarios_path=harness.SCENARIOS_PATH, input_counter=None, input_counter_id=None):
    natural(repetitions,"repetitions",1); natural(seed,"seed")
    if mode not in {"offline_mock","external"}: raise ValueError("Unsupported pilot mode.")
    if mode=="offline_mock":
        if settings!=MOCK_SETTINGS or prices!=Prices() or input_counter is not None: raise ValueError("Offline mode uses built-in fixture settings only.")
        input_counter=lambda r:len(r.prompt.encode()); input_counter_id="offline:utf8-bytes-not-model-tokens"
    else:
        if settings.model_id.startswith("mock:") or settings.client_id=="offline-mock": raise ValueError("External mode requires explicit model/client identity.")
        if input_counter is None: raise ValueError("External mode requires a local conservative input counter.")
        text(input_counter_id,"input_counter_id")
        if prices.reference==Prices().reference: raise ValueError("External mode requires explicit pricing reference.")
    raw=Path(scenarios_path).read_bytes(); payload=json.loads(raw); harness.validate_experiment(payload); protocol=payload["protocol"]
    if protocol["max_tool_calls"]!=0: raise ValueError("Pilot supports zero tools only.")
    if protocol["max_output_tokens"]>limits.max_output_tokens: raise ValueError("Frozen protocol exceeds output cap.")
    count=len(payload["scenarios"])*len(harness.CONDITIONS)*repetitions
    if count>limits.max_calls: raise ValueError("Entire paired schedule exceeds max_calls.")
    renderer=DecisionModelAdapter(OfflineMockClient(),settings); trials=[]; total=Decimal(0)
    for scenario in payload["scenarios"]:
        for rep in range(repetitions):
            pair_seed=harness._pair_seed(seed,scenario["id"],rep); packets=harness.build_packets(scenario,protocol,pair_seed)
            rel,request,_=harness._tria_objects(scenario["evidence"]); runtime=harness.Runtime.evaluate(rel,request)
            for condition in harness.CONDITIONS:
                req=renderer.request(packets[condition]); size=len(req.prompt.encode())
                if size>limits.max_prompt_bytes: raise ValueError("Prompt exceeds byte cap; no truncation permitted.")
                tokens=natural(input_counter(req),"input token bound",1)
                if tokens>limits.max_input_tokens: raise ValueError("Prompt exceeds input token cap.")
                reserve=prices.bound(tokens,req.max_output_tokens); total+=reserve
                trials.append({"scenario_id":scenario["id"],"family":scenario["family"],"condition":condition,"repetition":rep,"pair_seed":pair_seed,
                    "evidence_digest":harness.evidence_digest(scenario["evidence"]),"request":asdict(req),"prompt_sha256":hashlib.sha256(req.prompt.encode()).hexdigest(),
                    "input_token_bound":tokens,"reservation_usd":str(reserve),"expected_decision":scenario["evaluator"]["correct_decision"],
                    "counterfactual_runtime_allows":runtime.allowed,"counterfactual_runtime_outcome":runtime.outcome.value})
    if total>Decimal(limits.max_reserved_usd): raise ValueError("Entire paired schedule exceeds reserved USD budget.")
    random.Random(seed).shuffle(trials)
    doc={"schema":PLAN_SCHEMA,"plan_id":str(uuid.uuid4()),"mode":mode,"format_protocol":FORMAT_VERSION,"settings":asdict(settings),"limits":asdict(limits),"prices":asdict(prices),
        "input_counter_id":input_counter_id,"seed":seed,"repetitions":repetitions,"source_hashes":source_hashes(),"corpus_sha256":hashlib.sha256(raw).hexdigest(),"corpus_snapshot":payload,
        "sdk":harness.__version__,"evaluator_policy":harness.EVALUATOR_POLICY,"planned_calls":count,"total_reservation_usd":str(total),"trials":trials}
    return PilotPlan(canonical(doc),digest(doc))

def _new(path): return os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),"w",encoding="utf-8")
def save_new(path,payload):
    with _new(path) as f: f.write(canonical(payload)+"\n"); f.flush(); os.fsync(f.fileno())
class Journal:
    def __init__(self,path): self.f=_new(path); self.prev="0"*64; self.seq=0
    def append(self,event):
        record={"sequence":self.seq,"previous_sha256":self.prev,**event}; checksum=digest(record)
        self.f.write(canonical({**record,"sha256":checksum})+"\n"); self.f.flush(); os.fsync(self.f.fileno()); self.prev=checksum; self.seq+=1
    def close(self): self.f.close()

def summarize(rows):
    conditions={}
    for condition in harness.CONDITIONS:
        subset=[r for r in rows if r["condition"]==condition]; attempted=[r for r in subset if r["attempted"]]; valid=[r for r in attempted if r["status"]=="valid"]
        correct=sum(r["decision_correct"] for r in valid)
        conditions[condition]={"planned":len(subset),"attempted":len(attempted),"valid":len(valid),"invalid":len(attempted)-len(valid),"not_attempted":len(subset)-len(attempted),
            "status_counts":dict(Counter(r["status"] for r in subset)),"decision_accuracy_all_attempted":correct/len(attempted) if attempted else None,"decision_accuracy_valid_only":correct/len(valid) if valid else None}
    complete=bool(rows) and all(r["status"]=="valid" for r in rows); contrasts=None
    if complete:
        a,b,c=(conditions[k] for k in harness.CONDITIONS); contrasts={"structured_minus_ordinary":b["decision_accuracy_all_attempted"]-a["decision_accuracy_all_attempted"],"tria_minus_structured":c["decision_accuracy_all_attempted"]-b["decision_accuracy_all_attempted"]}
    return {"conditions":conditions,"complete_valid_schedule":complete,"paired_accuracy_contrasts":contrasts,"contrast_policy":"Suppress primary contrasts if any planned response is invalid or unattempted."}

def run_pilot(plan,*,output_dir,client=None,approved_plan_sha256=None):
    doc=plan.verify(); offline=doc["mode"]=="offline_mock"
    if offline:
        if client is not None and type(client) is not OfflineMockClient: raise ValueError("Offline mode refuses substituted clients.")
        client=OfflineMockClient() if client is None else client
    else:
        if approved_plan_sha256!=plan.sha256: raise PermissionError("External execution requires approval of this exact plan digest.")
        if client is None or type(client) is OfflineMockClient: raise ValueError("Explicit caller-owned external client required.")
    settings=ModelSettings(**doc["settings"]); limits=Limits(**doc["limits"]); prices=Prices(**doc["prices"])
    if (getattr(client,"client_id",None),getattr(client,"client_version",None))!=(settings.client_id,settings.client_version): raise ValueError("Client identity/version differs from approved plan.")
    adapter=DecisionModelAdapter(client,settings); output_dir=Path(output_dir); output_dir.mkdir(mode=0o700,exist_ok=False)
    with _new(output_dir/".gitignore") as f: f.write("*\n")
    save_new(output_dir/"plan.json",{"sha256":plan.sha256,"document":doc}); journal=Journal(output_dir/"events.jsonl")
    rows=[]; reserved=reported=Decimal(0); unknown=0; calls=0; stop=None
    try:
        journal.append({"event":"run_started","plan_sha256":plan.sha256})
        for index,trial in enumerate(doc["trials"]):
            base={k:v for k,v in trial.items() if k!="request"}; base["trial_index"]=index
            if stop: rows.append({**base,"attempted":False,"status":"not_attempted_after_stop"}); continue
            if source_hashes()!=doc["source_hashes"]: stop="source_changed"; rows.append({**base,"attempted":False,"status":"not_attempted_source_changed"}); continue
            reserve=Decimal(trial["reservation_usd"])
            if calls>=limits.max_calls or reserved+reserve>Decimal(limits.max_reserved_usd): stop="budget_limit"; rows.append({**base,"attempted":False,"status":"not_attempted_budget"}); continue
            req=CompletionRequest(**trial["request"]); calls+=1; reserved+=reserve; journal.append({"event":"call_started","trial_index":index,"request":asdict(req),"reservation_usd":str(reserve)})
            started=time.perf_counter(); attempt=adapter.attempt(req); row={**base,"attempted":True,**attempt.to_dict(),"latency_ms":(time.perf_counter()-started)*1000}; reply=attempt.reply
            if reply is None or reply.input_tokens is None or reply.output_tokens is None:
                unknown+=1; stop="usage_unresolved"; row["status"]="usage_unresolved" if row["status"]=="valid" else row["status"]
            else:
                cost=prices.bound(reply.input_tokens,reply.output_tokens); reported+=cost; row["reported_token_cost_usd"]=str(cost)
                if reply.input_tokens>trial["input_token_bound"] or reply.output_tokens>req.max_output_tokens or cost>reserve: stop="usage_exceeded_reservation"; row["status"]="usage_exceeded_reservation"
            if attempt.status in {"transport_error","invalid_reply","model_mismatch"}: stop=attempt.status
            if row["status"]=="valid": row.update(harness.score_decision(harness.Decision(attempt.decision),harness.Decision(trial["expected_decision"])))
            journal.append({"event":"call_finished","trial_index":index,"result":row}); rows.append(row)
        result={"schema":RESULT_SCHEMA,"mode":doc["mode"],"plan_sha256":plan.sha256,"status":"stopped" if stop else "completed","stop_reason":stop,"live_model_results":"not_run" if offline else "caller_owned_adapter_run",
            "calls_attempted":calls,"reserved_usd":str(reserved),"reported_token_cost_usd":str(reported),"unknown_usage_calls":unknown,"billing_warning":"Reservations depend on caller token bounds, complete prices, and client compliance; not a provider-enforced billing cap.",**summarize(rows),"trials":rows}
        journal.append({"event":"run_finished","status":result["status"],"stop_reason":stop}); result["journal_tail_sha256"]=journal.prev; save_new(output_dir/"results.json",result); return result
    finally: journal.close()

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--run-mock",action="store_true"); p.add_argument("--output-dir",type=Path); args=p.parse_args(argv); plan=prepare_pilot()
    if not args.run_mock: print(json.dumps({"status":"preflight_only","planned_calls":plan.document["planned_calls"],"plan_sha256":plan.sha256},indent=2)); return 0
    if args.output_dir is None: p.error("--run-mock requires a new --output-dir")
    result=run_pilot(plan,output_dir=args.output_dir); print(json.dumps({k:v for k,v in result.items() if k!="trials"},indent=2)); return 0 if result["complete_valid_schedule"] else 1
if __name__=="__main__": raise SystemExit(main())
