"""
Module with helpful utility functions used in and around houdini
"""

import os
import re

import hou


def get_children_recursive(nodes: list[hou.Node]) -> hou.Node | None:
    """
    Get Children recursively for the given list of nodes

    :param nodes: Description
    :type nodes: list[hou.Node]
    :return: Description
    :rtype: Node | None
    """
    for node in nodes.children():
        if node.type().name() == "subnet":
            for n in node.children():
                return get_children_recursive(n)
        elif node.type().name() == "geo":
            for sop in node.children():
                if sop.isGenericFlagSet(hou.nodeFlag.Display):
                    return sop


def get_connected_nodes(node: hou.Node) -> list[hou.Node]:
    """
    Get all connected nodes for the given node
    Returns Input and Output Nodes in a single list

    :param node: Description
    :type node: hou.Node
    :return: Description
    :rtype: list[Node]
    """
    nodes = [node]
    in_nodes = get_connected_input_nodes(nodes, selected=[])
    out_nodes = get_connected_output_nodes(nodes, selected=[])
    return in_nodes + out_nodes


def get_connected_input_nodes(
    nodes: list[hou.Node], selected: list[hou.Node]
) -> list[hou.Node]:
    """
    Get all connected Input nodes for the given node
    Returns only Input Nodes in a single list

    :param nodes: Description
    :type nodes: list[hou.Node]
    :param selected: Description
    :type selected: list[hou.Node]
    :return: Description
    :rtype: list[Node]
    """
    for node in nodes:
        if node is not None:
            selected.append(node)
            get_connected_input_nodes(node.inputs(), selected)
    return selected


def get_connected_output_nodes(
    nodes: list[hou.Node], selected: list[hou.Node]
) -> list[hou.Node]:
    """
    Get all connected Input nodes for the given node
    Returns only Input Nodes in a single list

    :param nodes: Description
    :type nodes: list[hou.Node]
    :param selected: Description
    :type selected: list[hou.Node]
    :return: Description
    :rtype: list[Node]
    """
    for node in nodes:
        if node is not None:
            selected.append(node)
            get_connected_output_nodes(node.outputs(), selected)
    return selected


def break_materialrefs() -> None:
    """
    Breaks all Material References for the currently selected Node
    """
    sel_nodes = hou.selectedNodes()

    for node in sel_nodes:
        lops = node.children()
        for lop in lops:
            if lop.type().name() == "materiallibrary":
                mats = lop.children()
                for mat in mats:
                    if mat.type().name() == "principledshader::2.0":
                        for parm in mat.parms():
                            parm.set(parm.evalAsString())

                    if mat.type().name() == "mtlxUsdUVTexture":
                        for parm in mat.parms():
                            parm.set(parm.evalAsString())

                    if mat.type().name() == "usduvtexture::2.0":
                        for parm in mat.parms():
                            parm.set(parm.evalAsString())


def save_selected_hda() -> None:
    """
    Save the selected Nodes as HDA
    """
    sel = hou.selectedNodes()
    for node in sel:
        if node.type().definition() is None or node.matchesCurrentDefinition():
            continue
        node.type().definition().updateFromNode(node)
        node.matchCurrentDefinition()


def show_all_nodes() -> None:
    """
    Unhides All selected Nodes
    """
    # Get All Nodes
    sel = hou.selectedNodes()
    all_nodes = sel if sel else hou.node("/obj").allSubChildren()

    # Hide all
    for n in all_nodes:
        n.setGenericFlag(hou.nodeFlag.Visible, True)


def fix_fbx_mats() -> None:
    """
    Fixes all FBX Materials to Metal Rough Workflow
    """
    for mat in hou.selectedNodes():
        # Move Reflect Tex
        if "metal" in mat.parm("reflect_texture").evalAsString():
            mat.parm("metallic_useTexture").set(1)
            mat.parm("metallic_texture").set(mat.parm("reflect_texture").evalAsString())
            mat.parm("reflect_texture").set("")
            mat.parm("reflect_useTexture").set(0)
            mat.parm("metallic").set(1)
            mat.parm("reflect").set(1)

        # Fix Roughness
        if mat.parm("rough_useTexture").evalAsInt():
            mat.parm("rough").set(1)

        # Fetch Color Texture from disk
        if not mat.parm("basecolor_useTexture").evalAsInt():
            if "rough" in mat.parm("rough_texture").evalAsString():
                path = mat.parm("rough_texture").evalAsString()
                path = path.replace("roughness", "color")
                if os.path.exists(path):
                    mat.parm("basecolor_useTexture").set(1)
                    mat.parm("basecolor_texture").set(path)
            elif "metal" in mat.parm("metallic_texture").evalAsString():
                path = mat.parm("metallic_texture").evalAsString()
                path = path.replace("metalness", "color")
                if os.path.exists(path):
                    mat.parm("basecolor_useTexture").set(1)
                    mat.parm("basecolor_texture").set(path)

        # Fetch AO Texture from disk
        if not mat.parm("occlusion_useTexture").evalAsInt():
            if "rough" in mat.parm("rough_texture").evalAsString():
                path = mat.parm("rough_texture").evalAsString()
                path = path.replace("roughness", "ao")
                if os.path.exists(path):
                    mat.parm("occlusion_useTexture").set(1)
                    mat.parm("occlusion_texture").set(path)
            elif "metal" in mat.parm("metallic_texture").evalAsString():
                path = mat.parm("metallic_texture").evalAsString()
                path = path.replace("metalness", "ao")
                if os.path.exists(path):
                    mat.parm("occlusion_useTexture").set(1)
                    mat.parm("occlusion_texture").set(path)


