import json
from pathlib import Path

from wow.provenance import load_jsonld, time
from wow.workflow_definition import TaskArgument
from wow.workflow_execution import (
    TaskExecution,
    WorkerExecution,
    create_software_agent,
    import_target,
)


def main():
    # This simulates a federated node.
    # - We are a separate process
    # - We fully have serialized all inputs to text
    # - We import the target function
    # - We will fully serialize all outputs to text
    payload = json.loads(Path('input.jsonld').read_text())
    func = import_target(payload['target'])
    task = load_jsonld(payload['task'])
    inputs = [
        TaskArgument(
            argument=item['argument'],
            value=load_jsonld(item['value']),
        )
        for item in payload['arguments']
    ]
    kwargs = {argument.argument: argument.value for argument in inputs}

    start_time = time()
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

    task_execution = TaskExecution(
        task=task,
        output=output,
        start_time=start_time,
        end_time=end_time,
        inputs=task.arguments,
        state=state,
        error=error,
    )
    worker_execution = WorkerExecution(
        worker_id=f'remote-{task.location}',
        software=create_software_agent(),
        task_executions=[task_execution],
    )
    Path('output.jsonld').write_text(
        json.dumps(worker_execution.to_jsonld(), indent=4)
    )
    print(f'Wrote remote output for {task.name} to output.jsonld', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
