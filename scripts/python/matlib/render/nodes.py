import os
import hou
import time
from matlib.render import thumbnail_scene, thumbs
from matlib.core import material
from matlib.prefs import prefs
from matlib.helpers import helpers


class NodeHandler:
    def __init__(self, preferences: prefs.Prefs) -> None:
        self._preferences = preferences
        self._builder = 0
        self._renderer = ""
        self._import_path = None
        self._hou_parent = None

    def cleanup(self):
        self._builder.destroy()

    def get_current_network_node(self) -> None | hou.Node:
        """Return thre current Node in the Network Editor"""
        for pt in hou.ui.paneTabs():  # type: ignore
            if pt.type() == hou.paneTabType.NetworkEditor:
                return pt.currentNode().parent()
        return None

    @property
    def builder(self) -> int:
        return self._builder

    @property
    def renderer(self) -> str:
        return self._renderer


    def get_renderer_from_node(self, node: hou.Node) -> str:
        if node.type().name() == "redshift_vopnet":
            self._renderer = "Redshift"
            self._builder = 1
        elif node.type().name() == "materialbuilder":
            self._renderer = "Mantra"
            self._builder = 1
        elif node.type().name() == "principledshader::2.0":
            self._renderer = "Mantra"
            self._builder = 0
        elif node.type().name() == "arnold_materialbuilder":
            self._renderer = "Arnold"
            self._builder = 1
        elif node.type().name() == "octane_vopnet":
            self._renderer = "Octane"
            self._builder = 1
        elif node.type().name() == "subnet":
            for n in node.children():
                if "mtlx" in n.type().name():
                    self._renderer = "MaterialX"
                    self._builder = 0
        elif node.type().name() == "collect":
            self._renderer = "MaterialX"
            self._builder = 0
        return self._renderer

    def import_asset_to_scene(self, mat: material.Material) -> None | hou.Node:
        """Import a Material to the Nework Editor/Scene"""

        parms_file_name = (
            self._preferences.dir
            + self._preferences.asset_dir
            + mat.mat_id
            + ".interface"
        )

        self.update_context()
        self._hou_parent = hou.node("obj").createNode("matnet")
        if "MaterialX" in mat.renderer:
            self.load_interface_mtlx(parms_file_name, mat)
            self.load_items_file(mat)
        elif mat.renderer == "Mantra":
            self.load_interface_mantra(parms_file_name, mat)
        elif "Redshift" in mat.renderer:
            self.load_interface_other(parms_file_name, mat, "redshift_vopnet")
            self.load_items_file(mat)
        elif "Octane" in mat.renderer:
            self.load_interface_other(parms_file_name, mat, "octane_vopnet")
            self.load_items_file(mat)
        elif mat.renderer == "Arnold":
            self.load_interface_other(parms_file_name, mat, "arnold_materialbuilder")
            self.load_items_file(mat)

        # Setup MaterialLibrary if Import Context was such
        if self._import_path.type().name() == "materiallibrary":
            self._import_path.parm("materials").set(0)
            self._import_path.parm("fillmaterials").pressButton()
            i = 0
            while i < self._import_path.parm("materials").evalAsInt():
                self._import_path.parm("".join(["assign", str(i + 1)])).set(0)
                i += 1
        # Cleanup
        self._hou_parent.destroy()

    def update_context(self) -> None:
        curr = self.get_current_network_node()
        curr_typename = curr.type().name()

        if "stage" in curr_typename or "lopnet" in curr_typename:  # Solaris
            self._import_path = curr.createNode("materiallibrary")
        elif "materiallibrary" in curr_typename:  # Solaris
            self._import_path = curr
        elif (
            "subnet" in curr_typename
        ):  # Inside Subnet - go to stage - there is no clear identifier
            print(curr.parent().childTypeCategory().name())
            if "lop" in curr.parent().childTypeCategory().name().lower():
                self._import_path = curr.parent().createNode("materiallibrary")
            elif "vop" in curr.parent().childTypeCategory().name().lower():
                self._import_path = curr.parent()
            elif "sop" in curr.parent().childTypeCategory().name().lower():
                self._import_path = curr.parent().createNode("matnet")
        elif "matnet" in curr_typename or "mat" == curr_typename:  # OldSchool Matnet
            self._import_path = curr
        elif "geo" in curr_typename:
            self._import_path = curr.createNode("matnet")
        else:  # Default to Solaris if antyhing else is current
            self._import_path = hou.node("/stage").createNode("materiallibrary")

    def load_interface_mtlx(self, parms_file_name, mat) -> None:
        if os.path.exists(parms_file_name):
            interface_file = open(parms_file_name, "r", encoding="utf-8")
            code = interface_file.read()
            hou_parent = self._hou_parent  # needed for exec
            exec(code)

            builder = self._import_path.createNode("subnet")
            builder.setName(mat.name, unique_name=True)
            builder.setGenericFlag(hou.nodeFlag.Material, True)
            self._builder = builder
            for n in builder.children():
                n.destroy()

        else:
            return

    def load_interface_mantra(self, parms_file_name, mat: material.Material) -> None:
        builder = None
        if os.path.exists(parms_file_name):
            # Only load parms if MatBuilder
            if self.check_materialbuilder_by_id(mat.mat_id):
                interface_file = open(parms_file_name, "r", encoding="utf-8")
                code = interface_file.read()
                hou_parent = self._hou_parent  # needed for exec
                exec(code)

                builder = hou.selectedNodes()[0]
            # Selection will be empty if not a MaterialBuilder
            else:
                builder = self._import_path.createNode("materialbuilder")
        else:
            builder = hou.node(self._import_path).createNode("materialbuilder")

        builder.setName(mat.name, unique_name=True)
        builder.setGenericFlag(hou.nodeFlag.Material, True)
        # Delete Default children in MaterialBuilder
        for node in builder.children():
            node.destroy()

        # If node is Principled Shader
        if not mat.builder:
            n = builder.children()[0]
            hou.moveNodesTo((n,), builder.parent())  # type: ignore
            builder.destroy()
            builder = hou.selectedNodes()[0]
        else:
            new_mat = hou.moveNodesTo((builder,), self._import_path)  # type: ignore
            new_mat[0].moveToGoodPosition()
            builder = new_mat[0]
        self._builder = builder

    def load_interface_other(self, parms_file_name, mat, builder_name) -> None:
        if os.path.exists(parms_file_name):
            interface_file = open(parms_file_name, "r", encoding="utf-8")
            code = interface_file.read()
            hou_parent = self._hou_parent  # needed for exec
            exec(code)

            builder = hou.node("obj").createNode("matnet").children()[0]
        else:
            builder = hou.node(self._import_path).createNode(builder_name)

        builder.setName(mat.name, unique_name=True)
        builder.setGenericFlag(hou.nodeFlag.Material, True)
        # Delete Default children in RS-VopNet
        for node in builder.children():
            node.destroy()

        self._builder = builder

    def load_items_file(self, mat):
        file_name = (
            self._preferences.dir
            + self._preferences.asset_dir
            + mat.mat_id
            + self._preferences.ext
        )
        try:
            self._builder.loadItemsFromFile(file_name, ignore_load_warnings=False)
        except OSError:
            hou.ui.displayMessage("Failure on Import. Please Check Files.")  # type: ignore
            return None

        new_mat = hou.moveNodesTo((self._builder,), self._import_path)  # type: ignore
        new_mat[0].moveToGoodPosition()
        self._builder = new_mat[0]

    def save_node(self, node: hou.Node, asset_id: str, update: bool) -> bool:
        """Save Node wrapper for different Material Types"""
        if hou.getenv("OCIO") is None:
            hou.ui.displayMessage("Please set $OCIO first")  # type: ignore
            return False
        val = False

        if "Redshift" in self._renderer:
            with hou.InterruptableOperation(
                "Rendering", "Performing Tasks", open_interrupt_dialog=True
            ):
                val = self.save_node_redshift(node, asset_id, update)
        elif "Mantra" in self._renderer:
            with hou.InterruptableOperation(
                "Rendering", "Performing Tasks", open_interrupt_dialog=True
            ):
                val = self.save_node_mantra(node, asset_id, update)
        elif "Arnold" in self._renderer:
            with hou.InterruptableOperation(
                "Rendering", "Performing Tasks", open_interrupt_dialog=True
            ):
                val = self.save_node_arnold(node, asset_id, update)
        elif "Octane" in self._renderer:
            with hou.InterruptableOperation(
                "Rendering", "Performing Tasks", open_interrupt_dialog=True
            ):
                val = self.save_node_octane(node, asset_id, update)
        elif "MaterialX" in self._renderer:
                if node.type().name() == "collect":
                    val = self.save_node_collect(node, asset_id, update)
                else:
                    val = self.save_node_mtlx(node, asset_id, update)
        else:
            hou.ui.displayMessage("Selected Node is not a Material Builder")  # type: ignore
        return val

    def save_node_collect(self, node: hou.Node, asset_id: str, update: bool) -> bool:
        """Saves the attached network from a collect node to disk - does not add to library"""
        # Filepath where to save stuff
        file_name = (
            self._preferences.dir
            + self._preferences.asset_dir
            + str(asset_id)
            + self._preferences.ext
        )
        parms_file_name = (
            self._preferences.dir
            + self._preferences.asset_dir
            + str(asset_id)
            + ".interface"
        )

        nodetree = helpers.get_connected_nodes(node)

        sub_tmp = nodetree[0].parent().createNode("subnet")
        children = sub_tmp.children()
        for n in children:
            n.destroy()
        hou.copyNodesTo((nodetree), sub_tmp)  # type: ignore
        children = sub_tmp.children()

        interface_file = open(parms_file_name, "w", encoding="utf-8")
        interface_file.write(sub_tmp.asCode())

        sub_tmp.saveItemsToFile(children, file_name, save_hda_fallbacks=False)
        sub_tmp.destroy()

        # If this is not a manual update and render_on_import is off, finish here
        if not update:
            if not self._preferences.render_on_import:
                return True

        thumber = thumbs.ThumbNailRenderer(self._preferences)
        return thumber.create_thumb_mtlx(nodetree, asset_id)

    def save_node_mtlx(self, node: hou.Node, asset_id: str, update: bool) -> bool:
        """Saves the MtlX node to disk - does not add to library"""
        # Filepath where to save stuff
        file_name = (
            self._preferences.dir
            + self._preferences.asset_dir
            + asset_id
            + self._preferences.ext
        )

        parms_file_name = (
            self._preferences.dir
            + self._preferences.asset_dir
            + asset_id
            + ".interface"
        )

        children = node.children()

        interface_file = open(parms_file_name, "w", encoding="utf-8")
        interface_file.write(node.asCode())

        node.saveItemsToFile(children, file_name, save_hda_fallbacks=False)

        if "subnet" in node.type().name():
            children = [node]

        # If this is not a manual update and render_on_import is off, finish here
        if not update:
            if not self._preferences.render_on_import:
                return True

        thumber = thumbs.ThumbNailRenderer(self._preferences)
        return thumber.create_thumb_mtlx(children, asset_id)

    def save_node_mantra(self, node: hou.Node, asset_id: str, update: bool) -> bool:
        """Saves the Mantra node to disk - does not add to library"""
        # Filepath where to save stuff
        file_name = (
            self._preferences.dir
            + self._preferences.asset_dir
            + str(asset_id)
            + self._preferences.ext
        )

        origNode = node
        builder = ""
        if node.type().name() != "materialbuilder":
            builder = hou.node("/mat").createNode("materialbuilder")
            for c in builder.children():
                c.destroy()
            hou.copyNodesTo((node,), builder)  # type: ignore
            node = builder

        # interface-stuff
        parms_file_name = (
            self._preferences.dir
            + self._preferences.asset_dir
            + str(asset_id)
            + ".interface"
        )
        children = node.children()

        interface_file = open(parms_file_name, "w", encoding="utf-8")
        interface_file.write(node.asCode())

        node.saveItemsToFile(children, file_name, save_hda_fallbacks=False)

        node = origNode
        if builder != "":
            builder.destroy()

        # If this is not a manual update and render_on_import is off, finish here
        if not update:
            if not self._preferences.render_on_import:
                return True

        thumber = thumbs.ThumbNailRenderer(self._preferences)
        return thumber.create_thumb_mantra(node, asset_id)

    def save_node_redshift(self, node: hou.Node, asset_id: str, update: bool) -> bool:
        """Saves the Redshift node to disk - does not add to library"""
        # Filepath where to save stuff
        file_name = (
            self._preferences.dir
            + self._preferences.asset_dir
            + str(asset_id)
            + self._preferences.ext
        )

        # interface-stuff
        parms_file_name = (
            self._preferences.dir
            + self._preferences.asset_dir
            + str(asset_id)
            + ".interface"
        )
        children = node.children()

        interface_file = open(parms_file_name, "w", encoding="utf-8")
        # interface_file.write(node.parmTemplateGroup().asCode())
        interface_file.write(node.asCode())

        node.saveItemsToFile(children, file_name, save_hda_fallbacks=False)

        # If this is not a manual update and render_on_import is off, finish here
        if not update:
            if not self._preferences.render_on_import:
                return True

        # Create Thumbnail
        sc = thumbnail_scene.ThumbNailScene()
        sc.setup("Redshift")
        thumb = sc.get_node()
        thumb.parm("mat").set(node.path())

        # Build path
        path = (
            self._preferences.dir
            + self._preferences.img_dir
            + str(asset_id)
            + self._preferences.img_ext
        )

        #  Set Rendersettings and Object Exclusions for Thumbnail Rendering
        thumb.parm("path").set(path)
        exclude = "* ^" + thumb.name()
        thumb.parm("obj_exclude").set(exclude)
        lights = thumb.name() + "/*"
        thumb.parm("lights").set(lights)
        thumb.parm("resx").set(self.rendersize)
        thumb.parm("resy").set(self.rendersize)

        # Render Frame
        thumb.parm("execute").pressButton()
        # CleanUp
        thumb.destroy()
        return True

    def save_node_octane(self, node: hou.Node, asset_id: str, update: bool) -> bool:
        # Filepath where to save stuff
        file_name = (
            self._preferences.dir
            + self._preferences.asset_dir
            + str(asset_id)
            + self._preferences.ext
        )

        # interface-stuff
        parms_file_name = (
            self._preferences.dir
            + self._preferences.asset_dir
            + str(asset_id)
            + ".interface"
        )
        children = node.children()

        interface_file = open(parms_file_name, "w", encoding="utf-8")
        # interface_file.write(node.parmTemplateGroup().asCode())
        interface_file.write(node.asCode())

        node.saveItemsToFile(children, file_name, save_hda_fallbacks=False)

        # If this is not a manual update and render_on_import is off, finish here
        if not update:
            if not self._preferences.render_on_import:
                return True

        # Create Thumbnail
        sc = thumbnail_scene.ThumbNailScene()
        sc.setup("Octane")
        thumb = sc.get_node()
        thumb.parm("mat").set(node.path())
        # Build path
        path = (
            self._preferences.dir
            + self._preferences.img_dir
            + str(asset_id)
            + self._preferences.img_ext
        )

        # Set Rendersettings and Object Exclusions for Thumbnail Rendering
        thumb.parm("path").set(path)
        exclude = "* ^" + thumb.name()
        thumb.parm("obj_exclude").set(exclude)
        lights = thumb.name() + "/*"
        thumb.parm("lights").set(lights)
        thumb.parm("resx").set(self.rendersize)
        thumb.parm("resy").set(self.rendersize)

        # Render Frame
        thumb.parm("render").pressButton()

        # CleanUp
        thumb.destroy()
        return True

    def save_node_arnold(
        self, node: hou.Node, asset_id: str, update: bool
    ) -> bool:  # ARNOLD
        """Saves the Arnold node to disk - does not add to library"""
        # Filepath where to save stuff
        file_name = (
            self._preferences.dir
            + self._preferences.asset_dir
            + str(asset_id)
            + self._preferences.ext
        )

        # interface-stuff
        parms_file_name = (
            self._preferences.dir
            + self._preferences.asset_dir
            + str(asset_id)
            + ".interface"
        )
        children = node.children()

        interface_file = open(parms_file_name, "w", encoding="utf-8")
        interface_file.write(node.asCode())

        node.saveItemsToFile(children, file_name, save_hda_fallbacks=False)

        # If this is not a manual update and render_on_import is off, finish here
        if not update:
            if not self._preferences.render_on_import:
                return True

        # Create Thumbnail
        sc = thumbnail_scene.ThumbNailScene()
        sc.setup("Arnold")
        thumb = sc.get_node()
        thumb.parm("mat").set(node.path())

        # Build path
        path = self._preferences.dir + self._preferences.img_dir + str(asset_id)

        #  Set Rendersettings and Object Exclusions for Thumbnail Rendering
        thumb.parm("path").set(path + ".exr")
        thumb.parm("cop_out_img").set(path + self._preferences.img_ext)

        exclude = "* ^" + thumb.name()
        thumb.parm("obj_exclude").set(exclude)
        lights = thumb.name() + "/*"
        thumb.parm("lights").set(lights)
        thumb.parm("resx").set(self.rendersize)
        thumb.parm("resy").set(self.rendersize)
        thumb.parm("render").pressButton()

        # WaitForRender - A really bad hack
        done_path = hou.getenv("EGMATLIB") + "/lib/done.txt"
        mustend = time.time() + 60.0
        while time.time() < mustend:
            if os.path.exists(done_path):
                os.remove(done_path)
                time.sleep(2)
                break
            time.sleep(1)

        thumb.destroy()
        if os.path.exists(path + ".exr"):
            os.remove(path + ".exr")

        return True
