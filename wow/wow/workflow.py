import taskblaster as tb

def computational_screening(a):
    return a

def experimental_step(a):
    return a

def decision_step(a, b):
    return a == b

@tb.workflow
class Step:
    a = tb.var()

    @tb.task
    def computational_screening(self):
        return tb.node(computational_screening, a=self.a)

    @tb.task
    def experimental_step(self):
        return tb.node(experimental_step, a=self.computational_screening)

    @tb.task
    def decision_step(self):
        return tb.node(decision_step, a=self.experimental_step, b=self.computational_screening)

def workflow(runner):
    rn = runner.with_subdirectory('workflow1')
    rn.run_workflow(Step(a='asd'))
