Welcome to the Breeze Blocks mod for Hytale!

### About the mod

Breeze blocks are blocks with holes in them - they provide both shade and airflow. I've balanced this mod for survival play and added accurate icons, sounds, particles, and breaking/placing animations. I hope you enjoy building with this mod!

### About the repo

This repository contains all of my models, icon templates, and scripts for generating hytale asset files and item icons.

atlas.py is a texture atlas management tool. While importing tiles to an atlas, it can discover new tiles and allows the user to choose where in the atlas they will go. While exporting tiles, it detects new tiles and prompts the user to name them.

generate.py is the script to generate a working hytale mod from template files. It automatically generates item icons by multiplying material textures with shape masks.

renamer.py is a bulk renaming tool, with the additional capability of updating file names where they appear in the text of other files.

colors.py looks at every texture in Hytale's BlockTextures folder, extracts an average color, and saves it in a shelf for later use in choosing particle colors.

mismatch.py lists all PNG files, and groups them by how many blockymodel files exist with names to which the PNG file's base name is a prefix. This is helpful for creating icons first, and then using those icon files and this script to keep track of which models still need to be created.

Suggestions are appreciated!