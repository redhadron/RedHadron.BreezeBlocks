
# builtin:
# import math


# project:
from Vectors import int_vec_add

# pip:
import pygame
from PIL import Image



WINDOW_HAZE_COLOR = (63, 63, 63)


def pil_image_to_surface(pil_image):
  assert isinstance(pil_image, Image.Image)
  return pygame.image.fromstring(pil_image.tobytes(), pil_image.size, pil_image.mode)
  
def surface_to_pil_image(surface):
  assert isinstance(surface, pygame.Surface)
  return Image.frombytes("RGB", surface.get_size(), pygame.image.tostring(surface, "RGB", False))

class PaddingDescription:
  def __init__(self, *, top=None, right=None, bottom=None, left=None, all_sides=None):
    if all_sides is not None:
      assert top is None and right is None and bottom is None and left is None
      top, right, bottom, left = (all_sides,)*4
    assert all(isinstance(item, int) and item >= 0 for item in (top, right, bottom, left))
    self.top, self.right, self.bottom, self.left = top, right, bottom, left

def join_surfaces_vertically(surfaces, background_color, padding=PaddingDescription(all_sides=0)):
  
  assert all(isinstance(item, pygame.Surface) for item in surfaces), surfaces
  width = max(surf.get_width() for surf in surfaces) + padding.left + padding.right
  height = sum(surf.get_height() for surf in surfaces) + padding.top + padding.bottom
  newSurf = pygame.Surface((width, height))
  newSurf.fill(background_color)
  y = padding.top
  for surf in surfaces:
    newSurf.blit(surf, (padding.left, y))
    y += surf.get_height()
  assert y + padding.bottom == newSurf.get_height()
  return newSurf
  
def make_externally_outlined_copy(input_surface: pygame.Surface, thickness: int, color: tuple[int]) -> pygame.Surface:
  # TODO use this in tooltip generation for interactive atlas prompt
  assert isinstance(input_surface, pygame.Surface), input_surface
  assert isinstance(thickness, int)
  outputSurface = pygame.Surface(int_vec_add(input_surface.get_size(), (thickness*2,thickness*2)))
  outputSurface.fill(color)
  outputSurface.blit(input_surface, (thickness,thickness))
  return outputSurface

"""
# this doesn't seem to work at all.
def make_copy_with_shadow(input_surface, thickness, color):
  outputSurf = pygame.Surface(size=int_vec_add(input_surface.get_size(), (thickness*2,)*2), flags=pygame.SRCALPHA)
  w, h = outputSurf.get_size()
  for y in range(h):
    for x in range(w):
      distFromEdge = min(min(y, h-y-1), min(x,w-x-1))
      
      if distFromEdge < thickness:
        shadowDistProportion = float(distFromEdge+1)/float(thickness)
        assert 0 <= shadowDistProportion <= 1
        colorHere = color + (round(64*shadowDistProportion),)
      else:
        pygameColorHere = input_surface.get_at((x-thickness,y-thickness))
        colorHere = (pygameColorHere.r, pygameColorHere.g, pygameColorHere.b, 255)
      assert len(colorHere) == 4
      outputSurf.set_at((x,y), colorHere)
  return outputSurf
"""
  
def apply_haze(surface: pygame.Surface) -> None:  
  for y in range(surface.get_size()[1]):
    for x in range(surface.get_size()[0]):
      if (x+y)%2:
        surface.set_at((x,y), WINDOW_HAZE_COLOR)