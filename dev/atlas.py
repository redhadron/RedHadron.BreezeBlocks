
# builtin:
import enum
import os
import json
import ast
import tkinter
import time
import itertools
import operator
import functools


# pip:
from bidict import bidict
from PIL import Image, ImageTk, ImageDraw # the k in ImageTk is lowercase.
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "True"
import pygame
import argparse
import pydantic

# project:
from Affixes import remove_suffix, remove_prefix, bisect_at_infix
from Utilities import is_valid_int_pair_tuple, nand, at_most_one
from Vectors import int_vec_add, int_vec_subtract, int_vec_divide_by_scalar_exact, int_vec_parallel_multiply, int_vec_all_components_are_less, int_vec_all_components_are_lessequal, int_vec_scale_by
from Graphics import pil_image_to_surface, surface_to_pil_image, PaddingDescription, join_surfaces_vertically, make_externally_outlined_copy, apply_haze # make_copy_with_shadow

"""
todo:
  -allow multiple values to be specified as blank, so that a solid-color tile in any of those colors will be ignored. Introduce checkerboard background pattern.
  -make a better atlas_config.json creation process, eliminate default values for atlas size and tile size.
  -2d range.
  -add check that atlas image file and atlas image size specified by config are the same.
  -search "TODO" and "NotImplementedError" in this file.
"""

SEP = os.sep
NEWLINE = "\n" # because you can't use a backslash inside the expression of an f-string.
TILE_FOLDER_PATH = SEP.join([".","..","Common","Blocks","Breeze"])
FPS = 30.0
ATLAS_IMAGE_NAME = "atlas_image.png"
ATLAS_IMAGE_PATH = TILE_FOLDER_PATH + SEP + ATLAS_IMAGE_NAME
_ATLAS_CONFIG_NAME = "atlas_config.json"
ATLAS_CONFIG_PATH = TILE_FOLDER_PATH + SEP + _ATLAS_CONFIG_NAME

ATLAS_CONFIG_SORT_KEYS = True
ATLAS_CONFIG_INDENT = 4

ATLAS_IMAGE_CREATION_FILL_COLOR = (255, 255, 255)
ATLAS_IMAGE_BLANK_COLOR = (*ATLAS_IMAGE_CREATION_FILL_COLOR, 255)

TILE_PREVIEW_SCALE = 10
PREVIEW_GRID_LINE_COLOR = (127, 127, 127)
HIGHLIGHT_COLOR = (255, 0, 0)
WINDOW_BACKGROUND_COLOR = (31, 31, 31)
WINDOW_TEXT_COLOR = (250, 250, 250)
WINDOW_FAINT_TEXT_COLOR = (127, 127, 127)
WINDOW_BG_STRING = "#cccccc"
class TRANSPORT_DIRECTION(enum.Enum):
  IMPORT = enum.auto()
  EXPORT = enum.auto()
def PARSE_TRANSPORT_DIRECTION(string):
  return {"in": TRANSPORT_DIRECTION.IMPORT, "out": TRANSPORT_DIRECTION.EXPORT}[string]
EXIT_CODES = {"GENERAL_SUCCESS":0, "TILE_PROMPT_EXIT_CHOICE": 2, "PYGAME_QUIT":3, "ATLAS_PROMPT_QUIT_CHOICE":4}







  


def config_file_to_string():
  with open(ATLAS_CONFIG_PATH, "r") as configFile:
    return configFile.read()

class ConfigManager:
  def __init__(self):
    self.coordinates_to_names = None
    self.tile_size = (32, 32)
    self.atlas_size = (6, 12)
  
  def _config_data_to_dict(self):
    return {"coordinates_to_names": self.coordinates_to_names, "tile_size":self.tile_size, "atlas_size":self.atlas_size}
  
  def load(self):
    loadedText = config_file_to_string()
    loadedData = json.loads(loadedText)
    assert self.coordinates_to_names is None, "config data should not be loaded twice!"
    self.coordinates_to_names = bidict()
    for keyString, value in loadedData["coordinates_to_names"].items():
      key = ast.literal_eval(keyString)
      assert is_valid_int_pair_tuple(key)
      assert key not in self.coordinates_to_names
      # only key duplicates are searched for here, because the bidict itself catches value duplicates.
      self.coordinates_to_names[key] = value
    
  def _config_data_to_string(self):
    rawConfigData = self._config_data_to_dict()
    serializableConfigData = dict()
    for cfgKey in rawConfigData.keys():
      if cfgKey == "coordinates_to_names":
        serializableConfigData[cfgKey] = {str(coord): name for coord, name in rawConfigData["coordinates_to_names"].items()}
      else:
        serializableConfigData[cfgKey] = rawConfigData[cfgKey]
    return json.dumps(serializableConfigData, sort_keys=ATLAS_CONFIG_SORT_KEYS, indent=ATLAS_CONFIG_INDENT)

  def save(self):
    textToWrite = self._config_data_to_string()
    with open(ATLAS_CONFIG_PATH, "w") as configFile:
      configFile.write(textToWrite)
    
  def has_changed(self):
    return self._config_data_to_string() != config_file_to_string()
    
  def assert_is_saved_correctly(self):
    if self.has_changed():
      print("config data changed unexpectedly.")
      print("config data:")
      print(self._config_data_to_string())
      print("config file:")
      print(config_file_to_string())
      print("the program will exit.")
      assert False
      
CONFIG = ConfigManager()



