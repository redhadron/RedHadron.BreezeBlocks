Welcome to the Breeze Blocks mod for Hytale!
To play with this mod, it is recommended that you download the latest release from https://www.curseforge.com/hytale/mods/breezeblocks

### About the mod

Breeze blocks (aka Cobogós) are bricks with holes - they provide both shade and airflow. I've balanced this mod for survival play and added accurate icons, sounds, particles, and breaking/placing animations. I hope you enjoy building with this mod!

### About the repo

This repository contains all of my models, icon templates, and scripts for generating hytale asset files and item icons.

- generate.py is the script to generate a working hytale mod from template files. It creates json asset files from a template, creates icons by multiplying material textures with shape masks, and creates new textures by pasting together smaller regions of hytale's stock textures.

- atlas.py is a texture atlas management tool. While importing tiles to an atlas, it can discover new tiles and allows the user to choose where in the atlas they will go. While exporting tiles, it detects new tiles and prompts the user to name them.

- colors.py looks at every texture in Hytale's BlockTextures folder, extracts an average color, and saves it in a python shelf for later use in choosing particle colors.

- mismatch.py lists all PNG files, and groups them by how many blockymodel files exist with names to which the PNG file's base name is a prefix. This is helpful for creating icons first, and then using those icon files and this script to keep track of which models still need to be created.

- renamer.py is a bulk renaming tool, with the additional capability of updating file names where they appear in the text of other files. This script is made obsolete by the interactive mode of atlas.py.

Suggestions are appreciated!