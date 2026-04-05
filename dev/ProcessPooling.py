import asyncio


def LOG(*args, **kwargs):
  print(*args, **kwargs)


class WorkOrder:
  def __init__(self, main_function, args, kwargs):
    assert hasattr(main_function, "__call__")
    assert isinstance(args, list) and isinstance(kwargs, dict)
    self.main_function = main_function
    self.args = args
    self.kwargs = kwargs
    self.has_been_run = False
  def run(self):
    LOG("a work order is running")
    assert not self.has_been_run
    result = self.main_function(*self.args, **self.kwargs)
    self.has_been_run = True
    return result

class Pooler:
  def __init__(self, pool_size):
    assert pool_size > 1
    self.pool_size = pool_size
    self.inbox = []
    self.running_tasks = []
    self._working = False
    
  def __repr__(self):
    return f"Pooler(inbox: {len(self.inbox)}, tasks: {len(self.running_tasks)}, pool size: {self.pool_size}, working: {self.is_working()})"
  
  def put(self, work_order):
    assert isinstance(work_order, WorkOrder)
    assert not work_order.has_been_run
    LOG(f"putting a job. I am {self!r}")
    self.inbox.append(work_order)

  def is_working(self):
    return self._working

  async def work(self):
    assert not self._working
    LOG("work is starting")
    self._working = True
    # assert len(se)
    LOG("waiting until work orders are available...")
    while len(self.inbox) == 0:
      LOG("no work orders are available.")
      await asyncio.sleep(0.05)
    LOG("work orders are available now!")
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
    LOG("work is ending")
    self._working = False
    return
    




if __name__ == "__main__": # if this file is not being imported as a module right now:
  import itertools
  
  async def waiting_function(seconds):
    LOG(f"starting to wait {seconds:.3f} seconds")
    await asyncio.sleep(seconds)
    LOG(f"done waiting {seconds:.3f} seconds")

  async def testPooler():
    delay = 5.0
    pooler = Pooler(3)
    poolerWorkTask = asyncio.create_task(pooler.work())
    LOG("done creating pooler work task")
    for i in itertools.count():
      await asyncio.sleep(0.25)
      # time.sleep(0.5)
      delay += 0.01
      pooler.put(WorkOrder(waiting_function, [delay], dict()))

  asyncio.run(testPooler())
  # testPooler()