def get_atlas_image_size():
  # TODO add builtin check that image is the same size as configured size?
  return int_vec_parallel_multiply(CONFIG.tile_size, CONFIG.atlas_size)

def get_a_free_coordinate():
  for y in range(CONFIG.atlas_size[1]):
    for x in range(CONFIG.atlas_size[0]):
      if (x,y) not in CONFIG.coordinates_to_names:
        return (x,y)
  assert False, "out of room"







# ----- file handling -----

def create_atlas_image():
  if os.path.exists(ATLAS_IMAGE_PATH):
    raise FileExistsError()
  atlasImg = Image.new(mode="RGB", size=get_atlas_image_size(), color=ATLAS_IMAGE_CREATION_FILL_COLOR)
  atlasImg.save(ATLAS_IMAGE_PATH)
  
def delete_atlas_image():
  assert ATLAS_IMAGE_PATH.endswith(".png"), "invalid atlas image path"
  if not os.path.exists(ATLAS_IMAGE_PATH):
    raise FileNotFoundError()
  os.remove(ATLAS_IMAGE_PATH)
  
def create_atlas_config():
  if os.path.exists(ATLAS_CONFIG_PATH):
    raise FileExistsError()
  save_config()
  
def delete_atlas_config():
  assert ATLAS_CONFIG_PATH.endswith(".json"), "invalid atlas config path"
  if not os.path.exists(ATLAS_CONFIG_PATH):
    raise FileNotFoundError()
  os.remove(ATLAS_CONFIG_PATH)
  






# ----- cell math -----

def intersection_coordinate_to_pixel_coordinate(intersection_address):
  return int_vec_parallel_multiply(CONFIG.tile_size, intersection_address)
  
def cell_coordinate_is_in_bounds(coordinate):
  assert is_valid_int_pair_tuple(coordinate)
  return 0 <= coordinate[0] < CONFIG.atlas_size[0] and 0 <= coordinate[1] < CONFIG.atlas_size[1]

def cell_coordinate_to_pillow_rect(coordinate):
  assert is_valid_int_pair_tuple(coordinate)
  x, y = coordinate
  return (*intersection_coordinate_to_pixel_coordinate((x,y)), *intersection_coordinate_to_pixel_coordinate((x+1,y+1)))










# ----- methods for working with tile images -----

def make_tile_preview_image(tile_image: Image.Image) -> Image.Image:
  """
  a tile preview image is a much larger version of a tile image, with a pixel grid drawn over it.
  """
  previewSize = int_vec_scale_by(CONFIG.tile_size, TILE_PREVIEW_SCALE)
  modifiedTileImage = tile_image.resize(size=previewSize, resample=Image.Resampling.NEAREST)
  imageDrawer = ImageDraw.Draw(modifiedTileImage) 
  for y in range(CONFIG.tile_size[1]):
    imageDrawer.line((0,y*TILE_PREVIEW_SCALE,modifiedTileImage.size[0],y*TILE_PREVIEW_SCALE), PREVIEW_GRID_LINE_COLOR)
  for x in range(CONFIG.tile_size[0]):
    imageDrawer.line((x*TILE_PREVIEW_SCALE, 0, x*TILE_PREVIEW_SCALE, modifiedTileImage.size[1]), PREVIEW_GRID_LINE_COLOR)
  return modifiedTileImage
  
def crop_atlas_image_to_tile_image(atlas_image: Image.Image, coordinate) -> Image.Image:
  assert is_valid_int_pair_tuple(coordinate)
  assert isinstance(atlas_image, Image.Image)
  return atlas_image.crop(cell_coordinate_to_pillow_rect(coordinate))
  
def get_preview_pil_image_of_cell(atlas_image: Image.Image, coordinate) -> Image.Image:
  assert is_valid_int_pair_tuple(coordinate)
  assert isinstance(atlas_image, Image.Image)
  return make_tile_preview_image(crop_atlas_image_to_tile_image(atlas_image, coordinate))
  
def get_preview_surface_of_cell(atlas_image: Image.Image, coordinate) -> pygame.Surface:
  assert is_valid_int_pair_tuple(coordinate)
  assert isinstance(atlas_image, Image.Image)
  return pil_image_to_surface(get_preview_pil_image_of_cell(atlas_image, coordinate))

def tile_image_is_blank(tile_image: Image.Image) -> bool:
  assert isinstance(tile_image, Image.Image)
  assert tile_image.size == CONFIG.tile_size
  for pixelY in range(tile_image.size[1]):
    for pixelX in range(tile_image.size[0]):
      if tile_image.getpixel((pixelX,pixelY)) != ATLAS_IMAGE_BLANK_COLOR:
        return False
  return True
  
def find_tile_names():
  return [item for item in os.listdir(TILE_FOLDER_PATH) if item.endswith(".png") and item != ATLAS_IMAGE_NAME]

def tile_name_to_path(tile_name):
  return TILE_FOLDER_PATH + SEP + tile_name
  
  
  
  
# ----- methods to import and export individual tiles -----
  
def import_tile_with_coordinate(destination_atlas_pil_image, cell_coordinate) -> None:
  assert is_valid_int_pair_tuple(cell_coordinate)
  assert isinstance(destination_atlas_pil_image, Image.Image)
  return import_tile_with_name(destination_atlas_pil_image, CONFIG.coordinates_to_names[cell_coordinate])

