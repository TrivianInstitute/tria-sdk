"""Deliberately failing assertions against frozen target. No SDK modifications.
Run from evidence with ../.venv/bin/python -m pytest test_frozen_counterexamples.py -v.
"""
import threading
from concurrent.futures import ThreadPoolExecutor
import pytest
from tria import *

def fixture():
 r=Tria().create_relationship(['human:a','agent:b']);r.grant_permission('human:a','agent:b','x',Capability.READ);r.grant_consent('human:a','scope');return r

@pytest.mark.parametrize('boundary',['permission','consent'])
def test_revocation_before_executor_prevents_consequence(boundary):
 r=fixture();calls=[]
 class RevokingAdapter(OpenAIResponsesAdapter):
  def translate(self,plan,**options):
   if boundary=='permission':r.revoke_permission('human:a','agent:b','x',Capability.READ)
   else:r.revoke_consent('human:a','scope')
   return super().translate(plan,**options)
 request=InvocationRequest('agent:b','action','model',requirements=(CapabilityRequirement('x',Capability.READ),),consent_requirements=(ConsentRequirement('human:a','scope'),))
 ExecutionBridge().execute(r,request,RevokingAdapter(),lambda wire:calls.append(wire) or {'id':'effect'},model='mock')
 assert calls==[], 'Executor ran after required '+boundary+' was revoked during translation'

def test_composed_engine_preserves_relationship_race_block():
 r=fixture();r.revoke_permission('human:a','agent:b','x',Capability.READ);r.grant_permission('agent:b','agent:b','x',Capability.READ)
 assert r.check_capability('agent:b','x',Capability.READ).outcome==GovernanceOutcome.BLOCK
 assert GovernanceEngine().require_capability(r.state,'agent:b','x',Capability.READ).outcome==GovernanceOutcome.BLOCK

def test_missing_relationship_does_not_authorize_execution():
 r=Tria().load_relationship('nonexistent');p=Runtime().prepare(r,InvocationRequest('agent:b','action','model'))
 assert not p.allowed, 'Unknown relationship with no creation event authorized a request'

def test_sqlite_concurrent_writers_preserve_chain(tmp_path):
 gate=threading.Barrier(2)
 class ScheduledStore(SQLiteEventStore):
  def append(self,event):
   # Synchronize after each writer computes its event; no event/source mutation.
   if event.event_type=='ConsentGranted':gate.wait(timeout=5)
   return super().append(event)
 store=ScheduledStore(tmp_path/'race.db');r=Tria(store).create_relationship(['human:a','agent:b'])
 a=Relationship(r.relationship_id,store);b=Relationship(r.relationship_id,store)
 with ThreadPoolExecutor(2) as pool:
  futures=[pool.submit(a.grant_consent,'human:a','s1'),pool.submit(b.grant_consent,'agent:b','s2')]
  for f in futures:f.result(timeout=10)
 assert r.audit()['chain_valid'], 'Both appends completed but shared predecessor produced invalid chain'
