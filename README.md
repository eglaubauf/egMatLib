# egMatLib - A Material Library for Houdini

A Material Library for Houdini Mantra and Redshift

### Features:

- Lightweight storing of Node networks
- Quick Restoring of Shader Trees
- Full Support for all Node-Types
- Favorites
- Adding and removing of Categories
- Tags
- Search for Names and Tags (use t: )
- Open Database (.json)
- Stores Materials in Houdini's native node-storing format
- Material Preview (ShaderSphere)
- 2 open HDAs for custom edits (Mantra and Redshift)
- Deletion of entries from the database (deletes also from disk)
- Custom Preview and Rendersize
- ACES 1.2 support
- Moving/Selection of Database location
- Right Click Menus via Network pane
- Importing to current network location (pwd()/matnet)
- Easy installation with packages (see below)


### Compatibility

 - Tested on 18.5.633 Windows 10 and Ubuntu 20.04
 - Tested with Redshift 3.0.51
 - Other Builds might work, i will update regularly if things break
 - Python 2 support
 - Python 3 support
 -

### Todo
- Update Material
- Arnold Support?
- Cleanup


### Installation
- Download or Clone this repository and unzip
- Copy the proviede MatLib.json to your houdini18.5/packages folder
- Edit the line "G:/Git/MatLib" to the location of your downloaded folder
- Start Houdini

### Usage
 - Open Pane (MatLib)
 - On first usage the pane will prompt you for a directory:
   - Choose a safe directory --> this is where all your data will be stored
   - You also can change this directory later from Library/Preferences
 - Use buttons for import/export from library
 - Right Click on Redshift Material Builder, Principled Shader or Material Builder to store a material
 - Double Click on a Material in MatLib-Pane to import
 - Use the table view to the right for edit of currently seleted material
 - Search Function also can search tags with t:*yoursearchstring*


### Additional
- You can move the directory by hand on disk iy you need to
- Do not (!) edit the .json file by hand if you do not have to
  - you have been warned ;)


### Contact & License

- Found a bug? please open an issue or contact me directly, happy to help :)

- As always: Open Source. Is. Will be. Feel free to use for any purpose, no reselling. GPLv3 License applies

- Twitter: @eglaubauf
