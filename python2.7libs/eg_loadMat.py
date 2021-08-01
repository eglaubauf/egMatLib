import hou


def run():

    # TODO get extension from settings
    # TODO get default dir from settings
    path = hou.ui.selectFile(title="Select File", file_type=hou.fileType.Any, pattern="*.rsmat")

    if not path:
        return

    # Get Filename
    filename = path.rsplit('/', 1)
    filename = filename[1][:-6]

    # CreateBuilder
    builder = hou.node('/mat').createNode('redshift_vopnet')
    builder.setName(filename, unique_name=True)

    # Delete Default children in RS-VopNet
    for node in builder.children():
        node.destroy()

    # Load File
    builder.loadItemsFromFile(path, ignore_load_warnings=False)
    # MakeFancyPos
    builder.moveToGoodPosition()
