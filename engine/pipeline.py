class PipelineElement:
    def __init__(self, name):
        self.name = name
        self.next = None

    def set_next(self, next_element):
        self.next = next_element

    def process(self, data):
        raise NotImplementedError
