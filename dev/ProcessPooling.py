import asyncio


class WorkOrder:
  def __init__(self, main_function, args, kwargs):
    assert hasattr(main_function, "__call__")
    assert isinstance(args, list) and isinstance(kwargs, dict)
    self.main_function = main_function
    self.args = args
    self.kwargs = kwargs
    self.has_been_run = False
  def run(self):
    assert not self.has_been_run
    result = self.main_function(*self.args, **self.kwargs)
    self.has_been_run = True
    return result

class Pooler:
  def __init__(self, pool_size):
    self.pool_size = pool_size
    self.inbox = []
    self.running_tasks = []
    self._working = False
    
  def __repr__(self):
    return f"Pooler(inbox: {len(self.inbox)}, tasks: {len(self.running_tasks)}, working: {self.is_working()})"
  
  def put(self, work_order):
    assert isinstance(work_order, WorkOrder)
    assert not work_order.has_been_run
    print(f"putting a job. I am {self!r}")
    self.inbox.append(work_order)

  def is_working(self):
    return self._working

  async def work(self):
    assert not self._working
    print("work is starting")
    self._working = True
    # assert len(se)
    print("waiting until coroutines are available...")
    while len(self.inbox) == 0:
      await asyncio.sleep(0.05)
    print("coroutines are available now!")
    while True:
      while len(self.running_tasks) < self.pool_size and len(self.inbox) > 0:
        newestTask = asyncio.create_task(self.inbox[0].run())
        del self.inbox[0]
        self.running_tasks.append(newestTask)
      if len(self.running_tasks) > 0:
        done, pending = await asyncio.wait(self.running_tasks, return_when=asyncio.FIRST_COMPLETED)
        print(f"{done=} {pending=}")
        for item in done:
          # delete_object_from_list(self.running_tasks, item)
          self.running_tasks.remove(item)
      else:
        break
    assert self._working
    print("work is ending")
    self._working = False
    return
    




if __name__ == "__main__": # if this file is not being imported as a module right now:
  import itertools
  
  async def waiting_function(seconds):
    print(f"starting to wait {seconds:.3f} seconds")
    await asyncio.sleep(seconds)
    print(f"done waiting {seconds:.3f} seconds")

  async def testPooler():
    delay = 5.0
    pooler = Pooler(3)
    poolerWorkTask = asyncio.create_task(pooler.work())
    print("done creating pooler work task")
    for i in itertools.count():
      await asyncio.sleep(0.25)
      delay += 0.01
      pooler.put(WorkOrder(waiting_function, [delay], dict()))

  asyncio.run(testPooler())