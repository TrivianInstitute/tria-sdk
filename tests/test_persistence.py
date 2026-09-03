import json
import sqlite3

from tria import EpistemicType, SQLiteEventStore, Tria, verify_event_chain


def test_sqlite_relationship_survives_restart(tmp_path):
    db = tmp_path / "tria.db"
    store = SQLiteEventStore(db)
    rel = Tria(store).create_relationship(["human:a", "agent:b"])
    rel.grant_consent("human:a", "memory")
    obs = rel.register_claim("agent:b", EpistemicType.OBSERVATION, "Latency increased.", source_refs=["sensor:latency"])
    rid = rel.relationship_id

    reopened = Tria(SQLiteEventStore(db)).load_relationship(rid)
    assert reopened.state.consent[("human:a", "memory")].active is True
    assert reopened.state.claims[obs.claim_id].content == "Latency increased."
    assert reopened.audit()["reconstructable"] is True
    assert reopened.audit()["chain_valid"] is True


def test_event_json_round_trip_preserves_hash(tmp_path):
    db = tmp_path / "tria.db"
    rel = Tria(SQLiteEventStore(db)).create_relationship(["human:a", "agent:b"])
    rel.grant_consent("human:a", "memory")
    events = rel.events
    assert all(event.verify_hash() for event in events)
    assert verify_event_chain(events)


def test_tampering_breaks_chain_validation(tmp_path):
    db = tmp_path / "tria.db"
    rel = Tria(SQLiteEventStore(db)).create_relationship(["human:a", "agent:b"])
    rel.grant_consent("human:a", "memory")

    with sqlite3.connect(db) as conn:
        row = conn.execute("SELECT commit_index, event_json FROM events WHERE relationship_id = ? ORDER BY commit_index DESC LIMIT 1", (rel.relationship_id,)).fetchone()
        payload = json.loads(row[1])
        payload["payload"]["scope"] = "tampered"
        conn.execute("UPDATE events SET event_json = ? WHERE commit_index = ?", (json.dumps(payload, sort_keys=True, separators=(",", ":")), row[0]))

    reopened = Tria(SQLiteEventStore(db)).load_relationship(rel.relationship_id)
    assert reopened.audit()["hashes_valid"] is False
    assert reopened.audit()["chain_valid"] is False
