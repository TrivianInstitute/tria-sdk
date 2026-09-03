from tria import Capability, Tria, export_replay_bundle, replay_export_resource


tria = Tria()
relationship = tria.create_relationship(["human:user", "agent:demo"])

resource = replay_export_resource(relationship.relationship_id)
relationship.grant_permission(
    "human:user",
    "human:user",
    resource,
    Capability.DISCLOSE,
)

bundle = export_replay_bundle(relationship, actor="human:user")
print(bundle.to_json())
