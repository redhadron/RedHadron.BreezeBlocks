
import enum
import os
import json
import ast
import tkinter
import time
import itertools
import operator


# pip
from bidict import bidict
from PIL import Image, ImageTk, ImageDraw # the k in ImageTk is lowercase.
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "True"
import pygame
import argparse
import pydantic


"""
todo:
  -add check that atlas image file and atlas image size specified by config are the same.
  -allow multiple values to be specified as blank, so that a solid-color tile in any of those colors will be ignored. Introduce checkerboard background pattern.
  -make a better atlas_config.json creation process, eliminate default values for atlas size and tile size.
  -2d range.
  -vector math methods.
  -search "TODO" and "NotImplementedError" in this file.
"""

TILE_FOLDER = "."
SEP = os.sep
FPS = 30.0
ATLAS_IMAGE_NAME = "atlas_image.png"
ATLAS_IMAGE_PATH = ".\\" + ATLAS_IMAGE_NAME
ATLAS_CONFIG_PATH = ".\\atlas_config.json"
ATLAS_CONFIG_SORT_KEYS = True
ATLAS_CONFIG_INDENT = 4
ATLAS_IMAGE_CREATION_FILL_COLOR = (255, 255, 255)
ATLAS_IMAGE_BLANK_COLOR = (*ATLAS_IMAGE_CREATION_FILL_COLOR, 255)
TILE_PREVIEW_SCALE = 10
# ATLAS_PREVIEW_SCALE = 5
PREVIEW_GRID_LINE_COLOR = (127, 127, 127)
HIGHLIGHT_COLOR = (255, 0, 0)
WINDOW_BACKGROUND_COLOR = (31, 31, 31)
WINDOW_TEXT_COLOR = (250, 250, 250)
WINDOW_BG_STRING = "#cccccc"
class TRANSPORT_DIRECTION(enum.Enum):
  IMPORT = enum.auto()
  EXPORT = enum.auto()
def PARSE_TRANSPORT_DIRECTION(string):
  return {"in": TRANSPORT_DIRECTION.IMPORT, "out": TRANSPORT_DIRECTION.EXPORT}[string]
EXIT_CODES = {"GENERAL_SUCCESS":0, "TILE_PROMPT_EXIT_CHOICE": 2, "PYGAME_QUIT":3, "ATLAS_PROMPT_QUIT_CHOICE":4}






def validate_int_pair_tuple(int_tuple):
  assert isinstance(int_tuple, tuple) and len(int_tuple) == 2 and all(isinstance(item, int) for item in int_tuple), int_tuple

def remove_suffix(string, suffix):
  assert len(suffix) <= len(string)
  assert len(suffix) > 0
  assert string.endswith(suffix)
  return string[:-len(suffix)]
  
def remove_prefix(string, prefix):
  assert len(prefix) <= len(string)
  assert len(prefix) > 0
  assert string.startswith(prefix)
  return string[len(prefix):]
  
def bisect_at_infix(string, infix):
  assert string.count(infix) == 1
  a, b = string.split(infix)
  return (a, b)

def nand(a, b):
  return not (a and b)
  
def at_most_one(input_list):
  return sum(bool(item) for item in input_list) in (0, 1)


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
  assert all(isintance(component, int) for component in vec)
  assert isinstance(scale, int)
  return tuple(component*scale for component in vec)
  


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
      validate_int_pair_tuple(key)
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
  
def intersection_coordinate_to_pixel_coordinate(intersection_address):
  return int_vec_parallel_multiply(CONFIG.tile_size, intersection_address)
  
def get_a_free_coordinate():
  for y in range(CONFIG.atlas_size[1]):
    for x in range(CONFIG.atlas_size[0]):
      if (x,y) not in CONFIG.coordinates_to_names:
        return (x,y)
  assert False, "out of room"

def tile_coordinate_is_in_bounds(coordinate):
  validate_int_pair_tuple(coordinate)
  return 0 <= coordinate[0] < CONFIG.atlas_size[0] and 0 <= coordinate[1] < CONFIG.atlas_size[1]






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
  







