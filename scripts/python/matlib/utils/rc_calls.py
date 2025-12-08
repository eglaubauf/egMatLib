import hou
from matlib.prefs import prefs
from matlib.core import models
from matlib.dialogs import usd_dialog


def save_material() -> None:
    """Call Save Script from RC-Menus in Houdini Network Pane"""

    # Find the Widget
    panel = None
    for pane_tab in hou.ui.paneTabs():  # type: ignore
        if pane_tab.type() == hou.paneTabType.PythonPanel:
            if pane_tab.label() == "MatLib":
                panel = pane_tab.activeInterfaceRootWidget()
    if not panel:
        return

    panel.save_asset()
