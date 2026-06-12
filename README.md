# Minimal Workflow Demonstrator with Taskblaster

## Thought process

Looking at the initial scaffolding, I find it too error prone to work directly with dictionaries (and also I was not that familiar with JSON-LD format). So I made a decision, that in the long run it will be better, if I learn JSON-LD from bottom up with its associated ontologies. Also, working with purely dictionaries is tedious, so I wanted to make the serialization and deserialization to work fully via JSON-LD utilizing modern python standard. This also allowed me to learn what JSON-LD is about as I had to implement many small details and think about the datastructures.
To that end, I created wow/provenance.py which has a parametrized class decorator which generalizes dataclasses to resource description framework.

This was initially hard work (and should be consolidated if this structure would be used in the future). However, it familiarized me a bit to JSON-LD and ontologies, and I was able to write
`workflow_definition.py` which defines crucial datatypes to satisfy the first requirement: To have a serializable workflow. It is very intuitive definition, and only about 50 lines of code and fully serializes and deserializes to/from valid JSON-LD. This satisfied the first deliverable: yaml or json input for the workflow. To that end, there is `wow/demo_workflow.py` which writes the json (due to serialization and deserialization, it works both ways).

To meet another deliverable, workflow execution, I created `wow/workflow_execution.py`. It also defines its own rdftypes so that the provenance data from the execution can be stored. The dockerfile executes this, and the output can be found at /work/outputs folder.

TODO: Software information
TODO: Units
TODO: Interoperability discussion
TODO: Failure handling
TODO: Reproducibility

## LLM Use

I chatted with ChatGPT about JSON-LD and ontologies and validated my ideas of decorators in intermediate stages. All edits and code was written by me. On two occasions, I asked codex to find a bug to speed up debugging. I would normally use more LLM, but since this is very first exploration phase of writing this kind of workflow, it was better for the learning process not to use direct LLM coding -- It would have written structures I would not have understood.
