import json
from wow.provenance import rdfclass, Namespace, load_jsonld

wf = Namespace('http://workflowofworkflows.example.com/workflow#', 'wf')

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
                yield from visit(deps)
                yield task
                seen.add(task.identity)

        return list(visit(self.tasks))

