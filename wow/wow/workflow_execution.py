import json
from wow.provenance import load_jsonld
from pathlib import Path

class Runner:
    def run(self, workflow):
        print(workflow.topological_order)

def execute_workflow(jsonfile: str):
    dct = json.loads(Path(jsonfile).read_text())
    workflow = load_jsonld(dct)
    print(workflow)

    runner = Runner()
    runner.run(workflow)
