"""Host-owned context resolution and JSON transport conversion, without networking."""
import json
from tria import (Tria, Runtime, ContextItem, Capability, CapabilityRequirement,
    ConsentRequirement, InvocationRequest, ExecutionBridge, OpenAIResponsesAdapter,
    UnknownResourceError)


def main():
    vault = {'context:profile': 'Preferred language: English.'}
    rel = Tria().create_relationship(['human:user','agent:assistant'])
    rel.grant_consent('human:user','profile',purpose='support')
    rel.admin.grant_permission('human:user','agent:assistant','context:profile',Capability.READ,purpose='support')
    def resolve(resource):
        if resource not in vault:
            raise UnknownResourceError('Host vault resource not found; verify the resource key.')
        return ContextItem(resource, vault[resource], provenance=('vault:profile:v1',))
    def executor(wire):
        payload = wire.to_transport_payload()
        # A host HTTP client could send this JSON. This example never sends it.
        assert 'Preferred language' in json.dumps(payload)
        return {'id':'local:response','status':'completed'}
    request = InvocationRequest('agent:assistant','Use the profile.','local',
        context_resources=('context:profile',),
        requirements=(CapabilityRequirement('context:profile',Capability.READ,purpose='support'),),
        consent_requirements=(ConsentRequirement('human:user','profile',purpose='support'),))
    receipt = ExecutionBridge(Runtime(resolve)).execute(rel,request,OpenAIResponsesAdapter(),executor,model='local-mock')
    assert receipt.result.status == 'COMPLETED'
    print('External context resolved; transport payload serialized; local execution COMPLETED.')

if __name__ == '__main__':main()
