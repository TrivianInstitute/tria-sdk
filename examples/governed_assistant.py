"""No-network governed assistant. Run: python examples/governed_assistant.py"""
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from tria import (
    Capability, CapabilityRequirement, ConsentRequirement, EpistemicType,
    ExecutionBridge, InvocationRequest, OpenAIResponsesAdapter, Runtime,
    SQLiteEventStore, Tria,
)


def run(database):
    calls = []
    with SQLiteEventStore(database) as store:
        tria = Tria(store)
        rel = tria.create_relationship(['human:user', 'agent:assistant'])
        preference = rel.register_claim('human:user', EpistemicType.OBSERVATION,
            'I prefer meetings after 10 AM.', source_refs=['user:preference'])
        resource = f'claim:{preference.claim_id}'
        rel.grant_consent('human:user', 'persistent_context', purpose='scheduling')
        # admin is a trusted-host capability. Never make it an agent tool.
        rel.admin.grant_permission('human:user', 'agent:assistant', resource,
            Capability.READ, purpose='scheduling')
        bridge = ExecutionBridge(Runtime())

        def executor(provider_request):
            # No networking: demonstrate that only an allowed attempt reads this.
            text = provider_request.payload['input'][0]['content'][0]['text']
            assert 'meetings after 10 AM' in text
            calls.append(provider_request.request_id)
            return {'id': 'local:scheduled-preference', 'status': 'completed'}

        def attempt():
            # Fresh ID for each attempt. action text does not imply requirements.
            request = InvocationRequest(
                requested_by='agent:assistant', action='Suggest a meeting time.',
                target='local-assistant', context_resources=(resource,),
                requirements=(CapabilityRequirement(resource, Capability.READ,
                    purpose='scheduling'),),
                consent_requirements=(ConsentRequirement('human:user',
                    'persistent_context', purpose='scheduling'),))
            return bridge.execute(rel, request, OpenAIResponsesAdapter(), executor,
                model='local-mock')

        allowed = attempt()
        assert allowed.executed and len(calls) == 1
        rel.admin.revoke_permission('human:user', 'agent:assistant', resource, Capability.READ)
        denied_permission = attempt()
        assert not denied_permission.plan.allowed and not denied_permission.executed
        assert len(calls) == 1
        rel.admin.grant_permission('human:user', 'agent:assistant', resource,
            Capability.READ, purpose='scheduling')
        rel.revoke_consent('human:user', 'persistent_context')
        denied_consent = attempt()
        assert not denied_consent.plan.allowed and not denied_consent.executed
        assert len(calls) == 1
        assert not rel.state.consent[('human:user','persistent_context')].active
        audit = rel.audit()
        assert audit['chain_valid'] and audit['relationship_valid']
        history = [{'type': e.event_type, 'status': e.payload.get('status')}
                   for e in rel.events]
        rid = rel.relationship_id
    # All instances are closed before releasing file ownership.
    with SQLiteEventStore(database) as store:
        reopened = Tria(store).load_relationship(rid)
        assert reopened.audit() == audit
        assert not reopened.state.consent[('human:user','persistent_context')].active
    return {'executor_calls': len(calls), 'permission_block': denied_permission.plan.reason,
            'consent_block': denied_consent.plan.reason, 'reopened': True,
            'audit': audit, 'history': history}


if __name__ == '__main__':
    with TemporaryDirectory() as directory:
        print(json.dumps(run(Path(directory)/'assistant.sqlite'), indent=2))
