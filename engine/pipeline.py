import asyncio
import logging
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

    async def call_next(self, *args):
        if not self.next:
            print(f"No next elements for {self.name}")
            return  # No next elements to process

        print(f"Processing next elements for {self.name}")
        tasks = []
        for element in self.next:
            if asyncio.iscoroutinefunction(element.process):
                # If the process method is a coroutine, create a task
                task = asyncio.create_task(element.process(*args))
            else:
                # If it's a regular function, run it in the executor
                loop = asyncio.get_running_loop()
                task = loop.run_in_executor(self.executor, element.process, *args)
            tasks.append(task)

        # Wait for all tasks to complete
        await asyncio.gather(*tasks)

    def shutdown(self):
        self.shutdown_flag.set()

    def is_shutdown(self):
        return self.shutdown_flag.is_set()
