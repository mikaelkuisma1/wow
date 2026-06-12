from wow.provenance import JSONLDContext, load_jsonld, rdfclass, time
from pathlib import Path
from importlib import import_module
from datetime import datetime, UTC
import os
import re
import subprocess
import sys
import tempfile
import time as walltime
import uuid
import json

from wow import __version__
from wow.workflow_definition import wf, Task, TaskArgument, Namespace

prov = Namespace("http://www.w3.org/ns/prov#", prefix="prov")

def import_target(target: str):
    module_name, func_name = target.rsplit(".", 1)
    module = import_module(module_name)
    return getattr(module, func_name)

@rdfclass(wf, subclassof=[prov.Activity])
class TaskExecution:
    task = wf.executed_task(type_of_value=Task)
    output = prov.generated()
    start_time = prov.startedAtTime()
    end_time = prov.endedAtTime()
    inputs = prov.used(many=True)
    state = wf.hasTaskState()
    error = wf.errorMessage()

@rdfclass(wf, _type=prov.SoftwareAgent)
class SoftwareAgent:
    software_id = wf.software_id(identity=True)
    name = wf.softwareName()
    version = wf.softwareVersion()
    container = wf.containerImage()

@rdfclass(wf, subclassof=[prov.Activity])
class WorkerExecution:
    worker_id = wf.worker_id(identity=True)
    software = prov.wasAssociatedWith(type_of_value=SoftwareAgent)
    task_executions = wf.task_execution(type_of_value=TaskExecution, many=True)

def create_software_agent():
    return SoftwareAgent(
        software_id='wow-demo-software',
        name='Minimal Workflow-of-Workflows demonstrator',
        version=__version__,
        container='python:3.13-slim',
    )

def serialize_jsonld_value(value):
    if hasattr(value, 'to_jsonld'):
        return value.to_jsonld(JSONLDContext())
    if isinstance(value, list):
        return [serialize_jsonld_value(item) for item in value]
    if isinstance(value, dict):
        return {key: serialize_jsonld_value(item) for key, item in value.items()}
    return value

def tasks_to_outputs(value, outputs):
    # Replace tasks with their outputs
    if isinstance(value, Task):
        return outputs[value.identity]

    # TODO: Does not support recursive visits
    return value

class Runner:
    def log(self, message):
        print(message, flush=True)

    @property
    def time():
        t = time.time()
        timestamp = datetime.fromtimestamp(t, UTC).isoformat()

    def local_task_execution(self, task, inputs):
        start_time = time()
        func = import_target(task.target)
        kwargs = {argument.argument: argument.value for argument in inputs}

        try:
            output = func(**kwargs)
        except Exception as err:
            output = None
            state = 'failed'
            error = f'{err.__class__.__name__}: {err}'
        else:
            state = 'done'
            error = None
        end_time = time()

        return TaskExecution(task=task,
                             output=output,
                             start_time=start_time,
                             end_time=end_time,
                             inputs=inputs,
                             state=state,
                             error=error)

    def remote_task_execution(self, task, inputs):
        location = task.location
        workdir = Path(tempfile.mkdtemp(prefix=f'{location}_'))
        payload = {
            'target': task.target,
            'task': task.to_jsonld(),
            'arguments': [
                {
                    'argument': argument.argument,
                    'value': serialize_jsonld_value(argument.value),
                }
                for argument in inputs
            ],
        }
        (workdir / 'input.jsonld').write_text(json.dumps(payload, indent=4))
        self.log(f'Wrote serialized inputs for {task.name} to {workdir}')

        env = os.environ.copy()
        process = subprocess.Popen(
            [sys.executable, '-m', 'wow.mock_federated_runner'],
            cwd=workdir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        while process.poll() is None:
            walltime.sleep(0.05)
        stdout, stderr = process.communicate()
        if stdout.strip():
            self.log(stdout.strip())

        output_file = workdir / 'output.jsonld'
        if process.returncode != 0 or not output_file.exists():
            error = stderr.strip() or f'remote process exited with {process.returncode}'
            return TaskExecution(
                task=task,
                output=None,
                start_time=time(),
                end_time=time(),
                inputs=task.arguments,
                state='failed',
                error=error,
            )

        import_target(task.target)
        worker_execution = load_jsonld(json.loads(output_file.read_text()))
        return worker_execution.task_executions[0]

    def run_task(self, task, inputs):
        if task.location:
            self.log(f'Starting task {task.name} at {task.location}')
            return self.remote_task_execution(task, inputs)

        self.log(f'Starting task {task.name}')
        return self.local_task_execution(task, inputs)

    def run(self, workflow):
        worker_id = str(uuid.uuid4())
        tasks = workflow.topological_order
        self.log(f'Running workflow {workflow.name} with {len(tasks)} tasks')
        # Temporarily store outputs of tasks here
        outputs = {}
        executions = []
        for task in tasks:
            self.log(f'Fetching task {task.name}')
            if any(execution.state != 'done' for execution in executions):
                start_time = time()
                end_time = time()
                te = TaskExecution(
                    task=task,
                    output=None,
                    start_time=start_time,
                    end_time=end_time,
                    inputs=task.arguments,
                    state='cancelled',
                    error='previous task did not complete successfully',
                )
                executions.append(te)
                self.log(f'Task {task.name} cancelled: {te.error}')
                continue

            inputs = [
                TaskArgument(
                    argument=argument.argument,
                    value=tasks_to_outputs(argument.value, outputs),
                )
                for argument in task.arguments
            ]
            te = self.run_task(task, inputs)
            if te.state == 'done':
                # Store outputs only for successfully completed tasks.
                outputs[task.identity] = te.output
                self.log(f'Task {task.name} done')
            else:
                self.log(f'Task {task.name} {te.state}: {te.error}')
            executions.append(te)
        return WorkerExecution(
            worker_id=worker_id,
            software=create_software_agent(),
            task_executions=executions,
        )

def execute_workflow(jsonfile: str, resultfile: str):
    dct = json.loads(Path(jsonfile).read_text())
    workflow = load_jsonld(dct)

    runner = Runner()
    worker_execution = runner.run(workflow)
    Path(resultfile).write_text(json.dumps(worker_execution.to_jsonld(), indent=4))
    print(f'Wrote workflow results to {resultfile}', flush=True)
