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
    
  def __repr__(self):
    return f"Pooler(inbox: {len(self.inbox)}, tasks: {len(self.running_tasks)}, pool size: {self.pool_size})"
  
  def put(self, work_order):
    assert isinstance(work_order, WorkOrder)
    assert not work_order.has_been_run
    print(f"putting a job. I am {self!r}")
    self.inbox.append(work_order)
    
  async def do_some_work(self):
    if len(self.running_tasks) == 0:
      if len(self.inbox) == 0:
        print("there's no work available, even in the inbox. returning...")
        return
      else:
        while len(self.inbox) > 0 and len(self.running_tasks) < self.pool_size:
          newThing = asyncio.create_task(self.inbox[0].run())
          self.running_tasks.append(newThing)
          del self.inbox[0]
        assert len(self.running_tasks) > 0
    assert len(self.running_tasks) > 0
    print(f"do_some_work: running task info: {[item.done() for item in self.running_tasks]}")
    done, pending = await asyncio.wait(self.running_tasks,  return_when=asyncio.FIRST_COMPLETED)
    # print(f"do_some_work: done types: {[type(item) for item in done]}, pending types: {[type(item) for item in pending]}")
    oldLen = len(self.running_tasks)
    self.running_tasks = list(item for item in self.running_tasks if not item.done())
    print(f"running tasks list len decreased by {oldLen - len(self.running_tasks)}")
    print("do_some_work: finished.")




if __name__ == "__main__": # if this file is not being imported as a module right now:
  import itertools
  
  async def waiting_function(seconds):
    print(f"starting to wait {seconds:.3f} seconds")
    await asyncio.sleep(seconds)
    print(f"done waiting {seconds:.3f} seconds")

  async def testPooler():
    delay = 2.0
    pooler = Pooler(3)
    for i in range(24):
      delay += 0.01
      pooler.put(WorkOrder(waiting_function, [delay], dict()))
    print("="*60)
    for i in range(24):
      await pooler.do_some_work()
      print("pooler is done doing some work.")
    print("done with testPooler, except for final sleep.")
    await asyncio.sleep(20)
    print("done sleeping. done with testPooler.")
      

  asyncio.run(testPooler())
  print("done with event loop.")