# Minimal Workflow Demonstrator with Full Provenance

## Reproducibility (deliverable)

There is a Dockerfile with associated make file. Do `sudo make build` to build the Docker. Then `sudo make run` to start the docker, and `sudo make shell` to attach and observe its content. The outputs will be at `/work/outputs` folder after `sudo make run` is executed.

For manual use, do `pip install -e wow` to install the python package at `wow/`. Then run the demo with
`python scripts/run_workflow.py` to produce the `workflow.jsonld` (deliverable) and `workflow_results.jsonld` (deliverable)'.

## Introduction

The `wow/provenance.py` provides Pythonic dataclass like wrappers to allow jsonld metadata output. It was the hardest part of this assignment, but it was necessary as explicitly writing jsonld without formal machinery is tedious and error prone.

Using that we can easily make a workflow definition datastructures (`wow/workflow_definition.py`),
and define our workflow (`wow/demo_workflow.py`).

We finally create a simple workflow executor at (`wow/workflow_execution.py`) which also utilizes the rdf framework created. It is just a mockup of a workflow engine, as implementing full workflow-engine is out of scope for this assignment.

## The workflow jsonld (deliverable)

`wow/workflow_definition.py` defines basic datastructures, so we can serialize and deserialize the workflows. The assignment asked for json of the workflow. In this case, since we can serialize and deserialized the workflow definition, we actually use Python to create the workflow object, which is then turned into json.

## Executing the workflow jsonld and provenance metadate (deliverable)

In `scripts/run_workflow.py` we run generate the json (previous section) and also run it by loading it explicitly from jsonld file. The runner is a simple, but focusses on provenance and giving PROV fields where applicable as metadata. The results of the run are again stored as completely serializable/deserialisable jsonld file (`workflow_results.json`). 

## Units (deliverable)

I focussed to get the units correctly to metadata, so no sanity checking is going on.
Units are represented explicitly via qudt namespace.

```
                        "wf:measuredVoltage": {
                            "@type": "qudt:QuantityValue",
                            "qudt:numericValue": 3.36,
                            "qudt:unit": "http://qudt.org/vocab/unit/V"
                        },
```

## Failure handling (deliverable)

The executor catches exceptions raised by individual task functions and records
the task execution state (either `done`, `failed`, or `cancelled` (if depending on `failed` task).
This way the metadata can always be returned, even some tasks will fail.

## Thought process

Looking at the initial scaffolding, I find it too error prone to work directly with dictionaries (and also I was not that familiar with JSON-LD format). So I made a decision, that in the long run it will be better, if I learn JSON-LD from bottom up with its associated ontologies. Also, working with purely dictionaries is tedious, so I wanted to make the serialization and deserialization to work fully via JSON-LD utilizing modern python standard. This also allowed me to learn what JSON-LD is about as I had to implement many small details and think about the datastructures.
To that end, I created wow/provenance.py which has a parametrized class decorator which generalizes dataclasses to resource description framework.

This was initially hard work (and should be consolidated if this structure would be used in the future). However, it familiarized me a bit to JSON-LD and ontologies, and I was able to write
`workflow_definition.py` which defines crucial datatypes to satisfy the first requirement: To have a serializable workflow. It is very intuitive definition, and only about 50 lines of code and fully serializes and deserializes to/from valid JSON-LD. This satisfied the first deliverable: yaml or json input for the workflow. To that end, there is `wow/demo_workflow.py` which writes the json (due to serialization and deserialization, it works both ways).

To meet another deliverable, workflow execution, I created `wow/workflow_execution.py`. It also defines its own rdftypes so that the provenance data from the execution can be stored. The dockerfile executes this, and the output can be found at /work/outputs folder.

TODO: Software information
TODO: Interoperability discussion

## LLM Use

I chatted with ChatGPT about JSON-LD and ontologies and validated my ideas of decorators in intermediate stages. All edits and code was written by me. On two occasions, I asked codex to find a bug to speed up debugging. I would normally use more LLM, but since this is very first exploration phase of writing this kind of workflow, it was better for the learning process not to use direct LLM coding -- It would have written structures I would not have understood.
