import json
from wow.provenance import load_jsonld
from wow.provenance import rdfclass
from pathlib import Path
from importlib import import_module

from wow.workflow_definition import wf, Task, Namespace

prov = Namespace("http://www.w3.org/ns/prov#", prefix="prov")

def import_target(target: str):
    module_name, func_name = target.rsplit(".", 1)
    module = import_module(module_name)
    return getattr(module, func_name)

@rdfclass(wf, subclassof=[prov.Activity])
class TaskExecution:
    task = wf.executed_task(type_of_value=Task)
    output = wf.generatedOutput(subpropertyof=prov.generated)
    start_time = wf.start_time(subpropertyof=prov.startedAtTime)
    end_time = wf.end_time(subpropertyof=prov.endedAtTime)
    inputs = wf.inputs(subpropertyof=prov.used)
    state = wf.hasTaskState()

def tasks_to_outputs(value, outputs):
    # Replace tasks with their outputs
    print(value, '\n!!!rdftype:', value._rdftype)
    if isinstance(value, Task):
        return outputs[value.identity]

    # TODO: Does not support recursive visits
    return value

class Runner:
    def run(self, workflow):
        # Temporarily store outputs of tasks here
        outputs = {}

        for task in workflow.topological_order:
            print(task.identity)
            print(dir(task))
            print(task.target)
            print(task.arguments)
            func = import_target(task.target)
            kwargs = {argument.argument: tasks_to_outputs(argument.value, outputs) for argument in task.arguments}
            # Store outputs
            outputs[task.identity] = func(**kwargs)
        print(outputs)

def execute_workflow(jsonfile: str):
    dct = json.loads(Path(jsonfile).read_text())
    workflow = load_jsonld(dct)
    print(workflow)

    runner = Runner()
    runner.run(workflow)
