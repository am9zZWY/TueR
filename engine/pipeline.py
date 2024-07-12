from concurrent.futures import ThreadPoolExecutor, wait


class PipelineElement:
    def __init__(self, name):
        self.name = name
        self.next = []
        self.executor = None
        print(f"Initialized {self.name}")

    def add_executor(self, executor):
        self.executor = executor

    def process(self, *args):
        raise NotImplementedError

    def add_next(self, next_element):
        self.next.append(next_element)

    def call_next(self, *args):
        futures = []
        for element in self.next:
            print(f"{self.name} -> {element.name}")
            future = element.executor.submit(element.process, *args)
            futures.append(future)
        wait(futures)  # Wait for all futures to complete
