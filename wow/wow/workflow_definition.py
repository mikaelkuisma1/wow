import json
from wow.provenance import rdfclass, Namespace, load_jsonld

wf = Namespace('workflowofworkflows.example.com/workflow#', 'wf')


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
        arguments = [TaskArgument(argument=argument, value=value) for argument, value in kwargs.items()]
        return cls(name=name, target=target, arguments=arguments)


@rdfclass(wf)
class Workflow:
    name = wf.name(identity=True)
    description = wf.description()
    tasks = wf.workflow_tasks(type_of_value=Task, many=True)


def create_workflow_json():
    task1 = Task.create('mytask1', 'run_experiment', material='BaTiO3', temperature=128)
    task2 = Task.create('mytask2', 'run_simulation', material='BaTiO3', temperature=128)
    task3 = Task.create('mytask3', 'decision_node', experiment=task1, simulation=task2)


    workflow = Workflow(name='WorkflowOfWorkflowDemo',
                        description="Simple workflow example",
                        tasks=[task1, task2, task3])

    s = json.dumps(workflow.to_jsonld(), indent=4)
    from pathlib import Path
    Path('workflow.json').write_text(s)
    
    dct = json.loads(s)
    lworkflow = load_jsonld(dct)
    s2 = json.dumps(lworkflow.to_jsonld(), indent=4)
    assert s == s2  # Reserialization of loaded should be the same

if __name__ == "__main__":
    create_workflow_json()
