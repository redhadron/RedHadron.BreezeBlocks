import asyncio
import time
import sys

"""
def LOG(*args, **kwargs):
  print(*args, **kwargs)
"""
def delete_object_from_list(input_list, value):
  for i, item in enumerate(input_list):
    if item is value:
      del input_list[i]
      return
  raise ValueError(f"the value {value} was not present in {input_list}.") #  dir of value is {dir(value)}")


class WorkOrder:
  def __init__(self, main_function, args, kwargs):
    assert hasattr(main_function, "__call__")
    assert isinstance(args, list) and isinstance(kwargs, dict)
    self.main_function = main_function
    self.args = args
    self.kwargs = kwargs
    self.has_been_run = False
    
  def run(self):
    print("WorkOrder.run called")
    assert not self.has_been_run
    result = self.main_function(*self.args, **self.kwargs)
    self.has_been_run = True
    print("WorkOrder.run finishing up. This doesn't mean that the main_function has been run because it is async.")
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
    print(f"putting a job. I am {self!r}")
    self.inbox.append(work_order)

  def is_working(self):
    return self._working
    
  async def do_some_work(self):
    if len(self.running_tasks) == 0:
      if len(self.inbox) > 0:
        print("there are no running tasks, but there are some in the inbox. pulling now...")
        self.pull_from_inbox()
      else:
        print("do_some_work: there's no work to do, even in the inbox! returning...")
        return
    print(f"it's time to wait for a task to finish. The tasks are {self.running_tasks}")
    copyOfRunningTasks = tuple(self.running_tasks)
    print(f"copyOfRunningTasks is {copyOfRunningTasks}")
    done, pending = await asyncio.wait(self.running_tasks, return_when=asyncio.FIRST_COMPLETED)
    print(f"{done=} {pending=}")
    print("done waiting for a task to finish.")
    for item in done:
      delete_object_from_list(self.running_tasks, item)
      """
      oldLen = len(self.running_tasks)
      try:
        self.running_tasks.remove(item)
      except ValueError:
        print(f"value error, could not remove {item} from {self.running_tasks}")
        sys.exit()
      assert len(self.running_tasks) < oldLen
    """
      assert item in copyOfRunningTasks
      assert item not in self.running_tasks
    print("done with assertions.")
    
  def pull_from_inbox(self):
    print("creating a new task")
    newestTask = asyncio.create_task(self.inbox[0].run())
    del self.inbox[0]
    self.running_tasks.append(newestTask)
    print(f"after adding it to running_tasks, now I am {self!r}")

  async def work(self):
    assert not self._working
    print("work is starting")
    self._working = True
    # assert len(se)
    print("waiting until work orders are available...")
    while len(self.inbox) == 0: # and len(self.running_tasks) == 0:
      print(f"inbox is empty. I am {self!r}")
      await asyncio.sleep(0.25)
    print("work orders are available now!")
    while True:
      while len(self.running_tasks) < self.pool_size and len(self.inbox) > 0:
        self.pull_from_inbox()
      if len(self.running_tasks) > 0:
        print("time to call do_some_work.")
        await self.do_some_work()
        print("done calling doing_some_work.")
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
    delay = 2.0
    pooler = Pooler(3)
    poolerWorkTask = asyncio.create_task(pooler.work())
    print("done creating pooler work task")
    for i in range(8):
      # await asyncio.sleep(0.25)
      time.sleep(0.5) # I need to come up with a design that works despite having non-async workload in this main loop
      delay += 0.01
      pooler.put(WorkOrder(waiting_function, [delay], dict()))
    for i in range(8):
      await pooler.do_some_work()
    print("done with testPooler, except for final sleep.")
    await asyncio.sleep(20)
    print("done sleeping. done with testPooler.")
      

  asyncio.run(testPooler())
  print("done with event loop.")