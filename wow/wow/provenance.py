from dataclasses import dataclass

class Namespace:
    def __init__(self, iri: str, prefix: str | None = None):
        self.iri = iri
        self.prefix = prefix
    
    def __getattr__(self, attr: str):
        return Term(self, attr)

    def __repr__(self):
        return self.iri

@dataclass(frozen=True)
class Term:
    namespace: Namespace
    name: str

    @property
    def iri(self):
        return self.namespace.iri + self.name


def rdfclass(*, type=None):
    """Class decorator for dataclass like structure, but for with rdf


    """
    def wrapper(cls):
        print('wrapping', cls)
        return cls

if __name__ == "__main__":
    wow = Namespace('workflowofworkflows.example.com', 'wowdemo')
    print(wow)
