import json
import subprocess
import sys
from dataclasses import replace
from datetime import datetime
import pytest
from tria import *


def request():return InvocationRequest('agent:b','read','local')
def relationship():return Tria().create_relationship(['human:a','agent:b'])


def test_external_resolver_and_no_read_no_fetch():
    r=relationship();seen=[]
    def resolve(resource):seen.append(resource);return ContextItem(resource, {'name':'Profile'}, provenance=('vault:1',))
    runtime=Runtime(resource_resolver=resolve)
    q=InvocationRequest('agent:b','read','local',context_resources=('context:profile',))
    assert not runtime.prepare(r,q).allowed and not seen
    r.admin.grant_permission('human:a','agent:b','context:profile',Capability.READ)
    p=runtime.prepare(r,q)
    assert p.allowed and p.context[0].value['name']=='Profile' and len(seen)==1


def test_resolver_revocation_cannot_execute():
    r=relationship();r.grant_consent('human:a','scope');r.admin.grant_permission('human:a','agent:b','context:profile',Capability.READ)
    def resolve(resource):r.revoke_consent('human:a','scope');return ContextItem(resource,'private')
    q=InvocationRequest('agent:b','read','local',context_resources=('context:profile',),consent_requirements=(ConsentRequirement('human:a','scope'),))
    seen=[];receipt=ExecutionBridge(Runtime(resolve)).execute(r,q,OpenAIResponsesAdapter(),lambda p:seen.append(p),model='mock')
    assert not seen and not receipt.plan.allowed

@pytest.mark.parametrize('resource',['context:profile','claim:missing'])
def test_unknown_resource_records_failure(resource):
    r=relationship();r.admin.grant_permission('human:a','agent:b',resource,Capability.READ)
    with pytest.raises(UnknownResourceError):Runtime().prepare(r,InvocationRequest('agent:b','read','local',context_resources=(resource,)))
    assert r.events[-1].payload['status']=='FAILED'


def test_resolver_wrong_resource_rejected():
    r=relationship();r.admin.grant_permission('human:a','agent:b','x',Capability.READ)
    with pytest.raises(UnknownResourceError):Runtime(lambda x:ContextItem('different','secret')).prepare(r,InvocationRequest('agent:b','read','local',context_resources=('x',)))


def test_nested_transport_conversion_detaches():
    p=ProviderRequest('local','r',{'nested':[{'data':[1,2,{'a':True}]}]})
    result=p.to_transport_payload();assert json.loads(json.dumps(result))==result
    result['nested'][0]['data'].append(3)
    assert len(p.payload['nested'][0]['data'])==3
    with pytest.raises(ProviderTranslationError):ProviderRequest('x','r',{'bad':object()}).to_transport_payload()

@pytest.mark.parametrize('adapter,options',[(OpenAIResponsesAdapter(),{'input':'unguarded'}),(OpenAIResponsesAdapter(),{'instructions':'unguarded'}),(AnthropicMessagesAdapter(),{'system':'unguarded'}),(AnthropicMessagesAdapter(),{'messages':[]})])
def test_prompt_overrides_fail_before_executor(adapter,options):
    r=relationship();seen=[]
    with pytest.raises(ProviderTranslationError):ExecutionBridge().execute(r,request(),adapter,lambda p:seen.append(p),model='mock',**options)
    assert not seen and r.events[-1].payload['status']=='FAILED'

@pytest.mark.parametrize('native',[None,{}, {'id':'x'}, {'status':'completed'}, {'id':'x','status':'invented'}])
def test_missing_or_incomplete_response_unknown(native):
    r=relationship();out=ExecutionBridge().execute(r,request(),OpenAIResponsesAdapter(),lambda p:native,model='mock')
    assert out.executed and out.result.status=='UNKNOWN_EFFECT'
    assert r.events[-1].payload['status']=='UNKNOWN_EFFECT'


def test_executor_exception_preserves_uncertainty_without_payload():
    r=relationship()
    def fail(p):raise RuntimeError('SECRET transport body')
    with pytest.raises(ExecutionError) as error:ExecutionBridge().execute(r,request(),OpenAIResponsesAdapter(),fail,model='mock')
    assert error.value.receipt.executed and error.value.receipt.result.status=='UNKNOWN_EFFECT'
    assert 'SECRET' not in str(error.value) and 'SECRET' not in str(r.events)


def test_explicit_provider_failure():
    r=relationship();out=ExecutionBridge().execute(r,request(),OpenAIResponsesAdapter(),lambda p:{'id':'x','status':'failed'},model='mock')
    assert out.result.status=='FAILED'


def test_sqlite_memory_and_closed_store():
    s=SQLiteEventStore(':memory:');r=Tria(s).create_relationship(['human:a']);r.grant_consent('human:a','scope')
    assert Tria(s).load_relationship(r.relationship_id).state.consent
    s.close()
    with pytest.raises(PersistenceError):s.list(r.relationship_id)


def test_sqlite_cross_process_rejected_and_released(tmp_path):
    path=tmp_path/'owner.db'
    s=SQLiteEventStore(path)
    code='from tria import SQLiteEventStore; import sys; s=SQLiteEventStore(sys.argv[1]); s.close()'
    child=subprocess.run([sys.executable,'-c',code,str(path)],text=True,capture_output=True)
    assert child.returncode!=0 and 'owned by another process' in child.stderr
    s.close()
    child=subprocess.run([sys.executable,'-c',code,str(path)],text=True,capture_output=True)
    assert child.returncode==0,child.stderr


