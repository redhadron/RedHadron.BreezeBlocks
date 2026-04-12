
# builtin:
import shelve
from collections import Counter
import statistics
# import os

# project:
from Hytale import HYTALE_ASSETS_PATH, SEP, HYTALE_BLOCKTEXTURES_PATH, HYTALE_BLOCKTEXTURE_FILE_NAMES

# pip:
from PIL import Image

COLORS_SHELF_PATH = SEP.join([".", "data", "colors.shelf"])




"""
TODO:
  replace counter mode with statistics.mode
  add tests
"""

def setitem_if_valid(dictionary, key, value, test_function):
  if test_function(value):
    dictionary[key] = value
    return True
  return False

def get_mode_from_counter(counter):
  best2 = counter.most_common(2)
  if len(counter) == 1 or best2[0][1] > best2[1][1]:
    return best2[0][0]
  else:
    return None
    
    
def distance(vec0, vec1, *, p):
  assert isinstance(vec0, tuple) and isinstance(vec1, tuple) and len(vec0) == len(vec1)
  assert p >= 1
  return sum(abs(item[0]-item[1])**p for item in zip(vec0, vec1))**(1/p)
assert distance((1,1), (5,6), p=1) == 9
assert distance((0,3), (4,0), p=2) == 5

def geometric_median(input_list, snap, *, p):
  raise NotImplementedError()
  
def median_by_pair_elimination(input_list, p):
  raise NotImplementedError()

def median_by_convex_hull_elimination(input_list):
  # https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.ConvexHull.html
  raise NotImplementedError()
  
#def median_rounded_up(input_list):
#  return int(math.ceiling(statistics.median(input_list)))
  
def channelwise_median(input_list, snap, *, p):
  resultF = tuple(map(statistics.median, zip(*input_list)))
  assert len(resultF) == 3
  if snap:
    nearest = min(input_list, key=lambda point: distance(point, resultF, p=p))
    return nearest
  else:
    raise NotImplementedError("rounding without snapping??")


class TransparencyError(Exception):
  pass

def opaque_pixel_list(raw_pixels):
  result = []
  for rawPixel in raw_pixels:
    assert isinstance(rawPixel, tuple), rawPixel
    if len(rawPixel) == 3:
      result.append(rawPixel)
    else:
      assert len(rawPixel) == 4, rawPixel
      if rawPixel[3] == 255:
        result.append(rawPixel[:3])
      else:
        if rawPixel[3] != 0:
          print(f"WARNING: partial transparency not properly supported: {rawPixel}")
          raise TransparencyError()
        # result.append(rawPixel[:3])
  return result



def find_colors():
  with shelve.open(COLORS_SHELF_PATH) as colorsShelf:
    for textureFileName in HYTALE_BLOCKTEXTURE_FILE_NAMES:
      
      with Image.open(HYTALE_BLOCKTEXTURES_PATH + SEP + textureFileName) as textureOnDisk:
        texture = textureOnDisk.convert("RGBA")
        
      textureStats = dict()
      if not texture.getbands() in [("R", "G", "B"), ("R", "G", "B", "A")]:
        colorsShelf[textureFileName] = {"ERROR": f"skipping {textureFileName} because it has the wrong bands {texture.getbands()}"}
        continue
      try:
        pixels = opaque_pixel_list(list(zip(*[texture.getchannel(char).getdata() for char in texture.getbands()])))
      except TransparencyError:
        colorsShelf[textureFileName]= {"ERROR": f"skipping {textureFileName} because of a problem with transparency"}
        continue
      assert all(len(pixel)==3 for pixel in pixels)
      
      isAValidColor = lambda x: x is not None and None not in x and len(x) == 3
      
      if setitem_if_valid(textureStats, "full_pixel_mode", get_mode_from_counter(Counter(pixels)), isAValidColor):
        assert isinstance(textureStats["full_pixel_mode"], tuple) and len(textureStats["full_pixel_mode"]) == 3

      setitem_if_valid(textureStats, "channelwise_mode", tuple(get_mode_from_counter(Counter(pixel[subpixelIndex] for pixel in pixels)) for subpixelIndex in range(3)), isAValidColor)
      
      setitem_if_valid(textureStats, "channelwise_median_snapped_to_input_color", channelwise_median(pixels, snap=True, p=2), isAValidColor)
      
      
      print(f"{textureFileName} -> {textureStats}")
      colorsShelf[textureFileName] = textureStats
      
if __name__ == "__main__":
  find_colors()  
      
