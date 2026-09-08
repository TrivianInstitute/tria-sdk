import runpy
from pathlib import Path


def test_complete_governed_tutorial(tmp_path):
    tutorial=runpy.run_path(str(Path(__file__).resolve().parents[1]/'examples/governed_assistant.py'))
    result=tutorial['run'](tmp_path/'assistant.sqlite')
    assert result['executor_calls']==1 and result['reopened']
    assert sum(e['status']=='BLOCKED' for e in result['history'])==2
