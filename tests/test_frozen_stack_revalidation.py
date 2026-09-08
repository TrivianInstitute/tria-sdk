"""New observations of merged SDK behavior; not substitutes for unchanged frozen tests."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
import threading
import pytest
from tria import Tria, Capability, ExecutionBridge, InvocationRequest, OpenAIResponsesAdapter
from tria.runtime import CapabilityRequirement, ConsentRequirement
from tria.types import GovernanceOutcome, LifecycleState
from tria.store import InMemoryEventStore
from tria.events import verify_event_chain
from tria.errors import (ConcurrentWriteError, InvocationAlreadyStartedError, ExecutionError, UnknownParticipantError)


def ready():
    r = Tria().create_relationship(['a','b'])
    r.grant_permission('a','b','resource',Capability.ACT)
    q = InvocationRequest('b','act','local',requirements=(CapabilityRequirement('resource',Capability.ACT),))
    return r, q


def execute(r, q, executor, adapter=None):
    return ExecutionBridge().execute(r,q,adapter or OpenAIResponsesAdapter(),executor,model='synthetic')


def test_F003_replay_exception_still_has_exactly_one_effect():
    r,q = ready(); effects=[]
    def executor(req): effects.append(req); return {'status':'completed'}
    execute(r,q,executor)
    with pytest.raises(InvocationAlreadyStartedError): execute(r,q,executor)
    assert len(effects) == 1


def test_F007_conflict_rejected_chain_valid_and_explicit_retry():
    class BarrierStore(InMemoryEventStore):
        barrier = None
        def append(self, event):
            if self.barrier is not None: self.barrier.wait(timeout=5)
            super().append(event)
    store = BarrierStore(); r = Tria(store).create_relationship(['a','b'])
    store.barrier = threading.Barrier(2)
    def attempt(actor):
        try: r.grant_consent(actor,'scope'); return None
        except ConcurrentWriteError: return actor
    with ThreadPoolExecutor(2) as pool: outcomes=list(pool.map(attempt,['a','b']))
    assert sum(x is None for x in outcomes) == 1
    assert verify_event_chain(r.events) and len(r.events) == 2
    store.barrier = None
    r.grant_consent(next(x for x in outcomes if x is not None),'scope')
    assert verify_event_chain(r.events) and len(r.events) == 3


def test_F008_unknown_effect_is_recorded_and_receipt_exposes_uncertainty():
    r,q=ready(); effects=[]
    def executor(req): effects.append('effect'); raise RuntimeError('injected')
    with pytest.raises(ExecutionError) as caught: execute(r,q,executor)
    assert effects == ['effect']
    assert caught.value.receipt.result.status == 'UNKNOWN_EFFECT'
    assert any(e.event_type == 'InvocationResultRecorded' and e.payload['status'] == 'UNKNOWN_EFFECT' for e in r.events)


def test_F035_post_audit_unknown_grantor_rejected_without_authority_change():
    r,q=ready(); r.revoke_permission('a','b','resource',Capability.ACT); before=tuple(r.events)
    with pytest.raises(UnknownParticipantError): r.grant_permission('c','b','resource',Capability.ACT)
    assert tuple(r.events) == before
    assert r.check_capability('b','resource',Capability.ACT).outcome is GovernanceOutcome.BLOCK

@pytest.mark.parametrize('change', ['permission','consent','expiry','relationship'])
def test_F001_F002_final_state_changes_block_executor(change):
    r,q=ready(); effects=[]
    if change == 'consent':
        r.grant_consent('a','use'); q=replace(q,consent_requirements=(ConsentRequirement('a','use'),))
    class Changing(OpenAIResponsesAdapter):
        def translate(self,*args,**kw):
            result=super().translate(*args,**kw)
            if change == 'permission': r.revoke_permission('a','b','resource',Capability.ACT)
            elif change == 'consent': r.revoke_consent('a','use')
            elif change == 'expiry':
                r.grant_permission('a','b','resource',Capability.ACT,expires_at=datetime.now(timezone.utc)-timedelta(seconds=1))
            else:
                r.grant_lifecycle_authority('tria:system','a')
                r.transition('a',LifecycleState.DISSOLVING)
            return result
    execute(r,q,lambda req: effects.append(req),Changing())
    assert not effects
