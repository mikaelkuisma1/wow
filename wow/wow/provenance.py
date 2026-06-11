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

    def __call__(self, obj: Term):
        return PredicateObjectTuple(self, obj)

    def __repr__(self):
        return self.namespace.prefix + self.name 

@dataclass(frozen=True)
class PredicateObjectTuple:
    predicate: Term
    obj: Term

    def __repr__(self):
        return f'pred:{self.predicate} obj:{self.obj}'

def rdfclass(namespace, /, *, _type=None):
    """Class decorator for dataclass like structure, but for with rdf


    """
    
    def wrapper(cls):
        print('wrapping', cls)
        cls._rdftype = namespace(cls.__name__) if _type is None else _type

        def __repr__(self):
            return f'{self._rdftype!r}()'
        cls.__repr__ = __repr__
        return cls
   
    return wrapper

if __name__ == "__main__":
    wf = Namespace('workflowofworkflows.example.com/workflow#', 'wf')
    print(wf)
    print(wf.task)
    print(wf.dependsOn(wf.task))

    # No type, implies the type is taken from class name
    @rdfclass(wf)
    class Workflow:
        name = wf.hasProperty(wf.name)

    print(Workflow)
    print(Workflow())
    #class WorkflowDescription:

