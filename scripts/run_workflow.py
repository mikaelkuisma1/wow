from wow.demo_workflow import write_workflow_json
from wow.workflow_execution import execute_workflow

write_workflow_json('workflow.jsonld')
execute_workflow('workflow.jsonld')
