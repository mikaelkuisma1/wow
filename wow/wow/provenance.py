from dataclasses import dataclass

class Namespace:
    def __init__(self, iri: str, prefix: str | None = None):
        self.iri = iri
        self._prefix = prefix
    
    def __getattr__(self, attr: str):
        return Term(self, attr)

    def __repr__(self):
        return f'Namespace("{self.iri}")'

    @property
    def prefix(self):
        return self._prefix or self.iri

@dataclass(frozen=True)
class Term:
    namespace: Namespace
    name: str

    @property
    def iri(self):
        return self.namespace.iri + ':' + self.name

    def __call__(self, obj: Term):
        return PredicateObjectTuple(self, obj)

    def __repr__(self):
        return self.namespace.prefix + ':' + self.name 

@dataclass(frozen=True)
class PredicateObjectTuple:
    predicate: Term
    obj: Term

    def __repr__(self):
        return f'pred:{self.predicate} obj:{self.obj}'

def rdfclass(*, type=None):
    """Class decorator for dataclass like structure, but for with rdf


    """
    def wrapper(cls):
        print('wrapping', cls)
        return cls

if __name__ == "__main__":
    wow = Namespace('workflowofworkflows.example.com', 'wowdemo')
    print(wow)
    print(wow.task)
    print(wow.dependsOn(wow.task))
    #@rdfclass(type=wow._
    #class WorkflowDescription:

