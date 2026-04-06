
import operator



def int_vec_parallel_operation(a, b, operation, packager):
  assert len(a) == len(b)
  assert isinstance(a, tuple) and isinstance(b, tuple)
  assert all(isinstance(val, int) for val in a)
  assert all(isinstance(val, int) for val in b)
  return packager(operation(aVal, bVal) for aVal,bVal in zip(a,b))
int_vec_add = lambda a, b: int_vec_parallel_operation(a, b, operator.add, tuple)
int_vec_parallel_multiply = lambda a, b: int_vec_parallel_operation(a, b, operator.mul, tuple)
# int_vec_parallel_compare_less = lambda a, b: int_vec_parallel_operation(a, b, operator.lt, tuple)
int_vec_all_components_are_less = lambda a, b: int_vec_parallel_operation(a, b, operator.lt, all)
# int_vec_parallel_compare_lessequal = lambda a, b: int_vec_parallel_operation(a, b, operator.le, tuple)
int_vec_all_components_are_lessequal = lambda a, b: int_vec_parallel_operation(a, b, operator.le, all)
assert int_vec_parallel_multiply((2,3),(5,7)) == (10,21)
  
def int_vec_scale_by(vec, scale):
  assert isinstance(vec, tuple)
  assert all(isinstance(component, int) for component in vec)
  assert isinstance(scale, int)
  return tuple(component*scale for component in vec)