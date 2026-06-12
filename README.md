# Minimal Workflow Demonstrator with Full Provenance

## Reproducibility (deliverable)

There is a Dockerfile with an associated Makefile. Do `sudo make build` to build the Docker image. Then `sudo make run` to start the container, and `sudo make shell` to attach and inspect its contents. The outputs will be in the `/work/outputs` folder after `sudo make run` is executed.

For manual use, do `pip install -e wow` to install the Python package at `wow/`. Then run the demo with
`python scripts/run_workflow.py` to produce `workflow.jsonld` and `workflow_results.jsonld`.

## Introduction

The `wow/provenance.py` module provides Pythonic dataclass-like wrappers for JSON-LD metadata output. It was the hardest part of this assignment, but it was necessary because explicitly writing JSON-LD without formal machinery is tedious and error prone.

Using that, we can easily make workflow definition data structures (`wow/workflow_definition.py`),
and define our workflow (`wow/demo_workflow.py`).

We finally create a simple workflow executor (`wow/workflow_execution.py`) which also uses the RDF framework created here. It is just a mock-up of a workflow engine, as implementing a full workflow engine is out of scope for this assignment.

## The workflow JSON-LD (deliverable)

`wow/workflow_definition.py` defines basic data structures, so we can serialize and deserialize workflows. The assignment asked for JSON describing the workflow. In this case, since we can serialize and deserialize the workflow definition, we use Python to create the workflow object, which is then turned into JSON-LD.

## Executing the workflow JSON-LD and provenance metadata (deliverable)

In `scripts/run_workflow.py` we generate the JSON-LD workflow description and also execute it by loading it explicitly from the JSON-LD file. The runner is simple, but focuses on provenance and uses PROV fields where applicable. The results of the run are stored as a completely serializable/deserializable JSON-LD file (`workflow_results.jsonld`). 

## Software metadata (deliverable)

Minimal mock software-agent metadata is generated and later referenced where applicable.

```
        {
            "@type": "prov:SoftwareAgent",
            "@id": "wow-demo-software",
            "wf:software_id": "wow-demo-software",
            "wf:softwareName": "Minimal Workflow-of-Workflows demonstrator",
            "wf:softwareVersion": "0.1"
        },
```

It is defined using the home-made `rdfclass` framework:

```
@rdfclass(wf, _type=prov.SoftwareAgent)
class SoftwareAgent:
    software_id = wf.software_id(identity=True)
    name = wf.softwareName()
    version = wf.softwareVersion()
```

What is missing from this demo is full TTL/OWL files declaring relationships from terms such as `wf.softwareName` to corresponding PROV terms.

## Units (deliverable)

I focused on getting the units correctly into the metadata, so no unit sanity checking is performed.
Units are represented explicitly via the QUDT namespace.

```
                        "wf:measuredVoltage": {
                            "@type": "qudt:QuantityValue",
                            "qudt:numericValue": 3.36,
                            "qudt:unit": "http://qudt.org/vocab/unit/V"
                        },
```

## Failure handling (deliverable)

The executor catches exceptions raised by individual task functions and records
the task execution state: either `done`, `failed`, or `cancelled` if the task depends on a failed task.
This way the metadata can always be returned, even if some tasks fail.

## Interoperability (deliverable)

We have created a generic representation of a workflow. It is still incomplete, but fits the scope of this minimal demonstrator assignment, and conversion to JSON-LD and back to Python structures is possible. We have thus demonstrated that we can convert from generic JSON-LD to our structures. I would argue that the current workflow representation can serve as an intermediate representation (IR), up to its incompleteness, and it acts as an "abstract syntax tree" (AST) which can then be transcribed to other workflow standards. For example, it is completely possible to make Taskblaster generate workflow classes from this representation and proceed with Taskblaster. The `Workflow` and `Task` classes could have a `to_taskblaster` method. Taskblaster workflows are dynamically generated classes with internal class attributes, and such things can be created dynamically. I have related work ongoing where Taskblaster workflows would be serialized from code to JSON, and from JSON back to an established new Python type.

## Future improvements

One should separate `BoundWorkflow` (with inputs given) and `UnboundWorkflow` (generic definition). The same applies to tasks. Due to lack of time, and to limit the scope, I did not implement this abstraction. I have worked with this abstraction in Taskblaster, and it would be reasonably easy to do. It would be interesting to try whether Taskblaster can be made to export JSON-LD provenance.

The mocked nodes are not really federated. A future improvement would be to launch a daemon to monitor federated remote tasks and provide a command-line interface. This is also beyond the scope of this assignment.

## Thought process

Looking at the initial scaffolding, I found it too error prone to work directly with dictionaries, and I was also not that familiar with the JSON-LD format. So I made the decision that, in the long run, it would be better if I learned JSON-LD from the bottom up with its associated ontologies. Also, working purely with dictionaries is tedious, so I wanted the serialization and deserialization to work fully via JSON-LD while using modern Python standards. This also allowed me to learn what JSON-LD is about, as I had to implement many small details and think about the data structures.
To that end, I created `wow/provenance.py` which has a parameterized class decorator that generalizes dataclasses to the Resource Description Framework.

This was initially hard work (and should be consolidated if this structure would be used in the future). However, it familiarized me a bit to JSON-LD and ontologies, and I was able to write
`workflow_definition.py` which defines crucial data types to satisfy the first requirement: to have a serializable workflow. It is a very intuitive definition, only about 50 lines of code, and it fully serializes and deserializes to/from valid JSON-LD. This satisfied the first deliverable: YAML or JSON input for the workflow. To that end, there is `wow/demo_workflow.py` which writes the JSON-LD; due to serialization and deserialization, it works both ways.

What is still missing is ontologies. Even though we declare our own types and provide full serialization and deserialization to JSON-LD, the ontologies are not 100% defined. One should consolidate the definitions and allow `subPropertyOf` and similar relationships to be defined at the `rdfclass` level. Also, it should be possible to produce ontology triples directly from the type definitions alone, which would greatly improve the current implementation. However, this is beyond the scope of this assignment.

## LLM Use

I chatted with ChatGPT about JSON-LD and ontologies and validated my ideas of decorators in intermediate stages. All edits and code were written by me, unless explicitly mentioned in what follows: On two occasions, I asked Codex to find a bug to speed up debugging. I would normally use more LLM assistance, but since this is the very first exploration phase of writing this kind of workflow, it was better for the learning process not to use direct LLM coding -- it would have written structures I would not have understood. `SoftwareAgent` and error handling were AI-assisted, the only direct edits via Codex.
