# egMatLib - A Material Library for Houdini

A Material Library for Houdini Karma, Mantra, Redshift and Arnold and Octane

[![Interface](https://github.com/eglaubauf/egMatLib/blob/dev/scripts/python/matlib/res/img/MatLib_v2.png)](https://github.com/eglaubauf/egMatLib/blob/dev/scripts/python/matlib/res/img/MatLib_v2.png)

## Features:

### Basics:

- Lightweight (Houdini-native) storing and loading of node networks
- Save MaterialX, OpenPBR-Surfae, Redshift Material Builders, Principled Shaders, Mantra Materialbuilders and Arnold Materialbuilders
- Favorites
- Categories
- Searchable Material-Names and tags (use ":" as a modifier )
- Open database (.json)
  - Houdini Nodes are stored in Houdini Format though
- Edit multiple materials at the same time via the Details-Pane
- Easy adjustable custom preview and rendersize, quality
- OCIO Config support
- Unrestricted Houdini Licensing (support Full Commercial and Indie)
- drag and drop material from and to Node Editor
- MultiThreaded Thumbnail Generation
- Ability to swap Shaderball for the Houdini Default

## Compatibility

- Tested on 21.0.631 on Ubuntu and MacOS, should work everywhere
- USD/Solaris for Karma only
- Python 3 support only
- Redshift 3.5+ (untested)
- Octane 2025 and 2026.1.0.1 for 21.0.559
- HtoA 6.3.7.0 (untested)

## Installation

- Download or Clone this repository and unzip
- Copy the provided `MatLib.json` to your `houdini21.0/packages` folder
- Edit the line `/home/user/MatLib` to the location of your downloaded folder, e.g.: `C:/Houdini_Things/MatLib`
- Start Houdini

## Usage

- Open Pane (MatLib)
- The setup will guide you to set a library if none is found
  - Choose a safe folder --> this is where all your data will be stored
  - You also can change this directory later from Library/Preferences
- Right Click Material X Builder (Solaris/USD), Karma Builder (Solaris/USD), Redshift Material Builder, Principled Shader, Material Builder to store a material
- Double Click on a Material in MatLib-Pane to import
- Use the details view to the right for edit of currently seleted material

## Acknowledgements

- Thanks to Rich Nosworthy for providing the Complex ShaderBall - https://www.richnosworthy.tv

## Contact

- Found a bug or suggest a feature? please open an issue
