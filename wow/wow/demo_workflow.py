from wow.provenance import Namespace, rdfclass, load_jsonld
from wow.workflow_definition import Workflow, Task
import json
import random

wow = Namespace('http://workflowofworkflows.example.com/workflow_of_workflows_demo#', 'wf')
qudt = Namespace('http://qudt.org/schema/qudt/', 'qudt')

KELVIN = 'http://qudt.org/vocab/unit/K'
VOLT = 'http://qudt.org/vocab/unit/V'
RANDOM_SEED = 20260612


@rdfclass(qudt)
class QuantityValue:
    value = qudt.numericValue()
    unit = qudt.unit()


def kelvin(value):
    return QuantityValue(value=value, unit=KELVIN)


def volt(value):
    return QuantityValue(value=value, unit=VOLT)


@rdfclass(wow)
class SimulationInputs:
    composition = wow.composition()
    temperature = wow.temperature(type_of_value=QuantityValue)


@rdfclass(wow)
class SimulationOutput:
    predicted_voltage = wow.predictedVoltage(type_of_value=QuantityValue)
    uncertainty = wow.uncertainty(type_of_value=QuantityValue)

@rdfclass(wow)
class ExperimentOutput:
    status = wow.experimentStatus()
    measured_voltage = wow.measuredVoltage(type_of_value=QuantityValue)
    uncertainty = wow.uncertainty(type_of_value=QuantityValue)
    reason = wow.reason()


def simulation_node(inputs: SimulationInputs) -> SimulationOutput:
    composition = inputs.composition
    temp = inputs.temperature.value
    
    # Mock deterministic-ish property model
    base = 3.45 if "Li" in composition else 2.5
    rng = random.Random(f'{RANDOM_SEED}:simulation:{composition}:{temp}')
    predicted = base - 0.0002 * (temp - 298) + rng.uniform(-0.03, 0.03)
    return SimulationOutput(predicted_voltage=volt(round(predicted, 3)),
                            uncertainty=volt(0.08))

def experiment_node(sim_result):
    if sim_result.predicted_voltage.value < 3.0:
        return ExperimentOutput(status="skipped", reason="prediction below threshold")

    # Mock latency and measurement noise for a remote SDL
    import time
    time.sleep(0.2)
    rng = random.Random(
        f'{RANDOM_SEED}:experiment:{sim_result.predicted_voltage.value}'
    )
    measured = sim_result.predicted_voltage.value + rng.uniform(-0.12, 0.12)
    return ExperimentOutput(status="completed",
                            measured_voltage=volt(round(measured, 3)),
                            uncertainty=volt(0.05))


def decision_node(sim_result, exp_result):
    if exp_result.status != "completed":
        return {"recommendation": "explore", "rationale": "experiment unavailable or skipped"}
    delta = abs(sim_result.predicted_voltage.value - exp_result.measured_voltage.value)
    if delta < 0.02:
        return {"recommendation": "exploit", "rationale": "simulation and experiment agree within tolerance"}
    return {"recommendation": "explore", "rationale": "model/experiment discrepancy suggests uncertainty"}

def write_workflow_json(filename: str):
    simulation_inputs = SimulationInputs(composition='LiFePO4', temperature=kelvin(300))
    task1 = Task.create('simulate_voltage',
                        simulation_node,
                        location='partner_A_hpc_or_cloud',
                        inputs=simulation_inputs)
    task2 = Task.create('remote_measurement',
                        experiment_node,
                        location='partner_B_remote_sdl',
                        sim_result=task1)
    task3 = Task.create('choose_next_experiment',
                        decision_node,
                        location='campaign_coordinator',
                        sim_result=task1,
                        exp_result=task2)

    workflow = Workflow(name='WorkflowOfWorkflowDemo',
                        description="Simple workflow example",
                        tasks=[task1, task2, task3])

    s = json.dumps(workflow.to_jsonld(), indent=4)
    from pathlib import Path
    Path(filename).write_text(s)
    print(f'Wrote workflow description to {filename}', flush=True)
    
    dct = json.loads(s)
    lworkflow = load_jsonld(dct)
    s2 = json.dumps(lworkflow.to_jsonld(), indent=4)
    assert s == s2  # Reserialization of loaded should be the same

if __name__ == "__main__":
    create_workflow_json()
