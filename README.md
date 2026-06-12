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

## Software metadata (deliverable)

A mock up software agent metadata was generated, and it is later referenced in nodes where applicable.

```
        {
            "@type": "prov:SoftwareAgent",
            "@id": "wow-demo-software",
            "wf:software_id": "wow-demo-software",
            "wf:softwareName": "Minimal Workflow-of-Workflows demonstrator",
            "wf:softwareVersion": "0.1"
        },
```

It is defined using the home made rdfclass-framework

```
@rdfclass(wf, _type=prov.SoftwareAgent)
class SoftwareAgent:
    software_id = wf.software_id(identity=True)
    name = wf.softwareName()
    version = wf.softwareVersion()
```

What is missing from this demo is full ttl/owl files to declare relationships of `wf.softwareName` to corresponding prov ones.

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

## Interoperability (deliverable)

We have created a generic representation of workflow (still incomplete, but suits well with this low effort assignment), where conversion to jsonld and back to Python structures is possible. We have thus demonstrated that we can convert from generic jsonld to our structures. I would argue that the current workflow representation can serve as intermediate representation (IR) (up to its incompleteness), and it acts as an "abstract syntax tree" (AST) which then can easily transcribed to other workflow standards. For example, it is completely possible to make taskblaster to generate workflow-classes from this representation and proceed with taskblaster. The Workflow and Task classes can have `to_taskblaster` method. Taskblaster workflows are dynamically generated classes with internal class attributes, and such things can easily be created dynamically. I have such work ongoing, where taskblaster workflows would be serialized (from code to json, and from json back to established new Python type). 

## Future improvements

One should separate BoundWorkflow (with inputs given) and UnboundWorkflow (generic definition). And same for tasks. Due to lack of time and to limit the scope it did not do this abstraction. But I have worked with this absraction in taskblaster and it would be reasonably easy to do. It would be interesting to try if taskblaster can be made to export jsonld provenance.

The mocked nodes are not really federated. A future improvement would be to launch a deamon to monitor federated remote tasks, and provide a command line interface. This is however also beyond the scope of this assignment.

## Thought process

Looking at the initial scaffolding, I find it too error prone to work directly with dictionaries (and also I was not that familiar with JSON-LD format). So I made a decision, that in the long run it will be better, if I learn JSON-LD from bottom up with its associated ontologies. Also, working with purely dictionaries is tedious, so I wanted to make the serialization and deserialization to work fully via JSON-LD utilizing modern python standard. This also allowed me to learn what JSON-LD is about as I had to implement many small details and think about the datastructures.
To that end, I created wow/provenance.py which has a parametrized class decorator which generalizes dataclasses to resource description framework.

This was initially hard work (and should be consolidated if this structure would be used in the future). However, it familiarized me a bit to JSON-LD and ontologies, and I was able to write
`workflow_definition.py` which defines crucial datatypes to satisfy the first requirement: To have a serializable workflow. It is very intuitive definition, and only about 50 lines of code and fully serializes and deserializes to/from valid JSON-LD. This satisfied the first deliverable: yaml or json input for the workflow. To that end, there is `wow/demo_workflow.py` which writes the json (due to serialization and deserialization, it works both ways).

What is still missing is ontologies, even we declare our own types and provide full serialization and deserialization to jsonld, the ontologies are not 100% defined. One should consolidate the definitions, and allow to define subPropertyOf and similar types at the rdfclass-level. Also, it should be possible to provide directly ontology triples from the type definitions alone, which would greatly improve the current implementation. However, this is beyond the scope of this assignment.

## LLM Use

I chatted with ChatGPT about JSON-LD and ontologies and validated my ideas of decorators in intermediate stages. All edits and code was written by me, unless explicitly mentioned in what follows: On two occasions, I asked codex to find a bug to speed up debugging. I would normally use more LLM, but since this is very first exploration phase of writing this kind of workflow, it was better for the learning process not to use direct LLM coding -- It would have written structures I would not have understood. SoftwareAgent and Error handling were AI-assisted (the only direct edits via codex).
