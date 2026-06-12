from wow.demo_workflow import write_workflow_json
from wow.workflow_execution import execute_workflow
from pathlib import Path

def consistency_check(filename: str):
    from wow.provenance import load_jsonld
    import json
    s = Path(filename).read_text()
    dct = json.loads(Path(filename).read_text())
    obj = load_jsonld(dct)
    s2 = json.dumps(obj.to_jsonld(), indent=4)
    assert s == s2, (s, s2)

write_workflow_json('workflow.jsonld')
execute_workflow('workflow.jsonld', 'workflow_results.jsonld')

consistency_check('workflow_results.jsonld')