def import_tile_with_name(destination_atlas_pil_image, tile_name) -> None:
  assert isinstance(tile_name, str)
  assert isinstance(destination_atlas_pil_image, Image.Image)
  assert tile_name in CONFIG.coordinates_to_names.inverse
  tilePath = tile_name_to_path(tile_name)
  if not os.path.exists(tilePath):
    raise FileNotFoundError(f"Tile with path {tilePath} does not exist and cannot be imported at the configured location. import_tile_with_name should only be called for names that are known to exist as files.")
  with Image.open(tilePath) as tileImg:
    if tileImg.size != CONFIG.tile_size:
      print(f"WARNING: Tile with name {tile_name} will not be imported because it is the wrong size: {tileImg.size}")
      return
    destinationCellCoordinate = CONFIG.coordinates_to_names.inverse[tile_name]
    if not int_vec_all_components_are_less(destinationCellCoordinate, CONFIG.atlas_size):
      print(f"WARNING: Tile with name {tile_name} will not be imported to the cell at {destinationCellCoordinate} because it is outside of the atlas according to the atlas config size of {config_data['atlas_size']}.")
      return
    if not int_vec_all_components_are_lessequal(intersection_coordinate_to_pixel_coordinate(int_vec_add(destinationCellCoordinate, (1,1))), destination_atlas_pil_image.size):
      print(f"WARNING: Tile with name {tile_name} will not be imported to the cell at {destinationCellCoordinate} because it would start or extend outside of the atlas image.")
      return
    destination_atlas_pil_image.paste(tileImg, intersection_coordinate_to_pixel_coordinate(destinationCellCoordinate))
    
def export_tile_with_coordinate(atlas_image: Image.Image, coordinate: tuple[int]) -> None:
  assert isinstance(atlas_image, Image.Image)
  assert is_valid_int_pair_tuple(coordinate)
  tileImgPath = tile_name_to_path(CONFIG.coordinates_to_names[coordinate])
  tileImg = crop_atlas_image_to_tile_image(atlas_image, coordinate)
      
  # \/ refuse to overwrite tile of wrong size
  if os.path.exists(tileImgPath):
    with Image.open(tileImgPath) as oldTileImg:
      if oldTileImg.size != tileImg.size:
        raise FileExistsError("the tile will not be overwritten because it is of a different size.")
        
  tileImg.save(tileImgPath)







class TilePromptResponse:
  pass
class TilePromptSubmission(TilePromptResponse):
  def __init__(self, name):
    self.name = name
def TilePromptSkip(TilePromptResponse):
  def __init__(self):
    pass
def TilePromptExit(TilePromptResponse):
  def __init__(self):
    pass
    
