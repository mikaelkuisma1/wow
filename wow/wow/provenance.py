from dataclasses import dataclass


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
        return self._prefix + ':' or self.iri


@dataclass(frozen=True)
class Term:
    namespace: Namespace
    name: str

    @property
    def iri(self):
        return self.namespace.iri + self.name

    def __call__(self, obj: Term, identity=False):
        return PredicateObjectTuple(self, obj, identity=identity)

    def __repr__(self):
        return self.namespace.prefix + self.name


@dataclass(frozen=True)
class PredicateObjectTuple:
    predicate: Term
    obj: Term
    identity: bool = False

    def __repr__(self):
        return f'pred:{self.predicate} obj:{self.obj} {"is @id" if self.identity else ""}'


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
            assert isinstance(value, PredicateObjectTuple), (name, type(value))
            if value.identity:
                assert identity is None
                identity = name
            fields[name] = value

        # Only add new fields after we have pruned users
        cls._fields = fields
        cls._rdftype = namespace(cls.__name__) if _type is None else _type
        cls._identity = identity

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

        def to_jsonld(self):
            dct = {}
            if self._identity is not None:
                dct.update({'@id': getattr(self, self._identity)})
            dct.update({name: getattr(self, name) for name in self._fields})

            return dct
        cls.to_jsonld = to_jsonld

        return cls

    return wrapper


if __name__ == '__main__':
    wf = Namespace('workflowofworkflows.example.com/workflow#', 'wf')
    print(wf)
    print(wf.task)
    print(wf.dependsOn(wf.task))
    print(type(wf.dependsOn(wf.task)))

    # No type, implies the type is taken from class name
    @rdfclass(wf)
    class Workflow:
        name = wf.hasProperty(wf.name, identity=True)

    print(Workflow)
    workflow = Workflow(name='WorkflowOfWorkflowDemo')
    print(workflow)
    print(workflow.to_jsonld())