def make_tile_preview_image(tile_image):
  previewSize = int_vec_scale_by(CONFIG.tile_size, TILE_PREVIEW_SCALE)
  modifiedTileImage = tile_image.resize(size=previewSize, resample=Image.Resampling.NEAREST) # resizing makes a copy so we are not drawing on the original.
  imageDrawer = ImageDraw.Draw(modifiedTileImage) 
  for y in range(CONFIG.tile_size[1]):
    imageDrawer.line((0,y*TILE_PREVIEW_SCALE,modifiedTileImage.size[0],y*TILE_PREVIEW_SCALE), PREVIEW_GRID_LINE_COLOR)
  for x in range(CONFIG.tile_size[0]):
    imageDrawer.line((x*TILE_PREVIEW_SCALE, 0, x*TILE_PREVIEW_SCALE, modifiedTileImage.size[1]), PREVIEW_GRID_LINE_COLOR)
  return modifiedTileImage


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


  
def prompt_user_for_tile_name(tile_image) -> TilePromptResponse:
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
      print("name contains invalid character")
      return
    promptResultHolder.value = TilePromptSubmission(entryText)
    window.destroy()
  entry.bind('<Return>', okayCallback)
  okayButton = tkinter.Button(text="OK", command=okayCallback)
  okayButton.bind('<Return>', okayCallback)
  okayButton.pack()
  
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
  
  
  
def pil_image_to_surface(pil_image):
  assert isinstance(pil_image, Image.Image)
  return pygame.image.fromstring(pil_image.tobytes(), pil_image.size, pil_image.mode)

def join_surfaces_vertically(surfaces, background_color):
  assert all(isinstance(item, pygame.Surface) for item in surfaces), surfaces
  width = max(surf.get_width() for surf in surfaces)
  height = sum(surf.get_height() for surf in surfaces)
  newSurf = pygame.Surface((width, height))
  newSurf.fill(background_color)
  y = 0
  for surf in surfaces:
    newSurf.blit(surf, (0, y))
    y += surf.get_height()
  assert y == newSurf.get_height()
  return newSurf
  
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
  tile_preview_top_text: str
  tile_preview_bottom_text: str
  alt_instructions: str
  static_instructions: str
  acceptable_keys: dict[str, list[int]]
  model_config = {"arbitrary_types_allowed": True} # this is required by Pydantic to use arbitrary types such as PIL's Image.Image as a type hint
    
