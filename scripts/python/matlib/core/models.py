import os
import uuid
import datetime
import time
import importlib

from PySide6 import QtCore, QtGui
from typing import Any

import hou

from matlib.helpers import helpers
from matlib.render import thumbnail_scene
from matlib.core import material, database


from matlib.prefs import prefs

importlib.reload(material)
importlib.reload(helpers)
importlib.reload(thumbnail_scene)
importlib.reload(database)


class Categories(QtCore.QAbstractListModel):
    def __init__(self, parent: QtCore.QObject | None = None) -> None:
        super().__init__()

        perferences = prefs.Prefs()
        db = database.DatabaseConnector()
        data = db.load(perferences.dir)
        self._categories = data["categories"]

    def rowCount(
        self, parent: QtCore.QModelIndex | QtCore.QPersistentModelIndex = ...
    ) -> int:
        return len(self._categories)

    def data(
        self, index: QtCore.QModelIndex | QtCore.QPersistentModelIndex, role: int = 0
    ) -> Any:
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return self._categories[index.row()]


class MaterialLibrary(QtCore.QAbstractListModel):

    def __init__(self, parent: QtCore.QObject | None = None) -> None:
        super().__init__()
        self._assets = []
        self._categories = [""]
        self._tags = [""]
        self.settings = {}
        self._path = ""
        self._thumbsize = -1
        self._rendersize = -1
        self._render_on_import = False

        self._context: hou.Node = hou.node("/stage")

        # Open Db Connection
        perferences = prefs.Prefs()
        self.settings = perferences  # TODO Remove Future
        db = database.DatabaseConnector()
        data = db.load(perferences.dir)

        self._path = perferences.dir
        # Map to Model
        self._assets = [material.Material.from_dict(d) for d in data["assets"]]
        self._categories = data["categories"]
        self._tags = data["tags"]
        self.thumbsize = data["thumbsize"]
        self.rendersize = data["rendersize"]
        self.render_on_import = data["render_on_import"]

        self.IdRole = QtCore.Qt.ItemDataRole.UserRole
        self.CategoryRole = QtCore.Qt.ItemDataRole.UserRole + 1
        self.FavoriteRole = QtCore.Qt.ItemDataRole.UserRole + 2
        self.RendererRole = QtCore.Qt.ItemDataRole.UserRole + 3
        self.TagRole = QtCore.Qt.ItemDataRole.UserRole + 4
        self.DateRole = QtCore.Qt.ItemDataRole.UserRole + 5

        self.default_image = QtGui.QImage(
            "/Users/elmar/git/egMatLib/scripts/python/matlib/res/img/default.png"
        ).scaled(QtCore.QSize(256, 256))

    # def roleNames(self) -> QtCore.Dict[int, QtCore.QByteArray]:
    #     return {self.IdRole: b"id", self.CategoryRole: b"Category"}

    def setCustomIconSize(self, size) -> None:
        self.default_image = QtGui.QPixmap.fromImage(
            QtGui.QImage(
                "/Users/elmar/git/egMatLib/scripts/python/matlib/res/img/default.png"
            ).scaled(size)
        )

    def rowCount(
        self, parent: QtCore.QModelIndex | QtCore.QPersistentModelIndex = ...
    ) -> int:
        return len(self._assets)

    def data(
        self, index: QtCore.QModelIndex | QtCore.QPersistentModelIndex, role: int = 0
    ) -> Any:
        # if self._assets[index.row()].mat_id == "-1":
        #     return None
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return self._assets[index.row()].name

        if role == QtCore.Qt.ItemDataRole.DecorationRole:
            # if index.row() < 0:
            #     return None
            # mat_id = self._assets[index.row()].mat_id
            # path = self.path + self.settings.img_dir + mat_id + self.settings.img_ext
            # if os.path.exists(path):
            #     return QtGui.QImage(path)

            return self.default_image

        if role == self.CategoryRole:
            return self._assets[index.row()].categories

        if role == self.TagRole:
            return self._assets[index.row()].tags

        if role == self.FavoriteRole:
            return str(self._assets[index.row()].fav)

        if role == self.RendererRole:
            return str(self._assets[index.row()].renderer)

        if role == self.DateRole:
            return str(self._assets[index.row()].date)

        if role == self.IdRole:
            return str(self._assets[index.row()].mat_id)

    def save(self) -> None:
        """Save data to disk as json"""
        db = database.DatabaseConnector()
        db.save()

    def check_exists_in_lib(self, path: str) -> bool:
        return any(asset.path == path for asset in self._assets)

    def run_dir(self, path: str, entries: list) -> list[str]:
        for file in os.listdir(path):
            if os.path.isdir(os.path.join(path, file)):
                self.run_dir(os.path.join(path, file), entries)
            else:
                if file.endswith(".usd"):
                    usd_file = os.path.join(path, file)
                    entries.append(usd_file)
        return entries

    @property
    def path(self) -> str:
        return self._path

    @path.setter
    def path(self, path: str) -> None:
        self._path = path

    @property
    def assets(self) -> list:
        return self._assets

    @property
    def categories(self) -> list:
        return self._categories

    @property
    def tags(self) -> list:
        return self._tags

    @property
    def thumbsize(self) -> int:
        return self._thumbsize

    @thumbsize.setter
    def thumbsize(self, val: int) -> None:
        self._thumbsize = val

    @property
    def rendersize(self) -> int:
        return self._rendersize

    @rendersize.setter
    def rendersize(self, val: int) -> None:
        self._rendersize = val

    @property
    def context(self) -> hou.Node:
        return self._context

    @context.setter
    def context(self, context: hou.Node) -> None:
        self._context = context

    @property
    def render_on_import(self) -> bool:
        return self._render_on_import

    @render_on_import.setter
    def render_on_import(self, val: bool) -> None:
        self._render_on_import = val

    def set_asset_name_by_id(self, asset_id: str, name: str) -> None:
        """Sets the Name for the given Asset (asset_id)"""
        asset = self.get_asset_by_id(asset_id)
        asset.name = name

    def get_asset_by_id(self, asset_id: str) -> None | material.Material:
        """Returns the Asset for the given id"""
        for asset in self._assets:
            if str(asset_id) == str(asset.mat_id):
                return asset
        return None

    def set_asset_cat(self, asset_id: str, cat: str) -> None:
        """Sets the category for the given material (asset_id)"""
        self.check_add_category(cat)
        asset = self.get_asset_by_id(asset_id)
        asset.set_categories(cat)

    def set_asset_tag(self, asset_id: str, tag: str) -> None:
        """Sets the tag for the given material (asset_id)"""
        asset = self.get_asset_by_id(asset_id)
        asset.set_tags(tag)

    def set_asset_fav(self, asset_id: str, fav: bool) -> None:
        """Sets the fav for the given material (asset_id)"""
        asset = self.get_asset_by_id(asset_id)
        asset.fav = fav

    def get_asset_fav(self, asset_id: str) -> bool:
        """Gets the fav for the given material (asset_id) as 0/1"""
        asset = self.get_asset_by_id(asset_id)
        return asset.fav

    def update_asset_date(self, asset_id: str) -> None:
        asset = self.get_asset_by_id(asset_id)
        asset.set_date()

    def remove_asset(self, asset_id: str) -> None:
        """Removes a material from this Library and Disk"""
        for asset in self._assets:
            if asset_id == asset.mat_id:
                self._assets.remove(asset)

                # Remove Files from Disk
                asset_file_path = os.path.join(
                    self.path,
                    self.settings.asset_dir,
                    str(asset_id) + self.settings.ext,
                )
                img_file_path = os.path.join(
                    self.path,
                    self.settings.img_dir,
                    str(asset_id) + self.settings.img_ext,
                )
                interface_file_path = os.path.join(
                    self.path,
                    self.settings.asset_dir,
                    str(asset_id) + ".interface",
                )

                if os.path.exists(asset_file_path):
                    os.remove(asset_file_path)
                if os.path.exists(img_file_path):
                    os.remove(img_file_path)
                if os.path.exists(interface_file_path):
                    os.remove(interface_file_path)

                self.save()
                return

    def check_add_category(self, cat: str) -> None:
        """Checks if this category exists and adds it if needed"""
        for c in cat.split(","):
            c = c.replace(" ", "")
            if c != "" and c not in self._categories:
                self._categories.append(c)
        self.save()

    def check_add_tags(self, tag: str) -> None:
        """Checks if this tag exists and adds it if needed"""
        for t in tag.split(","):
            t = t.replace(" ", "")
            if t != "" and t not in self.tags:
                self.tags.append(t)
        self.save()

    def get_current_network_node(self) -> None | hou.Node:
        """Return thre current Node in the Network Editor"""
        for pt in hou.ui.paneTabs():  # type: ignore
            if pt.type() == hou.paneTabType.NetworkEditor:
                return pt.currentNode()
        return None

    def remove_category(self, cat: str) -> None:
        """Removes the given category from the library (and also in all assets)"""
        self._categories.remove(cat)
        # check assets against category and remove there also:
        for asset in self._assets:
            asset.remove_category(cat)

    def rename_category(self, old: str, new: str) -> None:
        """Renames the given category in the library (and also in all assets)"""
        # Update Categories with that name
        for count, current in enumerate(self._categories):
            if current == old:
                self._categories[count] = new
        # Update all Categories with that name in all assets
        for asset in self._assets:
            asset.rename_category(old, new)

    def add_asset(
        self, node: hou.Node, cat: str, tag: str, fav: bool, use_usd: int = 0
    ) -> None:
        """Add a Material to this Library"""
        node_id = str(uuid.uuid1().time)
        if self.save_node(node, node_id, False):
            # Format
            name = node.name()
            name.replace(" ", "")

            cats = cat.split(",")
            for c in cats:
                c.replace(" ", "")

            tags = tag.split(",")
            for t in tags:
                t.replace(" ", "")

            renderer = ""
            builder = 0
            if node.type().name() == "redshift_vopnet":
                renderer = "Redshift"
                builder = 1
            if node.type().name() == "octane_vopnet":
                renderer = "Octane"
                builder = 1
            elif node.type().name() == "materialbuilder":
                renderer = "Mantra"
                builder = 1
            elif node.type().name() == "principledshader::2.0":
                renderer = "Mantra"
                builder = 0
            elif node.type().name() == "arnold_materialbuilder":
                renderer = "Arnold"
                builder = 1
            elif node.type().name() == "subnet":
                for n in node.children():
                    if "mtlx" in n.type().name():
                        renderer = "MatX"
                        builder = 0
            elif node.type().name() == "collect":
                renderer = "MatX"
                builder = 0

            date = str(datetime.datetime.now())
            date = date[:-7]

            mat = {
                "id": node_id,
                "name": name,
                "categories": cats,
                "tags": tags,
                "favorite": fav,
                "renderer": renderer,
                "date": date,
                "builder": builder,
                "usd": use_usd,
            }
            new_mat = material.Material.from_dict(mat)
            self._assets.append(new_mat)
            self.save()

    def get_renderer_by_id(self, asset_id: str) -> str:
        """Return the Renderer for this Material as a string"""
        for mat in self._assets:
            if isinstance(asset_id, int):
                if int(asset_id) == mat.mat_id:
                    return mat.renderer
            else:
                if asset_id == mat.mat_id:
                    return mat.renderer
        return ""

    def check_materialbuilder_by_id(self, asset_id: str) -> int | None:
        """Return if the Material is a Builder (Mantra) as a 0/1"""
        for mat in self._assets:
            if isinstance(asset_id, int):
                if int(asset_id) == mat.mat_id:
                    return mat.builder
            else:
                if asset_id == mat.mat_id:
                    return mat.builder
        return None

    def update_context(self) -> None:
        self.context = self.get_current_network_node()

    def import_asset_to_scene(self, index: QtCore.QModelIndex) -> None | hou.Node:
        """Import a Material to the Nework Editor/Scene"""
        mat = self._assets[index.row()]
        file_name = (
            self._path + self.settings.asset_dir + mat.mat_id + self.settings.ext
        )

        import_path = None

        # This checks if USD has been selected in the panel and imports accordingly
        if self.context == hou.node("/stage"):
            import_path = self.context.createNode("materiallibrary")
        elif self.context.path() == "/mat":
            import_path = hou.node("/mat")
            # override if Material was saved in USD Mode
            if mat.usd:
                import_path = hou.node("/stage").createNode("materiallibrary")
        else:
            # Radio is set to Current Network
            parent = self.get_current_network_node().parent()
            # If Stage or LOPnet
            if parent.type().name() == "stage" or parent.type().name() == "lopnet":
                import_path = parent.createNode("materiallibrary")
            elif parent.type().name() == "materiallibrary":
                import_path = parent
            # If oldschool matbuilder or matbld in lops
            elif parent.type().name() == "materialbuilder":
                if "stage" in parent.path() or "lopnet" in parent.path():
                    import_path = parent
                else:
                    import_path = parent
                    # override if Material was saved in USD Mode
                    if mat.usd:
                        import_path = hou.node("/stage").createNode("materiallibrary")
            elif parent.type().name() == "matnet":
                import_path = parent
            elif parent.type().name() == "mat":
                import_path = hou.node("/mat")
            elif parent.type().name() == "obj":
                if self.get_current_network_node().type().name() != "matnet":
                    import_path = self.get_current_network_node().createNode("matnet")
            elif parent.path() == "/":
                import_path = hou.node("/obj").createNode("matnet")
            else:
                import_path = parent.createNode("matnet")
                # override if Material was saved in USD Mode
                if mat.usd:
                    import_path = hou.node("/stage").createNode("materiallibrary")

        parms_file_name = (
            self._path + self.settings.asset_dir + str(mat.mat_id) + ".interface"
        )

        # Create temporary storage of nodes
        tmp_matnet = hou.node("obj").createNode("matnet")
        hou_parent = tmp_matnet  # needed for the code script below

        builder = None

        if mat.renderer == "Redshift":
            # Interface Check
            if os.path.exists(parms_file_name):
                interface_file = open(parms_file_name, "r", encoding="utf-8")
                code = interface_file.read()
                exec(code)

                builder = hou_parent.children()[0]

            else:
                builder = hou.node(import_path).createNode("redshift_vopnet")

            builder.setName(mat.name, unique_name=True)
            builder.setGenericFlag(hou.nodeFlag.Material, True)
            # Delete Default children in RS-VopNet
            for node in builder.children():
                node.destroy()

        elif mat.renderer == "Octane":
            # Interface Check
            if os.path.exists(parms_file_name):
                interface_file = open(parms_file_name, "r", encoding="utf-8")
                code = interface_file.read()
                exec(code)

                builder = hou_parent.children()[0]

            else:
                builder = hou.node(import_path).createNode("octane_vopnet")

            builder.setName(mat.name, unique_name=True)
            builder.setGenericFlag(hou.nodeFlag.Material, True)
            # Delete Default children in Octane-VopNet
            for node in builder.children():
                node.destroy()

        elif mat.renderer == "Mantra":
            # Interface Check
            if os.path.exists(parms_file_name):
                # Only load parms if MatBuilder
                if self.check_materialbuilder_by_id(mat.mat_id):
                    interface_file = open(parms_file_name, "r", encoding="utf-8")
                    code = interface_file.read()
                    exec(code)

                    builder = hou.selectedNodes()[0]
                # Selection will be empty if not a MaterialBuilder
                else:
                    builder = import_path.createNode("materialbuilder")
            else:
                builder = hou.node(import_path).createNode("materialbuilder")

            builder.setName(mat.name, unique_name=True)
            builder.setGenericFlag(hou.nodeFlag.Material, True)
            # Delete Default children in MaterialBuilder
            for node in builder.children():
                node.destroy()

        elif mat.renderer == "Arnold":
            # CreateBuilder
            # Interface Check
            if os.path.exists(parms_file_name):
                interface_file = open(parms_file_name, "r", encoding="utf-8")
                code = interface_file.read()
                exec(code)

                builder = hou_parent.children()[0]
            else:
                builder = hou.node(import_path).createNode("arnold_materialbuilder")

            builder.setName(mat.name, unique_name=True)
            builder.setGenericFlag(hou.nodeFlag.Material, True)
            # Delete Default children in Arnold MaterialBuilder
            for node in builder.children():
                node.destroy()

        elif mat.renderer == "MaterialX":
            if os.path.exists(parms_file_name):
                interface_file = open(parms_file_name, "r", encoding="utf-8")
                code = interface_file.read()
                exec(code)
                builder = import_path.createNode("subnet")
                builder.setName(mat.name, unique_name=True)
                builder.setGenericFlag(hou.nodeFlag.Material, True)
                for n in builder.children():
                    n.destroy()
            else:
                return
        # Import file from disk
        try:
            builder.loadItemsFromFile(file_name, ignore_load_warnings=False)
        except OSError:
            hou.ui.displayMessage("Failure on Import. Please Try again.")  # type: ignore
            return None

        # If node is Principled Shader
        if mat.renderer == "Mantra" and not self.check_materialbuilder_by_id(
            mat.mat_id
        ):
            n = builder.children()[0]
            hou.moveNodesTo((n,), builder.parent())  # type: ignore
            builder.destroy()
            builder = hou.selectedNodes()[0]
        else:
            new_mat = hou.moveNodesTo((builder,), import_path)  # type: ignore
            new_mat[0].moveToGoodPosition()
            builder = new_mat[0]

        # Cleanup
        tmp_matnet.destroy()

        if import_path.type().name() == "materiallibrary":
            import_path.parm("materials").set(0)
            import_path.parm("fillmaterials").pressButton()
            i = 0
            while i < import_path.parm("materials").evalAsInt():
                import_path.parm("".join(["assign", str(i + 1)])).set(0)
                i += 1

        return builder

    def save_node(self, node: hou.Node, asset_id: str, update: bool) -> bool:
        """Save Node wrapper for different Material Types"""
        # Check against NodeType
        val = False
        if node.type().name() == "redshift_vopnet":
            # Interruptable
            with hou.InterruptableOperation(
                "Rendering", "Performing Tasks", open_interrupt_dialog=True
            ):
                val = self.save_node_redshift(node, asset_id, update)
        elif (
            node.type().name() == "materialbuilder"
            or node.type().name() == "principledshader::2.0"
        ):
            # Interruptable
            if hou.getenv("OCIO") is None:
                hou.ui.displayMessage("Please set $OCIO first")  # type: ignore
                return False
            with hou.InterruptableOperation(
                "Rendering", "Performing Tasks", open_interrupt_dialog=True
            ):
                val = self.save_node_mantra(node, asset_id, update)
        elif node.type().name() == "arnold_materialbuilder":
            if hou.getenv("OCIO") is None:
                hou.ui.displayMessage("Please set $OCIO first")  # type: ignore
                return False
            with hou.InterruptableOperation(
                "Rendering", "Performing Tasks", open_interrupt_dialog=True
            ):
                val = self.save_node_arnold(node, asset_id, update)
        elif node.type().name() == "octane_vopnet":
            if hou.getenv("OCIO") is None:
                hou.ui.displayMessage("Please set $OCIO first")  # type: ignore
                return False
            with hou.InterruptableOperation(
                "Rendering", "Performing Tasks", open_interrupt_dialog=True
            ):
                val = self.save_node_octane(node, asset_id, update)
        elif node.type().name() == "subnet":
            # Hope for the best that it actually is a MtlX Subnet
            if hou.getenv("OCIO") is None:
                hou.ui.displayMessage("Please set $OCIO first")  # type: ignore
                return False
            with hou.InterruptableOperation(
                "Rendering", "Performing Tasks", open_interrupt_dialog=True
            ):
                val = self.save_node_mtlx(node, asset_id, update)
        elif node.type().name() == "collect":
            if hou.getenv("OCIO") is None:
                hou.ui.displayMessage("Please set $OCIO first")  # type: ignore
                return False
            with hou.InterruptableOperation(
                "Rendering", "Performing Tasks", open_interrupt_dialog=True
            ):
                val = self.save_node_collect(node, asset_id, update)
        else:
            hou.ui.displayMessage("Selected Node is not a Material Builder")  # type: ignore
        return val

    def save_node_collect(self, node: hou.Node, asset_id: str, update: bool) -> bool:
        """Saves the attached network from a collect node to disk - does not add to library"""
        # Filepath where to save stuff
        file_name = (
            self.path + self.settings.asset_dir + str(asset_id) + self.settings.ext
        )
        parms_file_name = (
            self.path + self.settings.asset_dir + str(asset_id) + ".interface"
        )

        nodetree = helpers.getConnectedNodes(node)

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
            if not self.render_on_import:
                return True

        return self.create_thumb_mtlx(nodetree, asset_id)

    def save_node_mtlx(self, node: hou.Node, asset_id: str, update: bool) -> bool:
        """Saves the MtlX node to disk - does not add to library"""
        # Filepath where to save stuff
        file_name = (
            self.path + self.settings.asset_dir + str(asset_id) + self.settings.ext
        )

        # interface-stuff
        parms_file_name = (
            self.path + self.settings.asset_dir + str(asset_id) + ".interface"
        )

        children = node.children()

        interface_file = open(parms_file_name, "w", encoding="utf-8")
        interface_file.write(node.asCode())

        node.saveItemsToFile(children, file_name, save_hda_fallbacks=False)

        if "subnet" in node.type().name():
            children = [node]

        # If this is not a manual update and render_on_import is off, finish here
        if not update:
            if not self.render_on_import:
                return True

        return self.create_thumb_mtlx(children, asset_id)

    def create_thumbnail(self, node: hou.Node, asset_id: str) -> None:
        renderer = self.get_renderer_by_id(asset_id)
        if renderer == "MatX":
            self.create_thumb_mtlx(node.children(), asset_id)
        elif renderer == "Mantra":
            self.create_thumb_mantra(node, asset_id)
        else:
            pass

    def create_thumb_mtlx(self, children: list[hou.Node], asset_id: str) -> bool:
        # Build path
        path = self.path + self.settings.img_dir + str(asset_id) + ".exr"

        # Create Thumbnail
        net = hou.node("/obj").createNode("lopnet")

        ref = net.createNode("reference::2.0")
        ref.parm("filepath1").set(
            hou.getenv("EGMATLIB")
            + "/scripts/python/matlib/res/usd/shaderBallScene.usd"
        )

        lib1 = net.createNode("materiallibrary")
        lib1.setFirstInput(ref)
        surf = lib1.createNode("mtlxstandard_surface")
        tex = lib1.createNode("mtlxtiledimage")
        tex.parm("file").set("color3")
        tex.parm("file").set("$EGMATLIB/scripts/python/matlib/res/img/FloorTexture.rat")
        surf.setInput(1, tex, 0)
        surf.setGenericFlag(hou.nodeFlag.Material, True)
        lib1.parm("materials").set(1)
        lib1.parm("matnode1").set("mtlxstandard_surface1")
        lib1.parm("matpath1").set("/thumb/bg_material")
        lib1.parm("geopath1").set("/shaderBallScene/geo/plane/mesh_0")
        lib1.parm("assign1").set(1)

        lib = net.createNode("materiallibrary")
        lib.setFirstInput(lib1)

        nodes = hou.copyNodesTo((children), lib)  # type: ignore
        collect = 0
        for n in nodes:
            if n.type().name() == "collect":
                n.setGenericFlag(hou.nodeFlag.Material, True)
                collect = 1
            for p in n.parms():
                if "_activate_" in p.name():
                    p.set(1)

        if not collect:
            for n in nodes:
                if n.type().name() == "mtlxstandard_surface":
                    n.setGenericFlag(hou.nodeFlag.Material, True)
                    break
                elif "subnet" in n.type().name():
                    n.setGenericFlag(hou.nodeFlag.Material, True)
                    break

        lib.parm("fillmaterials").pressButton()
        lib.parm("assign1").set(1)
        lib.parm("geopath1").set("/shaderBallScene/geo/ball/mesh_0")

        settings = net.createNode("karmarenderproperties")
        settings.parm("camera").set("/shaderBallScene/cameras/RenderCam")
        settings.parm("res_mode").set("manual")
        settings.parm("res_mode").pressButton()
        settings.parm("resolutionx").set(self.rendersize)
        settings.parm("resolutiony").deleteAllKeyframes()
        settings.parm("resolutiony").set(self.rendersize)
        settings.parm("engine").set("xpu")
        settings.parm("engine").pressButton()
        settings.parm("pathtracedsamples").set(256)
        settings.parm("enabledof").set(0)
        settings.parm("enablemblur").set(0)
        settings.parm("picture").set(path)
        settings.setFirstInput(lib)

        rop = net.createNode("usdrender_rop")
        rop.parm("renderer").set("BRAY_HdKarmaXPU")  # KarmaXPU
        rop.setFirstInput(settings)
        rop.parm("soho_foreground").set(1)
        rop.parm("execute").pressButton()

        # Copnet Setup
        copnet = rop.parent().createNode("cop2net")
        copnet.setName("exr_to_png")

        cop_file = copnet.createNode("file")

        cop_file.parm("nodename").set(0)
        cop_file.parm("overridedepth").set(2)
        cop_file.parm("depth").set(4)
        cop_file.parm("filename1").set(path)

        cop_out = copnet.createNode("rop_comp")

        aces_1_3 = False
        cop_file.parm("colorspace").set(3)  # OCIO

        if "v1.3" in hou.getenv("OCIO").lower():
            aces_1_3 = True
        else:
            for item in cop_file.parm("ocio_space").menuItems():
                if "encoded" in item.lower():
                    aces_1_3 = True

        # ACES 1.3
        if aces_1_3:
            cop_file.parm("colorspace").set(3)  # OCIO
            cop_file.parm("ocio_space").set("ACEScg")

            cop_out.setInput(0, cop_file)
            cop_out.parm("convertcolorspace").set(3)
            cop_out.parm("ocio_display").set("sRGB - Display")
            cop_out.parm("ocio_view").set("ACES 1.0 - SDR Video")

        else:
            # ACES 1.2
            # Vopnet
            cop_file.parm("colorspace").set(0)
            cop_vop = copnet.createNode("vopcop2filter")
            gn = cop_vop.node("global1")
            o = cop_vop.node("output1")
            ftv = cop_vop.createNode("floattovec")
            ocio = cop_vop.createNode("ocio_transform")
            vtf = cop_vop.createNode("vectofloat")

            o.setInput(0, vtf, 0)
            o.setInput(1, vtf, 1)
            o.setInput(2, vtf, 2)
            o.setInput(3, gn, 6)

            vtf.setInput(0, ocio, 0)

            ocio.setInput(0, ftv, 0)

            ocio.parm("fromspace").set("ACES - ACEScg")
            ocio.parm("tospace").set("Output - sRGB")

            ftv.setInput(0, gn, 3)
            ftv.setInput(1, gn, 4)
            ftv.setInput(2, gn, 5)

            cop_out.parm("convertcolorspace").set(0)
            cop_out.parm("gamma").set(1)

            cop_vop.setInput(0, cop_file)
            cop_out.setInput(0, cop_vop)

        newpath = (
            self.path + self.settings.img_dir + str(asset_id) + self.settings.img_ext
        )

        cop_out.parm("copoutput").set(newpath)
        cop_out.parm("execute").pressButton()

        net.destroy()

        if os.path.exists(path):
            os.remove(path)

        return True

    def create_thumb_mantra(self, node: hou.Node, asset_id: str) -> bool:
        # Create Thumbnail

        sc = thumbnail_scene.ThumbNailScene()
        sc.setup("Mantra")
        thumb = sc.get_node()

        thumb.parm("mat").set(node.path())

        # Build path
        path = self.path + self.settings.img_dir + str(asset_id)

        #  Set Rendersettings and Object Exclusions for Thumbnail Rendering
        thumb.parm("path").set(path + ".exr")
        thumb.parm("cop_out_img").set(path + self.settings.img_ext)
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
        if os.path.exists(path + ".exr"):
            os.remove(path + ".exr")
        return True

    def save_node_redshift(self, node: hou.Node, asset_id: str, update: bool) -> bool:
        """Saves the Redshift node to disk - does not add to library"""
        # Filepath where to save stuff
        file_name = (
            self.path + self.settings.asset_dir + str(asset_id) + self.settings.ext
        )

        # interface-stuff
        parms_file_name = (
            self.path + self.settings.asset_dir + str(asset_id) + ".interface"
        )
        children = node.children()

        interface_file = open(parms_file_name, "w", encoding="utf-8")
        # interface_file.write(node.parmTemplateGroup().asCode())
        interface_file.write(node.asCode())

        node.saveItemsToFile(children, file_name, save_hda_fallbacks=False)

        # If this is not a manual update and render_on_import is off, finish here
        if not update:
            if not self.render_on_import:
                return True

        # Create Thumbnail
        sc = thumbnail_scene.ThumbNailScene()
        sc.setup("Redshift")
        thumb = sc.get_node()
        thumb.parm("mat").set(node.path())

        # Build path
        path = self.path + self.settings.img_dir + str(asset_id) + self.settings.img_ext

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
            self.path + self.settings.asset_dir + str(asset_id) + self.settings.ext
        )

        # interface-stuff
        parms_file_name = (
            self.path + self.settings.asset_dir + str(asset_id) + ".interface"
        )
        children = node.children()

        interface_file = open(parms_file_name, "w", encoding="utf-8")
        # interface_file.write(node.parmTemplateGroup().asCode())
        interface_file.write(node.asCode())

        node.saveItemsToFile(children, file_name, save_hda_fallbacks=False)

        # If this is not a manual update and render_on_import is off, finish here
        if not update:
            if not self.render_on_import:
                return True

        # Create Thumbnail
        sc = thumbnail_scene.ThumbNailScene()
        sc.setup("Octane")
        thumb = sc.get_node()
        thumb.parm("mat").set(node.path())
        # Build path
        path = self.path + self.settings.img_dir + str(asset_id) + self.settings.img_ext

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
            self.path + self.settings.asset_dir + str(asset_id) + self.settings.ext
        )

        # interface-stuff
        parms_file_name = (
            self.path + self.settings.asset_dir + str(asset_id) + ".interface"
        )
        children = node.children()

        interface_file = open(parms_file_name, "w", encoding="utf-8")
        interface_file.write(node.asCode())

        node.saveItemsToFile(children, file_name, save_hda_fallbacks=False)

        # If this is not a manual update and render_on_import is off, finish here
        if not update:
            if not self.render_on_import:
                return True

        # Create Thumbnail
        sc = thumbnail_scene.ThumbNailScene()
        sc.setup("Arnold")
        thumb = sc.get_node()
        thumb.parm("mat").set(node.path())

        # Build path
        path = self.path + self.settings.img_dir + str(asset_id)

        #  Set Rendersettings and Object Exclusions for Thumbnail Rendering
        thumb.parm("path").set(path + ".exr")
        thumb.parm("cop_out_img").set(path + self.settings.img_ext)

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

    def save_node_mantra(self, node: hou.Node, asset_id: str, update: bool) -> bool:
        """Saves the Mantra node to disk - does not add to library"""
        # Filepath where to save stuff
        file_name = (
            self.path + self.settings.asset_dir + str(asset_id) + self.settings.ext
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
            self.path + self.settings.asset_dir + str(asset_id) + ".interface"
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
            if not self.render_on_import:
                return True
        self.create_thumb_mantra(node, asset_id)

        return True

    def cleanup_db(self) -> None:

        assets = self._assets
        mark_rmv = 0
        mark_render = 0

        for asset in assets:
            if asset.mat_id > 0:
                interface_path = os.path.join(
                    self.path,
                    self.settings.asset_dir,
                    str(asset.mat_id) + ".interface",
                )
                mat_path = os.path.join(
                    self.path, self.settings.asset_dir, str(asset.mat_id) + ".mat"
                )
                img_path = os.path.join(
                    self.path,
                    self.settings.img_dir,
                    str(asset.mat_id) + self.settings.img_ext,
                )

                # asset_path = asset.path
                if not os.path.exists(interface_path):
                    print("Asset %d missing on disk. Removing.", asset.mat_id)
                    mark_rmv = 1
                    self.library.remove_asset(asset.mat_id)
                if not os.path.exists(mat_path):
                    print("Asset %d missing on disk. Removing.", asset.mat_id)
                    mark_rmv = 1
                    self.library.remove_asset(asset.mat_id)
                if not os.path.exists(img_path):
                    mark_render = 1
                    print(
                        f"Image for Asset { asset.mat_id} missing on disk. Needs Rendering."
                    )

        mats_path = os.path.join(self.path, self.settings.asset_dir)
        mark_lone = 0
        for f in os.listdir(mats_path):
            if f.endswith(".mat") or f.endswith(".interface"):
                split = f.split(".")[0]
                mark_found = 0
                for a in assets:
                    if str(split) in str(a.get_id()):
                        mark_found = 1
                        break
                if not mark_found:
                    print(
                        f"Lonely File at {os.path.join(mats_path, f)} found. Removing from disk"
                    )
                    os.remove(os.path.join(mats_path, f))
                    mark_lone = 1

        if mark_rmv:
            hou.ui.displayMessage(
                "Assets have been cleaned up. See python shell for details"  # type: ignore
            )
        if mark_render:
            hou.ui.displayMessage(
                "Missing images have been found. Rerender thumbs required"  # type: ignore
            )
        if mark_lone:
            hou.ui.displayMessage("Lone files have been found and removed from disk.")  # type: ignore
