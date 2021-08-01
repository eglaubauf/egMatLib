import hou

def run():
    #TODO Save to Library directory from json
    lib = 'G:/Git/MatLib/lib'

    sel = hou.selectedNodes()

    # Check selection
    if not sel:
        hou.ui.displayMessage('No Material selected')
        return

    # Get Material Builder Node
    matBuild = sel[0]

    # Check against NodeType

    if matBuild.type().name() != "redshift_vopnet":
        hou.ui.displayMessage('No Material selected')
        return

    # Filepath where to save stuff
    name = matBuild.name()
    file_name = lib + "/" + name + '.rsmat'

    children = matBuild.children()
    matBuild.saveItemsToFile(children, file_name, save_hda_fallbacks=False)

    # Create Thumbnail
    thumb = hou.node("/obj").createNode("eg_thumbnail")

    thumb.parm("mat").set(matBuild.path())

    # Build path
    path = lib + '/' + name + ".exr"
    thumb.parm("path").set(path)
    exclude = "* ^" + thumb.name()
    thumb.parm("obj_exclude").set(exclude)
    lights = thumb.name() + "/*"
    thumb.parm("lights").set(lights)
    thumb.parm("render").pressButton()


    # OK, bye
    msg = "Material " + name + " created"
    hou.ui.displayMessage(msg)
