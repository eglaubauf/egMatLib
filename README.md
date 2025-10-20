# egMatLib - A Material Library for Houdini

A Material Library for Houdini Karma, Mantra, Redshift and Arnold and Octane

[![Interface](https://github.com/eglaubauf/egMatLib/blob/main/img/MatLib_2_0.png)](https://github.com/eglaubauf/egMatLib/blob/dev/img/MatLib_2_0.png)


### New Features 2025.07
 - better UI scaling
 - Scale and hide-able UI Elements for CatView and DetailsView
 - Readme Updates
 - Add confirmation message on Library Creation

### New Features 2025

- Added USD/Solaris Support for Karma
- MaterialX Shader saves
- Octane support has been revamped and new Rendertarget compatibility has been added (currently Octane Beta)
- Removed HDAs to provide unrestricted licensing support
- Added new Preference Setting to block rendering of materials on import [^1]
- UI improvements: Detail and Cat View can now be hided from the menu


[^1]: this is useful when importing a lot of materials, to not block the ui on import. Use Rerender Thumbnail option afterwards

### Base Features:

- Lightweight (Houdini-native) storing and loading of node networks
- Save Materialx, Redshift Material Builders, Principled Shaders,  Mantra Materialbuilders and Arnold Materialbuilders
- Favorites
- Adding and removing of categories
- Searchable tags (use t: as a modifier ) and material-names
- Open database (.json)
- Material Preview
- Deletion of entries from the database (deletes also from disk)
- Edit multiple materials at the same time via the Details-Pane
- Easy adjustable custom preview and rendersize
- ACES 1.2 support
- Added ACES 1.3 support (both, 1.2 and 1.3 are supported now)
- Right Click Menus for adding materials quickly from the network pane
- Importing to current network location (pwd()/matnet)
- Double Click or right click for importing Materials into the scene
- Easy installation with packages (see below)


### Compatibility

 - Tested on 21.0.508 on Windows
 - USD/Solaris for Karma only
 - Python 3 support
 - Redshift 3.5+
 - Octane  for 20.5.487 tested
 - HtoA 6.3.7.0

### Installation
- Download or Clone this repository and unzip
- Copy the provided `MatLib.json` to your `houdini20.5/packages` folder
- Edit the line `/home/user/MatLib` to the location of your downloaded folder, e.g.: `C:/git/MatLib`
- Start Houdini

### Usage
 - Open Pane (MatLib)
 - Choose Library/Open Libary:
   - Choose a safe folder --> this is where all your data will be stored
   - You also can change this directory later from Library/Preferences
 - Use buttons for import/export from library
 - Right Click Material X Builder (Solaris/USD), Karma Builder (Solaris/USD),  Redshift Material Builder, Principled Shader,  Material Builder to store a material
 - Double Click on a Material in MatLib-Pane to import
 - Use the details view to the right for edit of currently seleted material
 - Search Function also can search tags with t:*yoursearchstring*


### Additional
- You can move the directory by hand on disk if you need to
- Do not (!) edit the .json file by hand if not needed
  - you have been warned ;)

### Acknowledgements
- Thanks to Rich Nosworthy for providing the ShaderBall-Setup - https://www.richnosworthy.tv
- Thanks to @thopedam for providing initial Octane Support


### Contact
- Found a bug or suggest a feature? please open an issue


### Support
I soley do this project for fun and entirely in my free time. If you are using it on a regular basis, consider buying me a coffee.

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/D1D31CEN9X)
