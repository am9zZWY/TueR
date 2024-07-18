import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor


class PipelineElement:
    def __init__(self, name):
        self.name = name
        self.next = []
        self.executor = None
        self.task_queue = asyncio.Queue()
        self.shutdown_flag = threading.Event()
        self.loop = asyncio.get_event_loop()
        print(f"Initialized {self.name}")

    def add_executor(self, executor):
        self.executor = executor
        self.loop.create_task(self.worker_loop())

    async def process(self, *args):
        raise NotImplementedError

    def save_state(self):
        pass

    def add_next(self, next_element):
        self.next.append(next_element)

    def add_task(self, *args):
        self.loop.create_task(self.task_queue.put(args))

    async def worker_loop(self):
        while not self.is_shutdown():
            try:
                args = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                if asyncio.iscoroutinefunction(self.process):
                    await self.process(*args)
                else:
                    await self.loop.run_in_executor(self.executor, self.process, *args)
                self.task_queue.task_done()
            except asyncio.TimeoutError:
                continue  # No tasks available, continue checking

    async def propagate_to_next(self, *args):
        for element in self.next:
            element.add_task(*args)

    def shutdown(self):
        self.shutdown_flag.set()

    def is_shutdown(self):
        return self.shutdown_flag.is_set()
