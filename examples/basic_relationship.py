from tria import Tria

tria = Tria()
relationship = tria.create_relationship(["human:alice", "agent:demo"])
relationship.grant_consent(actor="human:alice", scope="persistent_context")

print(relationship.state)
print(relationship.audit())
