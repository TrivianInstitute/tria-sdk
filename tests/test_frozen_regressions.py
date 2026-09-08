"""Run exact historical witnesses, accepting only specified safe rejection paths."""
import importlib.util
from pathlib import Path
import pytest
from tria import ConcurrentWriteError, RelationshipNotFoundError, SQLiteEventStore, verify_event_chain

spec = importlib.util.spec_from_file_location('frozen', Path(__file__).parent/'frozen/clean_room_witnesses.py')
frozen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(frozen)

@pytest.mark.parametrize('boundary', ['permission', 'consent'])
def test_exact_translation_witness(boundary):
    frozen.test_revocation_before_executor_prevents_consequence(boundary)

def test_exact_modularity_witness():
    frozen.test_composed_engine_preserves_relationship_race_block()

def test_exact_missing_relationship_witness():
    with pytest.raises(RelationshipNotFoundError):
        frozen.test_missing_relationship_does_not_authorize_execution()

def test_exact_concurrent_witness_safe_rejection(tmp_path):
    with pytest.raises(ConcurrentWriteError):
        frozen.test_sqlite_concurrent_writers_preserve_chain(tmp_path)
    store = SQLiteEventStore(tmp_path/'race.db')
    # Audit independently even though the original witness exited by rejection.
    rows = store._session.conn.execute('SELECT DISTINCT relationship_id FROM events').fetchall()
    assert len(rows) == 1
    assert len(store.list(rows[0][0])) == 2
    assert verify_event_chain(store.list(rows[0][0]))
    store.close()
