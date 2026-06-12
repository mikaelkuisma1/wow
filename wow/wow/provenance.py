from dataclasses import dataclass
import json

declared_rdf_classes = {}

class Namespace:
    def __init__(self, iri: str, prefix: str | None = None):
        self.iri = iri
        self._prefix = prefix

    def __getattr__(self, attr: str):
        return Term(self, attr)

    def __repr__(self):
        return f'Namespace("{self.iri}")'

    def __call__(self, attr: str):
        return getattr(self, attr)

    @property
    def prefix(self):
        return self._prefix or self.iri

    @property
    def context(self):
        return {self.prefix: self.iri}

@dataclass(frozen=True)
class Term:
    namespace: Namespace
    name: str

    @property
    def iri(self):
        return self.namespace.iri + self.name

    @property
    def context(self):
        return self.namespace.context

    def __call__(self, type_of_value=None, identity=False, many=False):
        return Predicate(self, identity=identity, type_of_value=type_of_value, many=many)

    def __repr__(self):
        return self.curie

    @property
    def curie(self):
        # Compact URI Expression
        return self.namespace.prefix + ':' + self.name


@dataclass
class Predicate:
    term: Term
    identity: bool = False
    type_of_value: Type | None = None
    many: bool = False

@dataclass(frozen=True)
class PredicateObjectTuple:
    predicate: Term
    obj: Term
    identity: bool = False

    def __repr__(self):
        return f'pred:{self.predicate} obj:{self.obj} {"is @id" if self.identity else ""}'

class JSONLDContext:
    def __init__(self):
        self.context = {} 
        self.graph = []

    def add(self, dct):
        assert '@id' in dct
        self.context.update(dct.pop('@context', {}))
        self.graph.append(dct)

    @property
    def dct(self):
        if len(self.graph) > 1:
            return {'@context': self.context,
                    '@graph': self.graph}
        return {'@context': self.context, **self.graph[0]}

    @property
    def asstr(self):
        return json.dumps(self.dct)

def rdfclass(namespace, /, *, _type=None):
    """Class decorator for dataclass like structure, but for with rdf"""

    def wrapper(cls):
        print('wrapping', cls)

        # Iterate over all fields defined in our custom rdfclass
        fields = {}
        identity = None
        for name, value in cls.__dict__.items():
            if name.startswith('__'):
                continue
            if isinstance(value, classmethod):
                continue
            assert isinstance(value, Predicate), (name, type(value))
            if value.identity:
                assert identity is None
                identity = name
            fields[name] = value

        # Only add new fields after we have pruned users
        cls._fields = fields
        cls._rdftype = namespace(cls.__name__) if _type is None else _type
        
        assert cls._rdftype.curie not in declared_rdf_classes
        declared_rdf_classes[cls._rdftype.curie] = cls 

        cls._identity = identity

        # Create a property calleod identity
        def identity_property(self):
            return getattr(self, self._identity)

        cls.identity = property(identity_property)

        def __repr__(self):
            field_strs = []
            dct = {name: getattr(self, name) for name in self._fields}
            return f'{self._rdftype!r}({dct!r})'

        cls.__repr__ = __repr__

        # Create a custom init, only allow kwargs
        def __init__(self, **kwargs):
            assert self._fields.keys() == kwargs.keys(), (
                self._fields.keys(),
                kwargs.keys(),
            )
            self.__dict__.update(kwargs)

        cls.__init__ = __init__

        def to_jsonld(self, ctx: JSONLDContext | None = None):
            ctx_was_none = ctx is None
            ctx = ctx or JSONLDContext()
            
            dct = {'@context': self._rdftype.context,
                   '@type': self._rdftype.curie}
            if self._identity is not None:
                dct.update({'@id': getattr(self, self._identity)})
            
            def dump_and_ref(value):
                if hasattr(value, 'to_jsonld'):
                    # We dump it first to the graph, and only reference it here by id
                    value = value.to_jsonld(ctx)
                    if '@id' in value:
                        value = {'@id': value['@id']}
                    else:
                        # Omit context as we are dumping directly
                        value = {k:v for k, v in value.items() if k is not '@context'}
                return value
            
            for name, predicate in self._fields.items():
                value = getattr(self, name)
                # If the value needs be serialized as jsonld...
                if isinstance(value, list):
                    assert predicate.many
                    value = [dump_and_ref(v) for v in value]
                else:
                    value = dump_and_ref(value)

                dct.update({predicate.term.curie: value})
            
            if '@id' in dct:
                ctx.add(dct)

            # Return the entire graph only at the final call
            if ctx_was_none:
                # ctx_was_none indicates user is calling us to serialize
                # we need to have root @id node of us
                dct = ctx.dct
                dct['@id'] = self.identity
                return dct
            return dct

        cls.to_jsonld = to_jsonld

        return cls

    return wrapper

