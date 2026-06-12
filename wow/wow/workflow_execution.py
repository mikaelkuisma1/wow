import json
from wow.provenance import load_jsonld
from wow.provenance import rdfclass
from pathlib import Path
from importlib import import_module
import time
import uuid

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
    inputs = wf.inputs(subpropertyof=prov.used, many=True)
    state = wf.hasTaskState()

@rdfclass(wf, subclassof=[prov.Activity])
class WorkerExecution:
    worker_id = wf.worker_id(identity=True)
    task_executions = wf.task_execution(type_of_value=TaskExecution, many=True)

def tasks_to_outputs(value, outputs):
    # Replace tasks with their outputs
    print(value, '\n!!!rdftype:', value._rdftype)
    if isinstance(value, Task):
        return outputs[value.identity]

    # TODO: Does not support recursive visits
    return value

class Runner:
    def run(self, workflow):
        worker_id = str(uuid.uuid4())
        # Temporarily store outputs of tasks here
        outputs = {}
        executions = []
        for task in workflow.topological_order:
            start_time = time.time()
            print(task.identity)
            print(dir(task))
            print(task.target)
            print(task.arguments)
            func = import_target(task.target)
            kwargs = {argument.argument: tasks_to_outputs(argument.value, outputs) for argument in task.arguments}
            output = func(**kwargs)
            end_time = time.time()
            # Store outputs
            outputs[task.identity] = output

            te = TaskExecution(task=task,
                               output=output,
                               start_time=start_time,
                               end_time=end_time,
                               inputs=task.arguments,
                               state='done') # TODO: ENUM
            executions.append(te)
        return WorkerExecution(worker_id=worker_id, task_executions=executions)

def execute_workflow(jsonfile: str, resultfile: str):
    dct = json.loads(Path(jsonfile).read_text())
    workflow = load_jsonld(dct)
    print(workflow)

    runner = Runner()
    worker_execution = runner.run(workflow)
    Path(resultfile).write_text(json.dumps(worker_execution.to_jsonld(), indent=4))

