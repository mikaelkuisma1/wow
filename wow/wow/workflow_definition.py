import json
from wow.provenance import rdfclass, Namespace, load_jsonld

wf = Namespace('htto://workflowofworkflows.example.com/workflow#', 'wf')


@rdfclass(wf)
class TaskArgument:
    argument = wf.argument_name()
    value = wf.argument_value()


@rdfclass(wf)
class Task:
    name = wf.name(identity=True)
    target = wf.task_target()
    arguments = wf.task_arguments(type_of_value=TaskArgument, many=True)

    @classmethod
    def create(cls, name, target, **kwargs):
        if not isinstance(target, str):
            target = target.__module__ + "." + target.__qualname__
        arguments = [TaskArgument(argument=argument, value=value) for argument, value in kwargs.items()]
        return cls(name=name, target=target, arguments=arguments)

    @property
    def dependencies(self):
        deps = []
        for arg in self.arguments:
            assert isinstance(arg, TaskArgument)
            if isinstance(arg.value, Task):
                deps.append(arg.value)
        return deps

@rdfclass(wf)
class Workflow:
    name = wf.name(identity=True)
    description = wf.description()
    tasks = wf.workflow_tasks(type_of_value=Task, many=True)

    @property
    def topological_order(self):
        seen = set()
        def visit(tasks):
            for task in tasks:
                if task.identity in seen:
                    continue
                deps = task.dependencies
                visit(deps)
                yield task
                seen.add(task.identity)

        return list(visit(self.tasks))

wow = Namespace('htto://workflowofworkflows.example.com/workflow_of_workflows_demo#', 'wf')

@rdfclass(wow)
class SimulationInputs:
    composition = wow.composition()
    temperature_K = wow.temperature_K()


@rdfclass(wow)
class SimulationOutput:
    predicted_voltage_V = wow.predicted_voltage_V()
    uncertainty_V = wow.uncertainty_V()


def simulation_node(inputs: SimulationInputs) -> SimulationOutput:
    composition = inputs.composition
    temp = inputs.temperature_K
    
    # Mock deterministic-ish property model
    base = 3.45 if "Li" in composition else 2.5
    predicted = base - 0.0002 * (temp - 298) + random.uniform(-0.03, 0.03)
    return SimulationOutput(predicted_voltage_V=round(predicted, 3), uncertainty_V=0.08)

def experiment_node(sim_result):
    if sim_result["predicted_voltage_V"] < 3.0:
        return {"status": "skipped", "reason": "prediction below threshold"}
    # Mock latency and measurement noise for a remote SDL
    time.sleep(0.2)
    measured = sim_result["predicted_voltage_V"] + random.uniform(-0.12, 0.12)
    return {"status": "completed", "measured_voltage_V": round(measured, 3), "uncertainty_V": 0.05}


def decision_node(sim_result, exp_result):
    if exp_result.get("status") != "completed":
        return {"recommendation": "explore", "rationale": "experiment unavailable or skipped"}
    delta = abs(sim_result["predicted_voltage_V"] - exp_result["measured_voltage_V"])
    if delta < 0.12:
        return {"recommendation": "exploit", "rationale": "simulation and experiment agree within tolerance"}
    return {"recommendation": "explore", "rationale": "model/experiment discrepancy suggests uncertainty"}

def write_workflow_json(filename: str):
    simulation_inputs = SimulationInputs(composition='asd', temperature_K=200)
    task1 = Task.create('mytask1', simulation_node, inputs=simulation_inputs)
    task2 = Task.create('mytask2', experiment_node, material='BaTiO3', temperature=128)
    task3 = Task.create('mytask3', decision_node, experiment=task1, simulation=task2)

    workflow = Workflow(name='WorkflowOfWorkflowDemo',
                        description="Simple workflow example",
                        tasks=[task1, task2, task3])

    s = json.dumps(workflow.to_jsonld(), indent=4)
    from pathlib import Path
    Path(filename).write_text(s)
    
    dct = json.loads(s)
    lworkflow = load_jsonld(dct)
    s2 = json.dumps(lworkflow.to_jsonld(), indent=4)
    assert s == s2  # Reserialization of loaded should be the same

if __name__ == "__main__":
    create_workflow_json()