def load_jsonld_type(dct, ctx):
    context = dct.pop('@context', {})
    
    # We need to load a type for now
    rdftypename = dct['@type']
    assert rdftypename in declared_rdf_classes

    kwargs = {}
    rdftype = declared_rdf_classes[rdftypename]
    for name, predicate in rdftype._fields.items():
        key = predicate.term.curie
        # name is the python name of the field
        # key is the curie we used to store this
        # so here is the critical conversion of changing the keys from curies to
        # kwargs going to "dataclass constructor"
        kwargs[name] = load_jsonld(dct[key], ctx)
 
    instance = rdftype(**kwargs)
    
    if '@id' in dct:
        ctx.add(instance)

    return instance

class LoadJSONLDContext:
    def __init__(self):
        self.ids = {}

    def add(self, obj):
        self.ids[obj.identity] = obj

    def by_id(self, _id):
        return self.ids[_id]

def load_jsonld(dct, ctx=None):
    ctx = ctx or LoadJSONLDContext()

    # This is not a full jsonld parser for arbitrary triples
    # however, it will work for the requirements of this demo
    if isinstance(dct, (str, int, float)):
        return dct
    if isinstance(dct, list):
        return [load_jsonld(item, ctx) for item in dct]
    assert isinstance(dct, dict)

    if '@type' in dct:
        return load_jsonld_type(dct, ctx)
    if '@graph' in dct:
        graph = dct['@graph']
        types = [load_jsonld_type(item, ctx) for item in graph]
        return ctx.by_id(dct['@id'])

    if '@id' in dct:
        # Pure reference
        return ctx.by_id(dct['@id'])

    print(dct)
    print(type(dct))
    asd

if __name__ == '__main__':
    wf = Namespace('workflowofworkflows.example.com/workflow#', 'wf')
    print(wf)
    print(wf.task)
    print(wf.dependsOn(wf.task))
    print(type(wf.dependsOn(wf.task)))

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

    task1 = Task.create('mytask1', 'run_experiment', material='BaTiO3', temperature=128)
    task2 = Task.create('mytask2', 'run_simulation', material='BaTiO3', temperature=128)
    task3 = Task.create('mytask3', 'decision_node', experiment=task1, simulation=task2)

    print(task3)
    s = json.dumps(task3.to_jsonld())
    dct = json.loads(s)
    assert '@id' in dct
    ltask = load_jsonld(dct)
    print(type(ltask.arguments[0]))
    
    # No type, implies the type is taken from class name
    @rdfclass(wf)
    class Workflow:
        name = wf.name(identity=True)
        description = wf.description()
        tasks = wf.workflow_tasks(type_of_value=Task, many=True)
    print(Workflow)
    workflow = Workflow(name='WorkflowOfWorkflowDemo',
                        description="Simple workflow example",
                        tasks=[task1, task2, task3])
    print(workflow)
    print(workflow.to_jsonld())

    s = json.dumps(workflow.to_jsonld(), indent=4)
    from pathlib import Path
    Path('workflow.json').write_text(s)
    dct = json.loads(s)
    print('Deserializing', dct)
    lworkflow = load_jsonld(dct)
    print(lworkflow)
    s2 = json.dumps(lworkflow.to_jsonld(), indent=4)
    assert s == s2  # Reserialization of loaded should be the same