def test_same_predecessor_duplicate_retry_and_batch_rollback(tmp_path):
    with SQLiteEventStore(tmp_path/'atomic.db') as s:
        r=Tria(s).create_relationship(['human:a']);root=r.events[0]
        first=RelationalEvent.commit(EventProposal(r.relationship_id,'ConsentGranted','human:a',{'actor':'human:a','scope':'one'},1),root.event_hash)
        stale=RelationalEvent.commit(EventProposal(r.relationship_id,'ConsentGranted','human:a',{'actor':'human:a','scope':'two'},1),root.event_hash)
        s.append(first)
        for event in (stale,first):
            with pytest.raises(ConcurrentWriteError):s.append(event)
        assert r.audit()['chain_valid']
        good=RelationalEvent.commit(EventProposal(r.relationship_id,'ConsentGranted','human:a',{'actor':'human:a','scope':'three'},2),first.event_hash)
        bad=replace(good,event_hash='bad')
        with pytest.raises((PersistenceError,ConcurrentWriteError)):s.append_many([good,bad])
        assert len(r.events)==2 and r.audit()['chain_valid']
        s.append(good);assert len(r.events)==3

@pytest.mark.parametrize('call',[
    lambda:InvocationRequest('', 'do','local'),
    lambda:InvocationRequest('agent:b',None,'local'),
    lambda:InvocationRequest('agent:b','do','local',requirements=('READ',)),
    lambda:ConsentRequirement('human:a','scope',satisfied_conditions=None),
    lambda:CapabilityRequirement('x','READ'),
    lambda:relationship().admin.grant_permission('human:a','agent:b','x','READ'),
    lambda:relationship().grant_consent('human:a',''),
    lambda:relationship().grant_consent('human:a','scope',expires_at='tomorrow'),
    lambda:relationship().grant_consent('human:a','scope',expires_at=datetime.now()),
    lambda:relationship().check_lifecycle_transition('ACTIVE'),
])
def test_actionable_input_errors(call):
    with pytest.raises(InputValidationError):call()


def test_invalid_sqlite_path(tmp_path):
    with pytest.raises(PersistenceError):SQLiteEventStore(tmp_path/'missing'/'db')


def test_export_error_identifies_lifecycle():
    r=relationship();r.admin.grant_permission('human:a','human:a',replay_export_resource(r.relationship_id),Capability.DISCLOSE)
    r.grant_lifecycle_authority('tria:system','human:a');r.transition('human:a',LifecycleState.DISSOLVING)
    with pytest.raises(ReplayExportError,match='DISSOLVING'):export_replay_bundle(r,actor='human:a')


def test_state_nested_immutability():
    r=relationship();r.grant_consent('human:a','scope')
    with pytest.raises(TypeError):r.state.consent[('human:a','scope')]=None
    json.dumps(state_to_dict(r.state))


def test_reservation_survives_reopen(tmp_path):
    path=tmp_path/'repeat.db';q=InvocationRequest('human:a','act','local');calls=[]
    with SQLiteEventStore(path) as store:
        r=Tria(store).create_relationship(['human:a']);rid=r.relationship_id
        ExecutionBridge().execute(r,q,OpenAIResponsesAdapter(),lambda p:calls.append(p) or {'id':'x','status':'completed'},model='mock')
    with SQLiteEventStore(path) as store:
        r=Tria(store).load_relationship(rid)
        with pytest.raises(InvocationAlreadyStartedError):ExecutionBridge().execute(r,q,OpenAIResponsesAdapter(),lambda p:calls.append(p),model='mock')
    assert len(calls)==1


def test_old_envelope_rejected_explicitly():
    assert not check_compatibility('0.1',projection_version='0.4',bundle_format_version='0.1').supported
    with pytest.raises(SchemaCompatibilityError):
        RelationalEvent.commit(EventProposal('old','RelationshipCreated','tria:system',{'participants':['human:a']},1,schema_version='0.1'),None)


def test_none_cannot_be_promoted_by_custom_normalizer():
    class Optimistic(OpenAIResponsesAdapter):
        def normalize_response(self,rid,native):return ProviderResponse('custom',rid,'COMPLETED')
    out=ExecutionBridge().execute(relationship(),request(),Optimistic(),lambda p:None,model='mock')
    assert out.result.status=='UNKNOWN_EFFECT'


def test_interrupted_sqlite_batch_rolls_back(tmp_path,monkeypatch):
    with SQLiteEventStore(tmp_path/'interrupted.db') as store:
        r=Tria(store).create_relationship(['human:a']);root=r.events[-1]
        event=RelationalEvent.commit(EventProposal(r.relationship_id,'ConsentGranted','human:a',{'actor':'human:a','scope':'scope'},1),root.event_hash)
        original=RelationalEvent.to_dict
        def interrupt(self):
            if self.event_id==event.event_id:raise KeyboardInterrupt()
            return original(self)
        monkeypatch.setattr(RelationalEvent,'to_dict',interrupt)
        with pytest.raises(KeyboardInterrupt):store.append_many([event])
        assert len(r.events)==1 and r.audit()['chain_valid']
        monkeypatch.setattr(RelationalEvent,'to_dict',original)
        store.append(event);assert len(r.events)==2