def prompt_user_for_tile_name(tile_image, enable_skip_button=True) -> TilePromptResponse:
  assert isinstance(tile_image, Image.Image) # tile_image must be a PIL Image
  window = tkinter.Tk()
  window.configure(bg=WINDOW_BG_STRING)
  topLabel = tkinter.Label(window, text="Give this tile a name")
  topLabel.pack()
  
  tilePreviewImage = make_tile_preview_image(tile_image)
  
  canvas = tkinter.Canvas(window, width=tilePreviewImage.size[0], height=tilePreviewImage.size[1])
  canvas.pack()
  tkinterImage = ImageTk.PhotoImage(image=tilePreviewImage, size=tilePreviewImage.size)
  tkinterImageSprite = canvas.create_image(tilePreviewImage.size[0]//2, tilePreviewImage.size[1]//2, image=tkinterImage) # it doesn't matter if the division is not exact, this is just for preview.
  
  entryStringVar = tkinter.StringVar()
  entry = tkinter.Entry(window, textvariable=entryStringVar)
  entry.focus_set()
  entry.pack()
  
  class PromptResultHolder:
    def __init__(self):
      self.value = None
  promptResultHolder = PromptResultHolder()
  
  def okayCallback(*args, **kwargs):
    entryText = entry.get()
    if not entryText.endswith(".png"):
      print("name must end with .png")
      return
    if not len(remove_suffix(entryText, ".png")) > 0:
      print("name must be longer")
      return
    if entryText.lower() == ATLAS_IMAGE_NAME.lower():
      print("name must not match the name of the atlas image")
      return
    if any(char in "\/\:*?\"<>|" for char in entryText):
      print("name contains invalid character(s)")
      return
    promptResultHolder.value = TilePromptSubmission(entryText)
    window.destroy()
  entry.bind('<Return>', okayCallback)
  okayButton = tkinter.Button(text="OK", command=okayCallback)
  okayButton.bind('<Return>', okayCallback)
  okayButton.pack()
  
  if enable_skip_button:
    def skipCallback(*args, **kwargs):
      promptResultHolder.vale = TilePromptSkip()
      window.destroy()
    skipButton = tkinter.Button(text="Skip", command=skipCallback)
    skipButton.bind('<Return>', skipCallback)
    skipButton.pack()
  
  def exitCallback(*args, **kwargs):
    print("Exit button pressed.")
    promptResultHolder.value = TilePromptExit()
    window.destroy()
  exitButton = tkinter.Button(text="Exit", command=exitCallback)
  exitButton.bind('<Return>', exitCallback)
  exitButton.pack()
  
  window.mainloop()
  
  return promptResultHolder.value





@functools.cache
def GET_DEFAULT_FONT():
  pygame.init()
  return pygame.freetype.SysFont(pygame.freetype.get_default_font(), 18, bold=False)

def scrolling_surface_list_selection_prompt(surfaces: list[pygame.Surface], display_at_once: int = 9) -> int|None:
  assert display_at_once%2 == 1
  assert all(isinstance(item, pygame.Surface) for item in surfaces)
  head = 0
  screen = pygame.display.set_mode((500, 300))
  while True:
    screen.fill(WINDOW_BACKGROUND_COLOR)
    for event in pygame.event.get():
      if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_DOWN:
          head += 1
        if event.key == pygame.K_UP:
          head -= 1
        if event.key == pygame.K_RETURN:
          return head
        if event.key in (pygame.K_ESCAPE, ord("q")):
          return None
    head %= len(surfaces)
    
    topToDisplay = head - (display_at_once//2)
    bottomToDisplay = head + (display_at_once//2)
    
    topToDisplay = max(0, topToDisplay)
    bottomToDisplay = min(len(surfaces)-1, bottomToDisplay)
    
    bottomToDisplay = max(bottomToDisplay, topToDisplay+display_at_once-1)
    topToDisplay = min(topToDisplay, bottomToDisplay-display_at_once+1)
    
    topToDisplay = max(0, topToDisplay)
    bottomToDisplay = min(len(surfaces)-1, bottomToDisplay)
    # TODO make this less stupid /\
    surfaceIndicesToUse = range(topToDisplay, bottomToDisplay+1)
    surfacesToShow = [(make_externally_outlined_copy(surfaces[i], thickness=4, color=HIGHLIGHT_COLOR) if i == head else surfaces[i]) for i in surfaceIndicesToUse]
    screen.blit(join_surfaces_vertically(surfacesToShow, WINDOW_BACKGROUND_COLOR, padding=PaddingDescription(all_sides=6)), (0,0)) # TODO: create blit_centered method and use it to put this scrolling menu in the middle of the window.
    pygame.display.flip()
    time.sleep(1.0/FPS)
  assert False, "unreachable"





class AtlasPromptResponse:
  pass
class AtlasPromptSubmission(AtlasPromptResponse):
  def __init__(self, *, coordinate, event):
    self.coordinate, self.event = coordinate, event
class AtlasPromptExit(AtlasPromptResponse):
  def __init__(self):
    pass

class AtlasPromptDefinition(pydantic.BaseModel):
  tile_preview_image: Image.Image
  pointer_image: None|Image.Image
  tile_preview_top_text: str
  tile_preview_bottom_text: str
  key_descriptions: dict[int, str]
  acceptable_keys: dict[str, list[int]]
  clicks_are_acceptable: bool
  model_config = {"arbitrary_types_allowed": True} # this is required by Pydantic to use arbitrary types such as PIL's Image.Image as a type hint

TOOLTIP_PADDING = PaddingDescription(all_sides=6)

def atlas_interactive_prompt(*, prompt_definition: AtlasPromptDefinition, atlas_image: Image.Image) -> AtlasPromptResponse:
  # this method should never do anything except display a prompt and return the user's choice of action. It should not perform that action.
  assert isinstance(prompt_definition.tile_preview_image, Image.Image)
  assert all(isinstance(item, int) for item in itertools.chain(*prompt_definition.acceptable_keys.values()))
  assert isinstance(atlas_image, Image.Image)
  pygame.init()
  font = GET_DEFAULT_FONT()
  
  atlasSurf = pil_image_to_surface(atlas_image)
  screen = pygame.display.set_mode((max(600,atlasSurf.get_width()+400), max(400, atlasSurf.get_height())))
  pygame.display.set_caption("atlas.py interactive mode")
  tilePreviewSurf = pil_image_to_surface(prompt_definition.tile_preview_image)
  
  while True:
    
    screen.fill(WINDOW_BACKGROUND_COLOR)
    screen.blit(atlasSurf, (0,0))
    tilePreviewTopTextSurf = font.render(text=prompt_definition.tile_preview_top_text, fgcolor=WINDOW_TEXT_COLOR)[0]
    tilePreviewBottomTextSurf = font.render(text=prompt_definition.tile_preview_bottom_text, fgcolor=WINDOW_TEXT_COLOR)[0]
    labeledTilePreviewSurf = join_surfaces_vertically([tilePreviewTopTextSurf, tilePreviewSurf, tilePreviewBottomTextSurf], WINDOW_BACKGROUND_COLOR)
    screen.blit(labeledTilePreviewSurf, (atlasSurf.get_width()+10, 0))
    
    # determine pointer conditions:
    hoveredTileCoord = tuple(pygame.mouse.get_pos()[i]//CONFIG.tile_size[i] for i in (0,1)) # TODO int vec divide
    if not cell_coordinate_is_in_bounds(hoveredTileCoord):
      hoveredTileCoord = None
    hoveredTileName = CONFIG.coordinates_to_names.get(hoveredTileCoord, None)
    
    # rendering that depends on pointer conditions {
    # static instructions:
    font.render_to(screen, text="\n".join(prompt_definition.key_descriptions[keyCode] for keyCode in prompt_definition.acceptable_keys["no_requirements"]), dest=(atlasSurf.get_width()+10, screen.get_height()-30), fgcolor=WINDOW_TEXT_COLOR)
    
    # tooltip:
    if hoveredTileCoord is not None:
      # highlight the cell:
      pygame.draw.lines(screen, HIGHLIGHT_COLOR, True, [intersection_coordinate_to_pixel_coordinate(int_vec_add(hoveredTileCoord, offset)) for offset in [(0,0), (1,0), (1,1), (0,1)]])
      # generate the tooltip:
      hoveredTileDisplayName = CONFIG.coordinates_to_names.get(hoveredTileCoord, default="empty")
      _keycodesAvailableNowGen = (itertools.chain([] if hoveredTileCoord is None else itertools.chain(prompt_definition.acceptable_keys['coordinate_required'], prompt_definition.acceptable_keys["coordinate_required_link_forbidden"] if hoveredTileName is None else []), [] if hoveredTileName is None else prompt_definition.acceptable_keys['link_required']))
      tooltipText = f"{hoveredTileDisplayName}\n\n{NEWLINE.join(prompt_definition.key_descriptions[keyCode] for keyCode in _keycodesAvailableNowGen)}"
      tooltipLineSurfs = [font.render(text=tooltipTextLine, fgcolor=WINDOW_TEXT_COLOR, bgcolor=WINDOW_BACKGROUND_COLOR)[0] for tooltipTextLine in tooltipText.split("\n")]
      tooltipSurf = join_surfaces_vertically(tooltipLineSurfs, WINDOW_BACKGROUND_COLOR, padding=TOOLTIP_PADDING)
      outlinedTooltipSurf = make_externally_outlined_copy(tooltipSurf, thickness=2, color=WINDOW_TEXT_COLOR)
      # blit the tooltip a bit below the pointer:
      screen.blit(outlinedTooltipSurf, dest=int_vec_add(pygame.mouse.get_pos(), (2, 22)))
    
    # pointer image:
    if prompt_definition.pointer_image is not None:    
      screen.blit(pil_image_to_surface(prompt_definition.pointer_image), dest=int_vec_subtract(pygame.mouse.get_pos(), int_vec_divide_by_scalar_exact(prompt_definition.pointer_image.size, 2)))
    # }
    
    time.sleep(1.0/FPS) # the target FPS will never be hit this way but that's ok.
    pygame.display.flip()
    for event in pygame.event.get():
      
      if event.type == pygame.QUIT:
        print("exiting from within pygame")
        return AtlasPromptExit()
      elif event.type == pygame.MOUSEBUTTONDOWN:
        if hoveredTileCoord is None:
          continue # invalid click, no data to submit, don't submit.
        if not prompt_definition.clicks_are_acceptable:
          continue
        return AtlasPromptSubmission(coordinate=hoveredTileCoord, event=event)
      elif event.type == pygame.KEYDOWN:        
        if event.key in prompt_definition.acceptable_keys["no_requirements"]:
          return AtlasPromptSubmission(coordinate=hoveredTileCoord, event=event)
        elif event.key in prompt_definition.acceptable_keys["coordinate_required"]:
          if hoveredTileCoord is None:
            continue
          return AtlasPromptSubmission(coordinate=hoveredTileCoord, event=event)
        elif event.key in prompt_definition.acceptable_keys["link_required"]:
          if hoveredTileCoord is None:
            continue
          if hoveredTileName is None:
            continue
          return AtlasPromptSubmission(coordinate=hoveredTileCoord, event=event)
        elif event.key in prompt_definition.acceptable_keys["coordinate_required_link_forbidden"]:
          if hoveredTileCoord is None:
            continue
          if hoveredTileName is not None:
            continue
          return AtlasPromptSubmission(coordinate=hoveredTileCoord, event=event)
        else:
          print(f"atlas_interactive_prompt: ignoring key {event.key!r} because it is not acceptable.")

def prompt_user_for_a_free_coordinate(tile_image, tile_name, atlas_image) -> AtlasPromptResponse:
  raise NotImplementedError("this usage of AtlasPromptDefinition is out of date.")
  result = atlas_interactive_prompt(prompt_definition=AtlasPromptDefinition(
    tile_preview_image=tile_image,
    tile_preview_top_text="choose a coordinate for this new tile",
    tile_preview_bottom_text=tile_name,
    acceptable_keys={"no_requirements":[],"coordinate_required":[],"link_required":[]},
    alt_instructions="\n\n[left click] use this coordinate",
    clicks_are_acceptable=True,
  ), atlas_image=atlas_image)
  pygame.display.quit()
  return result





def pygame_wait_for_any_key():
    runEventLoop = True
    while runEventLoop:
      time.sleep(1.0/FPS)
      for event in pygame.event.get():
        if event.type == pygame.QUIT:
          print("exiting from pygame quit")
          exit(EXIT_CODES["PYGAME_QUIT"])
        if event.type == pygame.KEYDOWN:
          runEventLoop = False
        if event.type == pygame.MOUSEBUTTONDOWN:
          runEventLoop = False

def run_interactive_management_mode() -> None:
  
  blankPreviewImage = Image.new("RGB", size=(64,1))
  mainPromptDefinition = AtlasPromptDefinition(
    tile_preview_image=blankPreviewImage,
    pointer_image=None,
    tile_preview_top_text="Welcome to atlas.py!",
    tile_preview_bottom_text="Hover over a tile in the atlas for more options.",
    acceptable_keys={"no_requirements":[ord("q"), pygame.K_RETURN],"coordinate_required":[ord("s"), ord("m"), pygame.K_BACKSPACE],"link_required":[ord("u"), ord("r"), ord("i"), ord("e"), pygame.K_DELETE], "coordinate_required_link_forbidden":[ord("l")]},
    clicks_are_acceptable=False,
    key_descriptions={
      ord("s"): "[s] show",
      ord("i"): "[i] import",
      ord("e"): "[e] export",
      ord("r"): "[r] rename",
      ord("l"): "[l] link",
      ord("u"): "[u] unlink",
      ord("m"): "[m] move",
      pygame.K_BACKSPACE: "[backspace] clear cell",
      pygame.K_DELETE: "[delete] delete tile file",
      pygame.K_RETURN: "[enter] save and quit",
      ord("q"):"[q] quit without saving",
    },
  )
  
  
  def manage_link(coordinate):
    tileNamesForPrompt = find_tile_names()
    surfaceSelectionResponse = scrolling_surface_list_selection_prompt([GET_DEFAULT_FONT().render(text=tileName, fgcolor=(WINDOW_FAINT_TEXT_COLOR if tileName in CONFIG.coordinates_to_names.inverse else WINDOW_TEXT_COLOR), bgcolor=WINDOW_BACKGROUND_COLOR)[0] for tileName in tileNamesForPrompt])
    if isinstance(surfaceSelectionResponse, int):
      chosenName = tileNamesForPrompt[surfaceSelectionResponse]
      CONFIG.coordinates_to_names[coordinate] = chosenName
    else:
      assert surfaceSelectionResponse is None
      # do nothing (cancel), because the user did not select a name.
  
  def manage_unlink(coordinate):    
    print(f"removing link from {coordinate} to {CONFIG.coordinates_to_names[coordinate]!r}")
    del CONFIG.coordinates_to_names[coordinate]
  
  def manage_delete_tile_file(coordinate):
    pathToRemove = TILE_FOLDER_PATH + SEP + CONFIG.coordinates_to_names[coordinate]
    if os.path.exists(pathToRemove):
      print(f"deleting tile file {pathToRemove}")
      os.remove(pathToRemove)
    else:
      print(f"cannot remove tile file {pathToRemove} because it does not exist")
      
  def manage_clear_cell(coordinate):
    startX, startY, stopX, stopY = cell_coordinate_to_pillow_rect(coordinate)
    for y in range(startY, stopY):
      for x in range(startX, stopX):
        # assert ATLAS_IMAGE_CREATION_FILL_COLOR == ATLAS_IMAGE_BLANK_COLOR, "update for checkerboard??"
        atlasImage.putpixel((x,y), ATLAS_IMAGE_CREATION_FILL_COLOR)
        
  def manage_rename(atlas_image, coordinate):
    assert isinstance(atlas_image, Image.Image)
    assert is_valid_int_pair_tuple(coordinate)
    pathToRename = TILE_FOLDER_PATH + SEP + CONFIG.coordinates_to_names[coordinate]
    tilePromptResponse = prompt_user_for_tile_name(get_preview_pil_image_of_cell(atlas_image, coordinate), enable_skip_button=False)
    assert isinstance(tilePromptResponse, TilePromptResponse)
    newName = None
    if isinstance(tilePromptResponse, TilePromptSubmission):
      newName = tilePromptResponse.name
    elif isinstance(tilePromptResponse, TilePromptExit):
      print("exiting because of tile prompt choice to exit")
      exit(EXIT_CODES["TILE_PROMPT_EXIT_CHOICE"])
    else:
      raise ValueError(tilePromptResponse)
    newPath = TILE_FOLDER_PATH + SEP + newName
    assert newName not in CONFIG.coordinates_to_names.values()
    assert not os.path.exists(newPath)
    if os.path.exists(pathToRename):
      os.rename(pathToRename, newPath)
    del CONFIG.coordinates_to_names[coordinate]
    CONFIG.coordinates_to_names[coordinate] = newName
  
  def manage_show(atlas_image, coordinate):
    assert isinstance(atlas_image, Image.Image)
    assert is_valid_int_pair_tuple(coordinate)
    screen = pygame.display.get_surface()
    apply_haze(screen)
    screen.blit(get_preview_surface_of_cell(atlas_image, coordinate), dest=(0, 0))
    pygame.display.flip()
    pygame_wait_for_any_key()
    
  def manage_move(atlas_image, coordinate):
    """ modify both config and atlas image. save atlas_image immediately, config still needs to be saved later. """
    assert isinstance(atlas_image, Image.Image)
    assert is_valid_int_pair_tuple(coordinate)
    moveResponse = atlas_interactive_prompt(prompt_definition=AtlasPromptDefinition(
      tile_preview_image=blankPreviewImage,
      pointer_image=surface_to_pil_image(make_externally_outlined_copy(pil_image_to_surface(crop_atlas_image_to_tile_image(atlas_image, coordinate)), thickness=1, color=HIGHLIGHT_COLOR)),
      tile_preview_top_text="", tile_preview_bottom_text="",
      acceptable_keys={"no_requirements":[], "coordinate_required":[], "link_required":[], "coordinate_required_link_forbidden":[]},
      clicks_are_acceptable=True,
      key_descriptions=dict(),
    ), atlas_image=atlas_image)
    assert isinstance(moveResponse, AtlasPromptResponse)
    if isinstance(moveResponse, AtlasPromptSubmission):
      # edit the mapping:
      coordinateA, coordinateB = coordinate, moveResponse.coordinate
      if coordinateA == coordinateB:
        print("manage_move will not do anything because the same coordinate was clicked twice.")
        return
      del coordinate
      nameA = CONFIG.coordinates_to_names.pop(coordinateA, None)
      nameB = CONFIG.coordinates_to_names.pop(coordinateB, None)
      if nameB is not None:
        CONFIG.coordinates_to_names[coordinateA] = nameB
      if nameA is not None:
        CONFIG.coordinates_to_names[coordinateB] = nameA
      # edit the atlas_image:
      tileA = crop_atlas_image_to_tile_image(atlas_image, coordinateA)
      tileB = crop_atlas_image_to_tile_image(atlas_image, coordinateB)
      atlas_image.paste(tileA, cell_coordinate_to_pillow_rect(coordinateB))
      atlas_image.paste(tileB, cell_coordinate_to_pillow_rect(coordinateA))
      atlas_image.save(ATLAS_IMAGE_PATH)
    else:
      assert isinstance(moveResponse, AtlasPromptExit)
      raise NotImplementedError("what should happen when user exits from move?")
  
  with Image.open(ATLAS_IMAGE_PATH) as atlasImage:
    while True:
      
      response = atlas_interactive_prompt(prompt_definition=mainPromptDefinition, atlas_image=atlasImage)
      assert isinstance(response, AtlasPromptResponse)
      
      if isinstance(response, AtlasPromptSubmission):
        if response.event.type == pygame.KEYDOWN:
          if response.event.key == ord("l"):
            manage_link(response.coordinate)
          elif response.event.key == ord("u"):
            manage_unlink(response.coordinate)
          elif response.event.key == pygame.K_DELETE:
            manage_delete_tile_file(response.coordinate)
          elif response.event.key == pygame.K_BACKSPACE:
            manage_clear_cell(response.coordinate)
          elif response.event.key == ord("r"):
            manage_rename(atlasImage, response.coordinate)
          elif response.event.key == ord("s"):
            manage_show(atlasImage, response.coordinate)
          elif response.event.key == ord("m"):
            manage_move(atlasImage, response.coordinate)
          elif response.event.key == ord("i"):
            import_tile_with_coordinate(atlasImage, response.coordinate)
          elif response.event.key == ord("e"):
            export_tile_with_coordinate(atlasImage, response.coordinate)
            
          elif response.event.key == pygame.K_RETURN:
            print("finished with interactive management mode")
            atlasImage.save(ATLAS_IMAGE_PATH)
            pygame.display.quit()
            return
          elif response.event.key == ord("q"):
            print("exiting because of atlas prompt quit choice")
            exit(EXIT_CODES["ATLAS_PROMPT_QUIT_CHOICE"])
          else:
            raise ValueError(f"unknown key code {response.event.key}")
        else:
          raise ValueError(f"unknown pygame event type {response.event.type}")
      elif isinstance(response, AtlasPromptExit):
        print("exiting because of atlas prompt exit (a pygame exit)")
        exit(EXIT_CODES["PYGAME_QUIT"])
      else:
        raise ValueError(response)









def do_tile_export(*, atlas_image: Image.Image, discover: bool, organize: bool):
  if not os.path.exists(ATLAS_IMAGE_PATH):
    raise FileNotFoundError("can't export when atlas image does not exist.")
    
  for y in range(CONFIG.atlas_size[1]):
    for x in range(CONFIG.atlas_size[0]):
      tileImg = crop_atlas_image_to_tile_image(atlas_image, (x,y))
      if (x,y) not in CONFIG.coordinates_to_names:
        if discover and not tile_image_is_blank(tileImg):
          response = prompt_user_for_tile_name(tileImg)
          assert isinstance(response, TilePromptResponse)
          if isinstance(response, TilePromptSubmission):
            newTileName = response.name
          elif isinstance(response, TilePromptSkip):
            continue
          elif isinstance(response, TilePromptExit):
            exit(EXIT_CODES["TILE_PROMPT_EXIT_CHOICE"])
          else:
            raise ValueError(response)
          CONFIG.coordinates_to_names[(x,y)] = newTileName
        else:
          continue # don't attempt to export.
      assert (x,y) in CONFIG.coordinates_to_names
      export_tile_with_coordinate(atlas_image=atlas_image, coordinate=(x,y))
      
def do_tile_import(*, atlas_image: Image.Image, discover: bool, organize: bool):
  if not os.path.exists(ATLAS_IMAGE_PATH):
    assert False, "why is this test here?" # TODO
    
  newlyDiscoveredNames = []
  availableFileTileNames = find_tile_names()
  for registeredTileCoord, registeredTileName in CONFIG.coordinates_to_names.items():
    if registeredTileName not in availableFileTileNames:
      print(f"warning: cannot import tile {registeredTileName!r} to cell {registeredTileCoord} because it does not exist as a file.")
  for tileName in availableFileTileNames:
    if tileName in CONFIG.coordinates_to_names.inverse:
      import_tile_with_name(atlas_image, tileName)
    else:
      newlyDiscoveredNames.append(tileName)
  atlas_image.save(ATLAS_IMAGE_PATH) # this is a good time to save progress. config has not changed and doesn't need to be saved.
  
  if discover and organize:
    raise ValueError("can't do discover and organize at the same time.")
  elif not (discover or organize):
    pass
  else:
    assert xor(discover, organize)
    for tileName in newlyDiscoveredNames:
      placementCoordinate = None # must not carry over from previous iteration
      if discover:
        placementCoordinate = get_a_free_coordinate()
      elif organize:
        with Image.open(tile_name_to_path(tileName)) as tileImgForPrompt:
          promptResult = prompt_user_for_a_free_coordinate(tile_image=tileImgForPrompt, tile_name=tileName, atlas_image=atlas_image)
          assert isinstance(promptResult, AtlasPromptResponse)
          if isinstance(promptResult, AtlasPromptSubmission):
            if promptResult.event.type == pygame.MOUSEBUTTONDOWN:
              placementCoordinate = promptResult.coordinate
            elif promptResult.event.type == pygame.KEYDOWN:
              raise ValueError("no keys should be accepted here.")
            else:
              raise ValueError("invalid event type")
          elif isinstance(promptResult, AtlasPromptExit):
            exit(EXIT_CODES["PYGAME_QUIT"])
          else:
            raise ValueError(promptResult)
      else:
        assert False, "unreachable"
      assert is_valid_int_pair_tuple(placementCoordinate)
      CONFIG.coordinates_to_names.inverse[tileName] = placementCoordinate
      import_tile_with_name(atlas_image, tileName)
    atlas_image.save(ATLAS_IMAGE_PATH)
    # TODO put transport in charge of whether and when atlas config gets saved. Atlas config and atlas image should probably be saved at the same time.

def do_tile_transport(direction, discover=False, organize=False) -> None:
  assert not (discover and organize)
    
  with Image.open(ATLAS_IMAGE_PATH) as atlasImg:
    if direction is TRANSPORT_DIRECTION.EXPORT:
      do_tile_export(atlas_image=atlasImg, discover=discover, organize=organize)
    elif direction is TRANSPORT_DIRECTION.IMPORT:
      do_tile_import(atlas_image=atlasImg, discover=discover, organize=organize)
    else:
      raise ValueError(direction)
    # there is no need to save atlasImg now, it has been done.






"""
texture atlas editor commands:
  atlas-image <create|delete|view>
  atlas-config <create|delete|view>
  atlas-config regenerate //look at tile files and atlas image to restore a missing config file. possibly helpful in mass renaming. Might require the user to choose what happens with duplicate tiles, or, the command might require all duplicates to be deleted before it works.
  transport in [<--discover|--organize|--organize-all>]
  transport out [--discover]
  tiles delete [--confirm] //note: command must fail if confirm is provided when it is not necessary.
  manage // the interactive mode with the keyboard shortcuts.
  // some way to regenerate or detect renamed tiles.
  // some way to swap tile positions, or copy tiles.
"""
parser = argparse.ArgumentParser()
subparser_manager = parser.add_subparsers(dest="subcommand")

atlas_image_cmd_parser = subparser_manager.add_parser("atlas-image", help="Command for handling the single atlas image for the project")
atlas_image_cmd_parser.add_argument("subaction", help="May be any of: create, delete, show")

atlas_config_cmd_parser = subparser_manager.add_parser("atlas-config", help="Command for handling the single atlas config file for the project")
atlas_config_cmd_parser.add_argument("subaction", help="May be any of: create, delete, show")

transport_cmd_parser = subparser_manager.add_parser("transport", help="Command for transporting artwork into or out of the atlas image")
transport_cmd_parser.add_argument("direction", help="in or out")
transport_cmd_parser.add_argument("--discover", action="store_true", help="Discover new art and add it to the config")
transport_cmd_parser.add_argument("--organize", action="store_true", help="Discover new art and add it to the config at user-specified locations")
transport_cmd_parser.add_argument("--organize-all", action="store_true", help="The user specifies the location of every tile from scratch")

manage_parser = subparser_manager.add_parser("manage", help="enter interactive mode")



args = parser.parse_args()
if args.subcommand == "atlas-image":
  # assert not any((args.discover, args.organize, args.organize_all))
  if args.subaction == "create":
    create_atlas_image()
  elif args.subaction == "delete":
    delete_atlas_image()
  elif args.subaction == "show":
    assert os.path.exists(ATLAS_IMAGE_PATH) and ATLAS_IMAGE_PATH.endswith(".png")
    os.startfile(ATLAS_IMAGE_PATH)
  else:
    raise ValueError(args.subaction)
elif args.subcommand == "atlas-config":
  # assert not any((args.discover, args.organize, args.organize_all))
  if args.subaction == "create":
    create_atlas_config()
  elif args.subaction == "delete":
    delete_atlas_config()
  elif args.subaction == "show":
    assert os.path.exists(ATLAS_CONFIG_PATH)
    with open(ATLAS_CONFIG_PATH, "r") as configFile:
      print(configFile.read())
  else:
    raise ValueError(ars.subaction)
elif args.subcommand == "transport":
  CONFIG.load()
  CONFIG.assert_is_saved_correctly()
  direction = PARSE_TRANSPORT_DIRECTION(args.direction)
  assert args.discover is True or args.discover is False
  assert at_most_one((args.discover, args.organize, args.organize_all))
  if args.organize_all:
    raise NotImplementedError("a window to allow all tiles to be placed by the user into the atlas one by one") # this is only allowed while an atlas image does not exist, to prevent confusion from the atlas image and atlas config being completely different, which could cause data loss if you forget about it and then either (1) transport out and then delete the atlas image or (2) transport in and then delete the tile images.
  else:
    if direction is TRANSPORT_DIRECTION.EXPORT:
      assert not args.organize
      assert not args.organize_all
    do_tile_transport(direction, discover=args.discover, organize=args.organize)
  if args.discover or args.organize or args.organize_all:
    CONFIG.save() # TODO move into transport
  CONFIG.assert_is_saved_correctly()
elif args.subcommand == "manage":
  CONFIG.load()
  CONFIG.assert_is_saved_correctly()
  run_interactive_management_mode()
  CONFIG.save()
  CONFIG.assert_is_saved_correctly()
elif args.subcommand is None:
  print("a subcommand must be used. Use the --help option for information on subcommands.")
else:
  raise ValueError(args.subcommand)
  
  
exit(EXIT_CODES["GENERAL_SUCCESS"])

