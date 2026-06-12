from wow.provenance import Namespace, rdfclass, load_jsonld
from wow.workflow_definition import Workflow, Task
import json
import random

wow = Namespace('htto://workflowofworkflows.example.com/workflow_of_workflows_demo#', 'wf')

@rdfclass(wow)
class SimulationInputs:
    composition = wow.composition()
    temperature_K = wow.temperature_K()


@rdfclass(wow)
class SimulationOutput:
    predicted_voltage_V = wow.predicted_voltage_V()
    uncertainty_V = wow.uncertainty_V()

@rdfclass(wow)
class ExperimentOutput:
    status = wow.experimentStatus()
    measured_voltage_V = wow.measuredVoltage()
    uncertainty_V = wow.uncertainty_V()
    reason = wow.reason()


def simulation_node(inputs: SimulationInputs) -> SimulationOutput:
    composition = inputs.composition
    temp = inputs.temperature_K
    
    # Mock deterministic-ish property model
    base = 3.45 if "Li" in composition else 2.5
    predicted = base - 0.0002 * (temp - 298) + random.uniform(-0.03, 0.03)
    return SimulationOutput(predicted_voltage_V=round(predicted, 3), uncertainty_V=0.08)

def experiment_node(sim_result):
    if sim_result.predicted_voltage_V < 3.0:
        return ExperimentOutput(status="skipped", reason="prediction below threshold")

    # Mock latency and measurement noise for a remote SDL
    import time
    time.sleep(0.2)
    measured = sim_result.predicted_voltage_V + random.uniform(-0.12, 0.12)
    return ExperimentOutput(status="completed", measured_voltage_V= round(measured, 3), uncertainty_V= 0.05)


def decision_node(sim_result, exp_result):
    if exp_result.status != "completed":
        return {"recommendation": "explore", "rationale": "experiment unavailable or skipped"}
    delta = abs(sim_result.predicted_voltage_V - exp_result.measured_voltage_V)
    if delta < 0.02:
        return {"recommendation": "exploit", "rationale": "simulation and experiment agree within tolerance"}
    return {"recommendation": "explore", "rationale": "model/experiment discrepancy suggests uncertainty"}

def write_workflow_json(filename: str):
    simulation_inputs = SimulationInputs(composition='LiFePO4', temperature_K=300)
    task1 = Task.create('mytask1', simulation_node, inputs=simulation_inputs)
    task2 = Task.create('mytask2', experiment_node, sim_result=task1)
    task3 = Task.create('mytask3', decision_node, sim_result=task1, exp_result=task2)

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
