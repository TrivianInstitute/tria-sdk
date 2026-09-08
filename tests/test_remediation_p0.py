from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import threading
import pytest
from tria import *


def scenario():
    r = Tria().create_relationship(['human:a','agent:b'])
    r.admin.grant_permission('human:a','agent:b','x',Capability.ACT)
    r.grant_consent('human:a','scope')
    q = InvocationRequest('agent:b','act','local',requirements=(CapabilityRequirement('x',Capability.ACT),),consent_requirements=(ConsentRequirement('human:a','scope'),))
    return r,q


def run_mutation(r,q,mutation):
    calls=[]
    class Adapter(OpenAIResponsesAdapter):
        def translate(self,plan,**kw):
            mutation()
            return super().translate(plan,**kw)
    result=ExecutionBridge().execute(r,q,Adapter(),lambda p:calls.append(p) or {'id':'ok','status':'completed'},model='mock')
    return result,calls

@pytest.mark.parametrize('kind',['permission','consent','purpose','conditions','lifecycle','policy'])
def test_translation_neighbor_mutation(kind):
    r,q=scenario()
    def mutation():
        if kind=='permission': r.admin.revoke_permission('human:a','agent:b','x',Capability.ACT)
        if kind=='consent': r.revoke_consent('human:a','scope')
        if kind=='purpose': r.admin.grant_permission('human:a','agent:b','x',Capability.ACT,purpose='narrow-purpose')
        if kind=='conditions': r.admin.grant_permission('human:a','agent:b','x',Capability.ACT,conditions=('new-condition',))
        if kind=='lifecycle':
            r.grant_lifecycle_authority('tria:system','human:a');r.transition('human:a',LifecycleState.DISSOLVING)
        if kind=='policy':
            r.grant_policy_authority('tria:system','human:a','scope');r.register_policy('human:a','policy','2','scope',consent_impacting=True)
    receipt,calls=run_mutation(r,q,mutation)
    assert not calls and not receipt.plan.allowed
    assert r.events[-1].payload['status'] in ('BLOCKED','PAUSED')
    assert receipt.plan.reason

@pytest.mark.parametrize('kind',['permission','consent'])
def test_expiry_during_translation(kind,monkeypatch):
    import tria.governance as governance
    r,q=scenario(); now=datetime.now(timezone.utc)
    if kind=='permission':r.admin.grant_permission('human:a','agent:b','x',Capability.ACT,expires_at=now+timedelta(seconds=1))
    else:r.grant_consent('human:a','scope',expires_at=now+timedelta(seconds=1))
    monkeypatch.setattr(governance,'utcnow',lambda:now)
    receipt,calls=run_mutation(r,q,lambda:monkeypatch.setattr(governance,'utcnow',lambda:now+timedelta(seconds=2)))
    assert not calls and 'expired' in receipt.plan.reason


def test_prepared_request_reused_after_revocation():
    r,q=scenario();bridge=ExecutionBridge();prepared=bridge.prepare(r,q,OpenAIResponsesAdapter(),model='mock')
    assert prepared.plan.allowed
    r.admin.revoke_permission('human:a','agent:b','x',Capability.ACT)
    calls=[];new=bridge.execute(r,prepared.plan.request,OpenAIResponsesAdapter(),lambda p:calls.append(p),model='mock')
    assert not calls and not new.plan.allowed


def test_exactly_once_and_duplicate_attempt():
    r,q=scenario();calls=[];bridge=ExecutionBridge()
    first=bridge.execute(r,q,OpenAIResponsesAdapter(),lambda p:calls.append(p) or {'id':'ok','status':'completed'},model='mock')
    assert first.executed and len(calls)==1
    with pytest.raises(InvocationAlreadyStartedError):
        bridge.execute(r,q,OpenAIResponsesAdapter(),lambda p:calls.append(p),model='mock')
    assert len(calls)==1


def test_concurrent_revoke_before_guard_wins():
    r,q=scenario();translated=threading.Event();revoked=threading.Event();calls=[]
    class Adapter(OpenAIResponsesAdapter):
        def translate(self,plan,**kw):
            translated.set();assert revoked.wait(2);return super().translate(plan,**kw)
    def revoke():
        assert translated.wait(2);r.admin.revoke_permission('human:a','agent:b','x',Capability.ACT);revoked.set()
    with ThreadPoolExecutor(1) as pool:
        future=pool.submit(revoke)
        result=ExecutionBridge().execute(r,q,Adapter(),lambda p:calls.append(p),model='mock');future.result()
    assert not calls and not result.plan.allowed


