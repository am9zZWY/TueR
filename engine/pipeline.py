import threading


class PipelineElement:
    def __init__(self, name):
        self.name = name
        self.next = []
        self.executor = None
        self.tasks = []
        self.shutdown_flag = threading.Event()
        print(f"Initialized {self.name}")

    def add_executor(self, executor):
        self.executor = executor

    def process(self, *args):
        raise NotImplementedError

    def save_state(self):
        pass

    def add_next(self, next_element):
        self.next.append(next_element)

    def call_next(self, *args):
        for element in self.next:
            self.tasks.append(self.executor.submit(element.process, *args))

    def shutdown(self):
        self.shutdown_flag.set()

    def is_shutdown(self):
        return self.shutdown_flag.is_set()