def atlas_interactive_prompt(*, prompt_definition: AtlasPromptDefinition, atlas_image: Image.Image, _font=[]) -> AtlasPromptResponse:
  # this method should never do anything except display a prompt and return the user's choice of action. It should not perform that action.
  assert isinstance(prompt_definition.tile_preview_image, Image.Image)
  assert all(isinstance(item, int) for item in itertools.chain(*prompt_definition.acceptable_keys.values()))
  assert isinstance(atlas_image, Image.Image)
  pygame.init()
  if len(_font) == 0:
    _font.append(pygame.freetype.SysFont(pygame.freetype.get_default_font(), 18, bold=False))
  font = _font[0]
  
  screen = pygame.display.set_mode((600,400))
  atlasSurf = pil_image_to_surface(atlas_image)
  tilePreviewSurf = pil_image_to_surface(prompt_definition.tile_preview_image)
  
  while True:
    hoveredTileCoord = tuple(pygame.mouse.get_pos()[i]//CONFIG.tile_size[i] for i in (0,1)) # TODO int vec divide
    if not tile_coordinate_is_in_bounds(hoveredTileCoord):
      hoveredTileCoord = None
    
    screen.fill(WINDOW_BACKGROUND_COLOR)
    screen.blit(atlasSurf, (0,0))
    tilePreviewTopTextSurf = font.render(text=prompt_definition.tile_preview_top_text, fgcolor=WINDOW_TEXT_COLOR)[0]
    tilePreviewBottomTextSurf = font.render(text=prompt_definition.tile_preview_bottom_text, fgcolor=WINDOW_TEXT_COLOR)[0]
    labeledTilePreviewSurf = join_surfaces_vertically([tilePreviewTopTextSurf, tilePreviewSurf, tilePreviewBottomTextSurf], WINDOW_BACKGROUND_COLOR)
    screen.blit(labeledTilePreviewSurf, (atlasSurf.get_width()+10, 0))
    font.render_to(screen, text=prompt_definition.static_instructions, dest=(atlasSurf.get_width()+10, screen.get_height()-30), fgcolor=WINDOW_TEXT_COLOR)
    
    if hoveredTileCoord is not None:
      # highlight the cell:
      pygame.draw.lines(screen, HIGHLIGHT_COLOR, True, [intersection_coordinate_to_pixel_coordinate(int_vec_add(hoveredTileCoord, offset)) for offset in [(0,0), (1,0), (1,1), (0,1)]])
      # generate the tooltip:
      hoveredTileDisplayName = CONFIG.coordinates_to_names.get(hoveredTileCoord, default="empty")
      tooltipText = f"{hoveredTileDisplayName}{prompt_definition.alt_instructions}"
      tooltipLineSurfs = [font.render(text=tooltipTextLine, fgcolor=WINDOW_TEXT_COLOR, bgcolor=WINDOW_BACKGROUND_COLOR)[0] for tooltipTextLine in tooltipText.split("\n")]
      tooltipSurf = join_surfaces_vertically(tooltipLineSurfs, WINDOW_BACKGROUND_COLOR)
      # blit the tooltip a bit below the pointer:
      # TODO break out
      tooltipSurfSize = tooltipSurf.get_size()
      screen.fill(WINDOW_TEXT_COLOR, rect=(*int_vec_add(pygame.mouse.get_pos(), (0,20)), *int_vec_add(tooltipSurfSize, (4,4))))
      screen.blit(tooltipSurf, dest=int_vec_add(pygame.mouse.get_pos(), (2, 22)))
      
    time.sleep(1.0/FPS) # the target FPS will never be hit this way but that's ok.
    pygame.display.flip()
    for event in pygame.event.get():
      
      if event.type == pygame.QUIT:
        print("exiting from within pygame")
        pygame.display.quit()
        return AtlasPromptExit()
      elif event.type == pygame.MOUSEBUTTONDOWN:
        if hoveredTileCoord is None:
          continue # invalid click, no data to submit, don't submit.
        pygame.display.quit()
        return AtlasPromptSubmission(coordinate=hoveredTileCoord, event=event)
      elif event.type == pygame.KEYDOWN:
        # for keydown, don't check whether the hoveredTileCoord is None, because some keypresses (such as [s] for skip) are valid even without a valid coordinate.
        
        if event.key in prompt_definition.acceptable_keys["no_requirements"]:
          pygame.display.quit()
          return AtlasPromptSubmission(coordinate=hoveredTileCoord, event=event)
        elif event.key in prompt_definition.acceptable_keys["coordinate_required"]:
          if hoveredTileCoord is None:
            continue
          pygame.display.quit()
          return AtlasPromptSubmission(coordinate=hoveredTileCoord, event=event)
        elif event.key in prompt_definition.acceptable_keys["link_required"]:
          if hoveredTileCoord is None:
            continue
          if hoveredTileCoord not in CONFIG.coordinates_to_names:
            continue
          pygame.display.quit()
          return AtlasPromptSubmission(coordinate=hoveredTileCoord, event=event)
        else:
          print(f"atlas_interactive_prompt: ignoring key {event.key!r} because it is not acceptable.")


def prompt_user_for_a_free_coordinate(tile_image, tile_name, atlas_image) -> AtlasPromptResponse:
  return atlas_interactive_prompt(prompt_definition=AtlasPromptDefinition(**{"tile_preview_image":tile_image, "tile_preview_top_text":"choose a coordinate for this new tile", "tile_preview_bottom_text":tile_name, "acceptable_keys":{"no_requirements":[],"coordinate_required":[],"link_required":[]}, "alt_instructions":"\n\n[left click] use this coordinate"}), atlas_image=atlas_image)


def run_interactive_management_mode() -> None:
  blankPreviewImage = Image.new("RGB", size=(64,1))
  with Image.open(ATLAS_IMAGE_PATH) as atlasImage:
    while True:
      response = atlas_interactive_prompt(prompt_definition=AtlasPromptDefinition(
        tile_preview_image=blankPreviewImage,
        tile_preview_top_text="Welcome to atlas.py!",
        tile_preview_bottom_text="Hover over a tile in the atlas for more options.",
        acceptable_keys={"no_requirements":[ord("q"), pygame.K_RETURN],"coordinate_required":[],"link_required":[ord("u")]},
        alt_instructions="\n\n[u] unlink",
        static_instructions="[enter] save and exit\n[q] quit without saving"
      ), atlas_image=atlasImage)
      assert isinstance(response, AtlasPromptResponse)
      if isinstance(response, AtlasPromptSubmission):
        if response.event.type == pygame.KEYDOWN:
          if response.event.key == ord("u"):
            print(f"removing link from {response.coordinate} to {CONFIG.coordinates_to_names[response.coordinate]!r}")
            del CONFIG.coordinates_to_names[response.coordinate]
          elif response.event.key == pygame.K_RETURN:
            print("finished with interactive management mode")
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






def tile_image_is_blank(tile_image) -> bool:
  # assert tile_image.mode == "RGB", tile_image.mode
  assert tile_image.size == CONFIG.tile_size
  for pixelY in range(tile_image.size[1]):
    for pixelX in range(tile_image.size[0]):
      if tile_image.getpixel((pixelX,pixelY)) != ATLAS_IMAGE_BLANK_COLOR:
        return False
  return True
  
def find_tile_names():
  return [item for item in os.listdir(TILE_FOLDER) if item.endswith(".png") and item != ATLAS_IMAGE_NAME]

def tile_name_to_path(tile_name):
  return TILE_FOLDER + SEP + tile_name

def import_tile_with_name(tile_name, destination_atlas_pil_image) -> None:
  assert isinstance(tile_name, str)
  assert isinstance(destination_atlas_pil_image, Image.Image)
  assert tile_name in CONFIG.coordinates_to_names.inverse
  tilePath = tile_name_to_path(tile_name)
  if not os.path.exists(tilePath):
    raise FileNotFoundError(f"Tile with path {tilePath} does not exist and cannot be imported at the configured location. import_tile_with_name should only be called for names that are known to exist as files.")
  with Image.open(tilePath) as tileImg:
    # TODO check whether coordinate is valid according to config atlas size.
    # TODO check whether coordinate is valid according to actual size of atlas.
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


def do_tile_export(*, atlas_image, discover, organize):
  if not os.path.exists(ATLAS_IMAGE_PATH):
    raise FileNotFoundError("can't export when atlas image does not exist.")
    
  for y in range(CONFIG.atlas_size[1]):
    for x in range(CONFIG.atlas_size[0]):
      
      locationInAtlasImage = (*intersection_coordinate_to_pixel_coordinate((x,y)), *intersection_coordinate_to_pixel_coordinate((x+1,y+1)))
      tileImg = atlas_image.crop(locationInAtlasImage)
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
      tileImgPath = tile_name_to_path(CONFIG.coordinates_to_names[(x,y)])
      
      # \/ refuse to overwrite tile of wrong size
      if os.path.exists(tileImgPath):
        with Image.open(tileImgPath) as oldTileImg:
          if oldTileImg.size != tileImg.size:
            raise FileExistsError("the tile will not be overwritten because it is of a different size.")
            
      tileImg.save(tileImgPath)
      
def do_tile_import(*, atlas_image, discover, organize):
  if not os.path.exists(ATLAS_IMAGE_PATH):
    assert False, "why is this test here?" # TODO
    
  newlyDiscoveredNames = []
  availableFileTileNames = find_tile_names()
  for registeredTileCoord, registeredTileName in CONFIG.coordinates_to_names.items():
    if registeredTileName not in availableFileTileNames:
      print(f"warning: cannot import tile {registeredTileName!r} to cell {registeredTileCoord} because it does not exist as a file.")
  for tileName in availableFileTileNames:
    if tileName in CONFIG.coordinates_to_names.inverse:
      import_tile_with_name(tileName, atlas_image)
    else:
      newlyDiscoveredNames.append(tileName)
  atlas_image.save(ATLAS_IMAGE_PATH) # this is a good time to save progress. config has not changed and doesn't need to be saved.
      
  if discover or organize:
    assert nand(discover, organize), "the following code is designed for either discover or organize to be true, but not both"
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
      validate_int_pair_tuple(placementCoordinate)
      CONFIG.coordinates_to_names.inverse[tileName] = placementCoordinate
      import_tile_with_name(tileName, atlasImg)
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
atlas_image_cmd_parser.add_argument("subaction", help="May be any of: create, delete, view")

atlas_config_cmd_parser = subparser_manager.add_parser("atlas-config", help="Command for handling the single atlas config file for the project")
atlas_config_cmd_parser.add_argument("subaction", help="May be any of: create, delete, view")

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
  elif args.subaction == "view":
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
  elif args.subaction == "view":
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

