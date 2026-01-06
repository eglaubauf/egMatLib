# egMatLib - A Material Library for Houdini

A Material Library for Houdini Karma, Mantra, Redshift and Arnold and Octane

[![Interface](https://github.com/eglaubauf/egMatLib/blob/dev/scripts/python/matlib/res/img/MatLib_v2.png)](https://github.com/eglaubauf/egMatLib/blob/dev/scripts/python/matlib/res/img/MatLib_v2.png)

## Features:

### Basics:

- Lightweight (Houdini-native) storing and loading of node networks
- Save MaterialX, Redshift Material Builders, Principled Shaders, Mantra Materialbuilders and Arnold Materialbuilders
- Favorites
- Categories
- Searchable Material-Names and tags (use ":" as a modifier )
- Open database (.json)
  - Houdini Nodes are stored in Houdini Format though
- Edit multiple materials at the same time via the Details-Pane
- Easy adjustable custom preview and rendersize, quality
- ACES 1.3 support (both, 1.2 and 1.3 are supported now)
- Unrestricted Houdini Licensing (support Full Commercial and Indie)

### New Features in V2:

- complete rewrite
- improve onBoarding Process/Installation
- improved User-Interface
  - drag and drop material from and to Node Editor
  - Remove manual Context Switching for simplification
  - Much better feedback on Thumbnail Scaling
- MultiThreaded Thumbnail Generation
- Ability to swap Shaderball for the Houdini Default
- Improved Preferences:
  - Ability to en/disable renderers
  - Enable/Disable "Rendering On Import": This can be handy if you want to import a lot of materials
  - Set Samples for Houdini Karma
  - Set Complex or simple Shaderball for Rendering
- To import old Materiallibrary files please choose Library/Import from MatLib V1 and select the correspoding .json file

## Compatibility

- Tested on 21.0.580 on Ubuntu and MacOS, should work everywhere
- USD/Solaris for Karma only
- Python 3 support only
- Redshift 3.5+ (untested)
- Octane for 20.5.487 (untested)
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
- Thanks to @thopedam for providing initial Octane Support

## Contact

- Found a bug or suggest a feature? please open an issue
