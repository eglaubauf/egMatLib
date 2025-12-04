import hou
from matlib.prefs import main_prefs
from matlib.core import matlib_core
from matlib.dialogs import usd_dialog


def save_material(node: hou.Node) -> None:
    # Call from RC-Menus in Network Pane
    # TODO: Move
    # Initialize
    pref = main_prefs.Prefs()

    # Save new Data to Library
    library = matlib_core.MaterialLibrary()
    library.load(pref.dir, pref)

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