def test_concurrent_revoke_after_executor_entry_is_ordered():
    r,q=scenario();entered=threading.Event();attempted=threading.Event();revoked=threading.Event()
    def revoke():
        assert entered.wait(2);attempted.set();r.admin.revoke_permission('human:a','agent:b','x',Capability.ACT);revoked.set()
    def executor(p):
        entered.set();assert attempted.wait(2);assert not revoked.is_set();return {'id':'ok','status':'completed'}
    with ThreadPoolExecutor(1) as pool:
        future=pool.submit(revoke)
        result=ExecutionBridge().execute(r,q,OpenAIResponsesAdapter(),executor,model='mock');future.result(timeout=2)
    assert result.executed and revoked.is_set()
    assert r.check_capability('agent:b','x',Capability.ACT).outcome==GovernanceOutcome.BLOCK


def test_nonparticipant_empty_and_missing():
    with pytest.raises(RelationshipNotFoundError):Tria().load_relationship('missing')
    r=Relationship('empty',InMemoryEventStore());assert not r.audit()['relationship_valid']
    assert not Runtime().prepare(r,InvocationRequest('agent:b','do','local')).allowed
    assert not r.audit()['relationship_valid']
    good=Tria().create_relationship(['human:a']);assert not Runtime().prepare(good,InvocationRequest('unknown','do','local')).allowed
    with pytest.raises(InputValidationError):Tria().create_relationship([])
    with pytest.raises(InputValidationError):Tria().create_relationship([''])
    with pytest.raises(InputValidationError):Tria().create_relationship(['human:a','human:a'])
    with pytest.raises(UnknownParticipantError):good.admin.grant_permission('human:a','unknown','x',Capability.ACT)


def test_direct_admin_vs_participant_delegation():
    r=Tria().create_relationship(['human:a','agent:b','agent:c'])
    with pytest.raises(DelegationError):r.delegate_permission('agent:b','agent:c','x',Capability.ACT)
    r.admin.grant_permission('human:a','agent:b','x',Capability.DELEGATE)
    r.delegate_permission('agent:b','agent:c','x',Capability.ACT)
    assert r.check_capability('agent:c','x',Capability.ACT).outcome==GovernanceOutcome.ALLOW


def test_caller_created_state_and_custom_engine_cannot_drop_floor():
    assert GovernanceEngine().require_runtime_execution(RelationalState('fake')).outcome==GovernanceOutcome.BLOCK
    r,q=scenario();r.admin.revoke_permission('human:a','agent:b','x',Capability.ACT)
    class Allow(GovernanceEngine):
        def require_capability(self,*a,**kw):return GovernanceDecision(GovernanceOutcome.ALLOW,'fake','1','allow')
    custom=Relationship(r.relationship_id,r._store,Allow())
    assert not Runtime().prepare(custom,q).allowed


def test_custom_runtime_cannot_override_final_gate():
    r,q=scenario();r.revoke_consent('human:a','scope');calls=[]
    class UnsafeRuntime(Runtime):
        def prepare(self,r,q):return InvocationPlan(q,GovernanceOutcome.ALLOW,())
    receipt=ExecutionBridge(UnsafeRuntime()).execute(r,q,OpenAIResponsesAdapter(),lambda p:calls.append(p),model='mock')
    assert not calls and not receipt.plan.allowed


def test_reentrant_governance_change_detected():
    r,q=scenario();count=[]
    class Changing(GovernanceEngine):
        def require_capability(self,*a,**kw):
            if len(count)>0:r.revoke_consent('human:a','scope')
            count.append(1);return super().require_capability(*a,**kw)
    r._governance=Changing();calls=[]
    result=ExecutionBridge().execute(r,q,OpenAIResponsesAdapter(),lambda p:calls.append(p),model='mock')
    assert not calls and not result.plan.allowed


def test_store_without_execution_guard_fails_explicitly():
    memory=InMemoryEventStore()
    class LegacyStore:
        append=memory.append;append_many=memory.append_many;list=memory.list
    r=Tria(LegacyStore()).create_relationship(['human:a'])
    with pytest.raises(UnsupportedStoreError):
        ExecutionBridge().execute(r,InvocationRequest('human:a','do','local'),OpenAIResponsesAdapter(),lambda p:None,model='mock')
