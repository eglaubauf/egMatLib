import hou
from matlib.prefs import prefs
from matlib.core import models
from matlib.dialogs import usd_dialog


def save_material(node: hou.Node) -> None:
    # Call from RC-Menus in Network Pane
    # TODO: Move
    # Initialize
    pref = prefs.Prefs()

    # Save new Data to Library
    library = models.MaterialLibrary()
    library.load(pref)

    # Get Stuff from User
    dialog = usd_dialog.UsdDialog()
    r = dialog.exec_()
    if dialog.canceled or not r:
        return

    # Check if Category or Tags already exist
    if dialog.categories:
        library.check_add_category(dialog.categories)
    if dialog.tags:
        library.check_add_tags(dialog.tags)

    library.add_asset(node, dialog.categories, dialog.tags, dialog.fav)

    library.save()

    # Update Widget
    for pane_tab in hou.ui.paneTabs():  # type: ignore
        if pane_tab.type() == hou.paneTabType.PythonPanel:
            if pane_tab.label() == "MatLib":
                panel = pane_tab.activeInterfaceRootWidget()
                panel.update_external()
                return