def networkbox() -> None:
    """
    Draw a named Network Box around the selected Nodes
    """
    sel = hou.selectedNodes()
    nbox = sel[0].parent().createNetworkBox()

    for node in sel:
        nbox.addItem(node)

    sticky = sel[0].parent().createStickyNote()
    sticky.setColor(hou.Color(1, 1, 1))
    choice, msg = hou.ui.readInput("Name:")  # type: ignore
    sticky.setTextSize(1)
    sticky.setText(msg)
    sticky.setSize(hou.Vector2(4, 2))
    sticky.setDrawBackground(False)
    nbox.addStickyNote(sticky)

    pos = sel[0].position()
    pos[0] += 5
    pos[1] += 2
    sticky.setPosition(pos)
    nbox.setBounds(hou.BoundingRect(0, 0, 0.01, 0.01))
    nbox.fitAroundContents()


def container():
    """
    Return the Parm_Container for the current Node
    """
    parm_pane = hou.ui.curDesktop().paneTabOfType(hou.paneTabType.Parm)  # type: ignore
    parmnode = parm_pane.currentNode()
    parm_container = parmnode.parent()
    return parm_container


def find_parm(parmname: str) -> None:
    """Find Parms which reference the selected Parameter"""
    if parmname is None:
        text = hou.ui.readInput("Search text:", buttons=("Search", "Cancel"))[1]  # type: ignore
    else:
        text = parmname

    parm_pane = hou.ui.curDesktop().paneTabOfType(hou.paneTabType.Parm)  # type: ignore
    parmnode = parm_pane.currentNode()
    parm_container = parmnode.parent()

    nodes = parm_container.allSubChildren()
    pattern = ""
    pattern_count = 0

    print("----    found:   ----")
    for node in nodes:
        parms = node.parms()
        for parm in parms:
            raw = parm.rawValue()
            if raw.find(text) > -1:
                if pattern_count > 0:
                    pattern += " | "
                pattern += parm.name() + "~=*" + text + "*"
                pattern_count += 1
                print(
                    "NODE: "
                    + str(node)
                    + "   // PARM: "
                    + parm.description()
                    + "   // RAW: "
                    + raw
                )
    print("--------------------------")

    hou.ui.copyTextToClipboard(pattern)  # type: ignore


def sanitize_usd_path(path: str) -> str:
    """
    Sanitze String for usage in .usd files and Solaris

    :param path: Description
    :type path: str
    :return: Description
    :rtype: str
    """
    clean_path = path.replace(" ", "_")
    clean_path = clean_path.replace("-", "_")
    clean_path = re.sub("[^a-z^A-Z^0-9]", "_", path)
    return clean_path


def subframe_splits(node: hou.Node) -> str:
    """
    Allow for Subframe Input/Outputs on Filecaches

    :param node: Description
    :type node: hou.Node
    :return: Description
    :rtype: str
    """
    if node.parm("trange").evalAsString() != "off":
        if node.parm("f3").evalAsFloat() < 1:

            front = str(int(hou.frame())).zfill(4)
            back = str(round((hou.frame() - int(hou.frame())) * 100.0) / 100.0)
            back = back[2:]
            back = back.ljust(2, "0")
            return "." + front + "." + back
        else:
            return "." + str(int(hou.frame())).zfill(4)
    return ""


def texture_lookup(files: list[str] | str) -> dict:
    """
    Make Key Value Pairs for Filenames and return Dict

    :param files: Description
    :type files: list[str] | str
    :return: Description
    :rtype: dict[Any, Any]
    """

    diffuse_lookup = [
        "base_color",
        "basecolor",
        "diffuse",
        "albedo",
        "diff",
        "col",
    ]
    rough_lookup = ["rough", "roughness", "gloss"]
    refl_lookup = ["refl"]
    metallic_lookup = ["metal", "mtl"]
    displace_lookup = ["disp"]
    normal_lookup = ["norm", "normal", "nor"]
    bump_lookup = ["bump", "bmp"]
    height_lookup = ["height"]
    ao_lookup = ["ao", "ambient", "occlusion"]

    mapped = {
        "basecolor": "",
        "roughness": "",
        "normal": "",
        "metallic": "",
        "reflect": "",
        "displace": "",
        "bump": "",
        "ao": "",
    }

    if files == "":
        return mapped

    if isinstance(files, list):
        strings = files
    else:
        strings = files.split(";")

    # Get all Entries
    for s in strings:
        # Remove Spaces
        s = s.rstrip(" ")
        s = s.lstrip(" ")

        # Get Name of File
        name = s.split(".")
        k = name[0].rfind("/")
        name = name[0][k + 1 :]  # type: ignore

        for d in diffuse_lookup:
            if d in name.lower():
                mapped["basecolor"] = s

        for d in rough_lookup:
            if d in name.lower():
                mapped["roughness"] = s

        for d in normal_lookup:
            if d in name.lower():
                mapped["normal"] = s

        for d in metallic_lookup:
            if d in name.lower():
                mapped["metallic"] = s

        for d in refl_lookup:
            if d in name.lower():
                mapped["reflect"] = s

        for d in displace_lookup:
            if d in name.lower():
                mapped["displace"] = s

        for d in bump_lookup:
            if d in name.lower():
                mapped["bump"] = s

        for d in height_lookup:
            if d in name.lower():
                # if height_displace:  # User sets Height as Displacement
                mapped["displace"] = s
                # else:
                #    mapped["bump"] = s

        for d in ao_lookup:
            if d in name.lower():
                mapped["ao"] = s
    return mapped
