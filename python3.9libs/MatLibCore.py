import os

# from debian import c

import helpers
import hou
import json

# import sys

import uuid
import datetime
import time

import thumbNailScene
import Material
import importlib

importlib.reload(Material)
importlib.reload(helpers)
importlib.reload(thumbNailScene)

###################################
########### THE LIBRARY ###########
###################################


class MaterialLibrary:
    def __init__(self):
        self.assets = None
        self.categories = None
        self.tags = None
        self.settings = None
        self.path = None
        # self.USD = False

        self.context = hou.node("/stage")

    def load(self, path, prefs):
        self.path = path
        with open(self.path + ("/library.json")) as lib_json:
            self.data = json.load(lib_json)

            asset_data = self.data["assets"]
            self.assets = []
            for data in asset_data:
                new_asset = Material.Material.from_dict(data)
                self.assets.append(new_asset)

            self.categories = self.data["categories"]
            self.tags = self.data["tags"]
            self.thumbsize = self.data["thumbsize"]
            self.rendersize = self.data["rendersize"]
            self.renderOnImport = self.data["renderOnImport"]

        self.settings = prefs
        return

    def save(self):
        # Update actual config
        asset_list = []
        for curr_asset in self.assets:
            asset_list.append(curr_asset.get_as_dict())

        self.data["assets"] = asset_list
        self.data["categories"] = self.categories
        self.data["tags"] = self.tags
        self.data["thumbsize"] = self.thumbsize
        self.data["rendersize"] = self.rendersize
        self.data["renderOnImport"] = self.renderOnImport

        with open(self.path + ("/library.json"), "w") as lib_json:
            json.dump(self.data, lib_json, indent=4)
        return

    def check_exists_in_lib(self, path):
        for asset in self.assets:
            if asset.get_path() == path:
                return True
        return False

    def run_dir(self, path, entries):
        for file in os.listdir(path):
            if os.path.isdir(os.path.join(path, file)):
                self.run_dir(os.path.join(path, file), entries)
            else:
                if file.endswith(".usd"):
                    usd_file = os.path.join(path, file)
                    entries.append(usd_file)
        return entries

    def set_context(self, context):
        self.context = context

    def get_path(self):
        return self.path

    def get_assets(self):
        return self.assets

    def get_categories(self):
        return self.categories

    def get_tags(self):
        return self.tags

    def get_thumbSize(self):
        return self.thumbsize

    def set_thumbSize(self, val):
        self.thumbsize = val

    def set_renderSize(self, val):
        self.rendersize = val

    def get_renderSize(self):
        return self.rendersize

    def get_context(self):
        return self.context

    def get_renderOnImport(self):
        return self.renderOnImport

    def set_renderOnImport(self, val):
        self.renderOnImport = val

    def set_asset_name(self, id, name):
        """Sets the Name for the given Asset (id)"""
        asset = self.get_asset_by_id(id)
        asset.set_name(name)

    def get_asset_by_id(self, id):
        """Returns the Asset for the given id"""
        for asset in self.assets:
            if int(id) == asset.get_id():
                return asset
        return None

    def set_asset_cat(self, id, cat):
        """Sets the category for the given material (id)"""
        self.check_add_category(cat)
        asset = self.get_asset_by_id(id)
        asset.set_categories(cat)

    def set_asset_tag(self, id, tag):
        """Sets the tag for the given material (id)"""
        asset = self.get_asset_by_id(id)
        asset.set_tags(tag)

    def set_asset_fav(self, id, fav):
        """Sets the fav for the given material (id)"""
        asset = self.get_asset_by_id(id)
        asset.set_fav(fav)

    def get_asset_fav(self, id):
        """Gets the fav for the given material (id) as 0/1"""
        asset = self.get_asset_by_id(id)
        return asset.get_fav()

    def update_asset_date(self, id):
        asset = self.get_asset_by_id(id)
        asset.set_date()

    def remove_asset(self, id):
        """Removes a material from this Library and Disk"""
        for asset in self.assets:
            if id == asset.get_id():
                self.assets.remove(asset)

                # Remove Files from Disk
                asset_file_path = os.path.join(
                    self.path,
                    self.settings.get_asset_dir(),
                    str(id) + self.settings.get_ext(),
                )
                img_file_path = os.path.join(
                    self.path,
                    self.settings.get_img_dir(),
                    str(id) + self.settings.get_img_ext(),
                )
                interface_file_path = os.path.join(
                    self.path, self.settings.get_asset_dir(), str(id) + ".interface"
                )

                if os.path.exists(asset_file_path):
                    os.remove(asset_file_path)
                if os.path.exists(img_file_path):
                    os.remove(img_file_path)
                if os.path.exists(interface_file_path):
                    os.remove(interface_file_path)

                self.save()
                return

    def check_add_category(self, cat):
        """Checks if this category exists and adds it if needed"""
        cats = cat.split(",")
        for c in cats:
            c = c.replace(" ", "")
            if c != "":
                if c not in self.categories:
                    self.categories.append(c)

    def check_add_tags(self, tags):
        """Checks if this tag exists and adds it if needed"""
        tags = tags.split(",")
        for t in tags:
            t = t.replace(" ", "")
            if t != "":
                if t not in self.tags:
                    self.tags.append(t)

    def get_current_network_node(self):
        """Return thre current Node in the Network Editor"""
        for pt in hou.ui.paneTabs():
            if pt.type() == hou.paneTabType.NetworkEditor:
                return pt.currentNode()
        return None

    def remove_category(self, cat):
        """Removes the given category from the library (and also in all assets)"""
        self.categories.remove(cat)
        # check assets against category and remove there also:
        for asset in self.assets:
            asset.remove_category(cat)
        return

    def rename_category(self, old, new):
        """Renames the given category in the library (and also in all assets)"""
        # Update Categories with that name
        for count, current in enumerate(self.categories):
            if current == old:
                self.categories[count] = new
        # Update all Categories with that name in all assets
        for asset in self.assets:
            asset.rename_category(old, new)

    def add_asset(self, node, cats, tags, fav, use_usd=0):
        """Add a Material to this Library"""
        id = uuid.uuid1().time
        if self.save_node(node, id, False):
            # Format
            name = node.name()
            name.replace(" ", "")

            cats = cats.split(",")
            for c in cats:
                c.replace(" ", "")

            tags = tags.split(",")
            for t in tags:
                t.replace(" ", "")

            renderer = ""
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

            material = {
                "id": id,
                "name": name,
                "categories": cats,
                "tags": tags,
                "favorite": fav,
                "renderer": renderer,
                "date": date,
                "builder": builder,
                "usd": use_usd,
            }

            new_mat = Material.Material.from_dict(material)
            self.assets.append(new_mat)
            self.save()

    def get_renderer_by_id(self, id):
        """Return the Renderer for this Material as a string"""
        for mat in self.assets:
            if int(id) == mat.get_id():
                return mat.get_renderer()
        return None

    def check_materialBuilder_by_id(self, id):
        """Return if the Material is a Builder (Mantra) as a 0/1"""
        for mat in self.assets:
            if int(id) == mat.get_id():
                return mat.get_builder()
        return None

    def update_context(self):
        self.context = self.get_current_network_node()

    def import_asset_to_scene(self, id):
        """Import a Material to the Nework Editor/Scene"""
        file_name = (
            self.get_path()
            + self.settings.get_asset_dir()
            + str(id)
            + self.settings.get_ext()
        )

        mat = self.get_asset_by_id(id)

        renderer = self.get_renderer_by_id(id)
        builder = None

        # Import to current context
        import_path = None
        use_USD = False

        # self.update_context()
        # print(self.context)
        # This checks if USD has been selected in the panel and imports accordingly
        if self.context == hou.node("/stage"):
            import_path = self.context.createNode("materiallibrary")
            use_USD = True
        elif self.context.path() == "/mat":
            import_path = hou.node("/mat")
            # override if Material was saved in USD Mode
            if mat.get_usd():
                import_path = hou.node("/stage").createNode("materiallibrary")
                use_USD = True
        else:
            self.context = self.get_current_network_node()

            # If Stage or LOPnet
            if (
                self.context.type().name() == "stage"
                or self.context.type().name() == "lopnet"
            ):
                import_path = self.context.createNode("materiallibrary")
                use_USD = True
            else:
                self.context = self.get_current_network_node().parent()
                # print("Context updated: " + self.context.name())
                # If materiallibrary in Lopnet/Stage
                if (
                    "stage" in self.context.type().name()
                    or "lopnet" in self.context.type().name()
                ):
                    import_path = self.context.createNode("materiallibrary")
                    use_USD = True

                elif self.context.type().name() == "materiallibrary":
                    import_path = self.context
                    use_USD = True
                # If oldschool matbuilder or matbld in lops
                elif self.context.type().name() == "materialbuilder":
                    if (
                        "stage" in self.context.path()
                        or "lopnet" in self.context.path()
                    ):
                        import_path = self.context
                        use_USD = True
                    else:
                        import_path = self.context.parent()
                        # override if Material was saved in USD Mode
                        if mat.get_usd():
                            import_path = hou.node("/stage").createNode(
                                "materiallibrary"
                            )
                            use_USD = True
                elif self.context.type().name() == "matnet":
                    import_path = self.context
                else:
                    import_path = self.context.createNode("matnet")
                    # override if Material was saved in USD Mode
                    if mat.get_usd():
                        import_path = hou.node("/stage").createNode("materiallibrary")
                        use_USD = True

        parms_file_name = (
            self.get_path() + self.settings.get_asset_dir() + str(id) + ".interface"
        )

        # Create temporary storage of nodes
        tmp_matnet = hou.node("obj").createNode("matnet")
        hou_parent = tmp_matnet  # needed for the code script below

        if renderer == "Redshift":
            # Interface Check
            if os.path.exists(parms_file_name):
                interface_file = open(parms_file_name, "r")
                code = interface_file.read()
                exec(code)

                builder = hou_parent.children()[0]

            else:
                builder = hou.node(import_path).createNode("redshift_vopnet")

            builder.setName(mat.get_name(), unique_name=True)
            builder.setGenericFlag(hou.nodeFlag.Material, True)
            # Delete Default children in RS-VopNet
            for node in builder.children():
                node.destroy()

        elif renderer == "Octane":
            # Interface Check
            if os.path.exists(parms_file_name):
                interface_file = open(parms_file_name, "r")
                code = interface_file.read()
                exec(code)

                builder = hou_parent.children()[0]

            else:
                builder = hou.node(import_path).createNode("octane_vopnet")

            builder.setName(mat.get_name(), unique_name=True)
            builder.setGenericFlag(hou.nodeFlag.Material, True)
            # Delete Default children in Octane-VopNet
            for node in builder.children():
                node.destroy()

        elif renderer == "Mantra":
            # Interface Check
            if os.path.exists(parms_file_name):
                # Only load parms if MatBuilder
                if self.check_materialBuilder_by_id(id):
                    interface_file = open(parms_file_name, "r")
                    code = interface_file.read()
                    exec(code)

                    builder = hou.selectedNodes()[0]
                # Selection will be empty if not a MaterialBuilder
                else:
                    builder = import_path.createNode("materialbuilder")
            else:
                builder = hou.node(import_path).createNode("materialbuilder")

            builder.setName(mat.get_name(), unique_name=True)
            builder.setGenericFlag(hou.nodeFlag.Material, True)
            # Delete Default children in MaterialBuilder
            for node in builder.children():
                node.destroy()

        elif renderer == "Arnold":
            # CreateBuilder
            # Interface Check
            if os.path.exists(parms_file_name):
                interface_file = open(parms_file_name, "r")
                code = interface_file.read()
                exec(code)

                builder = hou_parent.children()[0]
            else:
                builder = hou.node(import_path).createNode("arnold_materialbuilder")

            builder.setName(mat.get_name(), unique_name=True)
            builder.setGenericFlag(hou.nodeFlag.Material, True)
            # Delete Default children in Arnold MaterialBuilder
            for node in builder.children():
                node.destroy()

        elif renderer == "MatX":
            # Interface Check
            if os.path.exists(parms_file_name):
                interface_file = open(parms_file_name, "r")
                code = interface_file.read()
                exec(code)

                builder = import_path.createNode("subnet")
                builder.setName(mat.get_name(), unique_name=True)
                builder.setGenericFlag(hou.nodeFlag.Material, True)
                for n in builder.children():
                    n.destroy()

        # Import file from disk
        try:
            builder.loadItemsFromFile(file_name, ignore_load_warnings=False)
        except:
            hou.ui.displayMessage("Failure on Import. Please Try again.")
            return

        # If node is Principled Shader
        if renderer == "Mantra" and not self.check_materialBuilder_by_id(id):
            n = builder.children()[0]
            hou.moveNodesTo((n,), builder.parent())
            builder.destroy()
            builder = hou.selectedNodes()[0]
        else:
            new_mat = hou.moveNodesTo((builder,), import_path)
            new_mat[0].moveToGoodPosition()
            builder = new_mat[0]

        # not sure why this was here
        # # If USD move into Material Library
        # if (
        #     self.context.type().name() == "stage"
        #     or self.context.type().name() == "lopnet"
        # ):
        #     print(builder)
        #     # nodes = builder.children()
        #     # nodes = hou.moveNodesTo(nodes, builder.parent())
        #     # builder.destroy()

        #     # builder = nodes[0].parent()

        # Cleanup
        tmp_matnet.destroy()

        if import_path.type().name() == "materiallibrary":
            import_path.parm("materials").set(0)
            import_path.parm("fillmaterials").pressButton()
            i = 0
            while i < import_path.parm("materials").evalAsInt():
                import_path.parm("".join(["assign", str(i + 1)])).set(0)
                i += 1

        self.context = self.get_current_network_node()
        return builder

    def save_node(self, node, id, update):
        """Save Node wrapper for different Material Types"""
        # Check against NodeType
        val = False
        print("Starting Render")
        if node.type().name() == "redshift_vopnet":
            # Interruptable
            with hou.InterruptableOperation(
                "Rendering", "Performing Tasks", open_interrupt_dialog=True
            ) as operation:
                val = self.save_node_redshift(node, id, update)
        elif (
            node.type().name() == "materialbuilder"
            or node.type().name() == "principledshader::2.0"
        ):
            # Interruptable
            if hou.getenv("OCIO") is None:
                hou.ui.displayMessage("Please set $OCIO first")
                return False
            with hou.InterruptableOperation(
                "Rendering", "Performing Tasks", open_interrupt_dialog=True
            ) as operation:
                val = self.save_node_mantra(node, id, update)
        elif node.type().name() == "arnold_materialbuilder":
            if hou.getenv("OCIO") is None:
                hou.ui.displayMessage("Please set $OCIO first")
                return False
            with hou.InterruptableOperation(
                "Rendering", "Performing Tasks", open_interrupt_dialog=True
            ) as operation:
                val = self.save_node_arnold(node, id, update)
        elif node.type().name() == "octane_vopnet":
            if hou.getenv("OCIO") is None:
                hou.ui.displayMessage("Please set $OCIO first")
                return False
            with hou.InterruptableOperation(
                "Rendering", "Performing Tasks", open_interrupt_dialog=True
            ) as operation:
                val = self.save_node_octane(node, id, update)
        elif node.type().name() == "subnet":
            # Hope for the best that it actually is a MtlX Subnet
            if hou.getenv("OCIO") is None:
                hou.ui.displayMessage("Please set $OCIO first")
                return False
            with hou.InterruptableOperation(
                "Rendering", "Performing Tasks", open_interrupt_dialog=True
            ) as operation:
                val = self.save_node_mtlX(node, id, update)
        elif node.type().name() == "collect":
            if hou.getenv("OCIO") is None:
                hou.ui.displayMessage("Please set $OCIO first")
                return False
            with hou.InterruptableOperation(
                "Rendering", "Performing Tasks", open_interrupt_dialog=True
            ) as operation:
                val = self.save_node_collect(node, id, update)
        else:
            hou.ui.displayMessage("Selected Node is not a Material Builder")
        return val

    def save_node_collect(self, node, id, update):
        """Saves the attached network from a collect node to disk - does not add to library"""
        # Filepath where to save stuff
        file_name = (
            self.get_path()
            + self.settings.get_asset_dir()
            + str(id)
            + self.settings.get_ext()
        )
        parms_file_name = (
            self.get_path() + self.settings.get_asset_dir() + str(id) + ".interface"
        )

        nodetree = helpers.getConnectedNodes(node)

        sub_tmp = nodetree[0].parent().createNode("subnet")
        children = sub_tmp.children()
        for n in children:
            n.destroy()
        hou.copyNodesTo((nodetree), sub_tmp)
        children = sub_tmp.children()

        interface_file = open(parms_file_name, "w")
        interface_file.write(sub_tmp.asCode())

        sub_tmp.saveItemsToFile(children, file_name, save_hda_fallbacks=False)
        sub_tmp.destroy()

        # If this is not a manual update and renderOnImport is off, finish here
        if not update:
            if not self.renderOnImport:
                return True

        return self.create_thumb_mtlx(nodetree, id)

    def save_node_mtlX(self, node, id, update):
        """Saves the MtlX node to disk - does not add to library"""
        # Filepath where to save stuff
        file_name = (
            self.get_path()
            + self.settings.get_asset_dir()
            + str(id)
            + self.settings.get_ext()
        )

        # interface-stuff
        parms_file_name = (
            self.get_path() + self.settings.get_asset_dir() + str(id) + ".interface"
        )

        children = node.children()

        interface_file = open(parms_file_name, "w")
        interface_file.write(node.asCode())

        node.saveItemsToFile(children, file_name, save_hda_fallbacks=False)

        if "subnet" in node.type().name():
            children = (node,)

        # If this is not a manual update and renderOnImport is off, finish here
        if not update:
            if not self.renderOnImport:
                return True

        return self.create_thumb_mtlx(children, id)

    def create_thumbnail(self, nodes, id):
        renderer = self.get_renderer_by_id(id)

        if renderer == "MatX":
            self.create_thumb_mtlx(nodes.children(), id)
        elif renderer == "Mantra":
            self.create_thumb_mantra(nodes, id)
        else:
            pass
        return

    def create_thumb_mtlx(self, children, id):
        # Build path
        path = self.get_path() + self.settings.get_img_dir() + str(id) + ".exr"
        # Create Thumbnail
        net = hou.node("/obj").createNode("lopnet")

        ref = net.createNode("reference::2.0")
        ref.parm("filepath1").set(hou.getenv("EGMATLIB") + "/usd/shaderBallScene.usd")

        lib1 = net.createNode("materiallibrary")
        lib1.setFirstInput(ref)
        surf = lib1.createNode("mtlxstandard_surface")
        tex = lib1.createNode("mtlxtiledimage")
        tex.parm("file").set("color3")
        tex.parm("file").set("$EGMATLIB/img/FloorTexture.rat")
        surf.setInput(1, tex, 0)
        surf.setGenericFlag(hou.nodeFlag.Material, True)
        lib1.parm("materials").set(1)
        lib1.parm("matnode1").set("mtlxstandard_surface1")
        lib1.parm("matpath1").set("/thumb/bg_material")
        lib1.parm("geopath1").set("/shaderBallScene/geo/plane/mesh_0")
        lib1.parm("assign1").set(1)

        lib = net.createNode("materiallibrary")
        lib.setFirstInput(lib1)

        nodes = hou.copyNodesTo((children), lib)
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

        copnet = rop.parent().createNode("cop2net")

        ############################
        # CopNet Setup
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
            self.get_path()
            + self.settings.get_img_dir()
            + str(id)
            + self.settings.get_img_ext()
        )

        cop_out.parm("copoutput").set(newpath)
        cop_out.parm("execute").pressButton()

        ############################

        net.destroy()

        if os.path.exists(path):
            os.remove(path)

        return True

    def create_thumb_mantra(self, node, id):
        # Create Thumbnail

        sc = thumbNailScene.ThumbNailScene()
        sc.setup("Mantra")
        thumb = sc.get_node()

        thumb.parm("mat").set(node.path())

        # Build path
        path = self.get_path() + self.settings.get_img_dir() + str(id)

        #  Set Rendersettings and Object Exclusions for Thumbnail Rendering
        thumb.parm("path").set(path + ".exr")
        thumb.parm("cop_out_img").set(path + self.settings.get_img_ext())
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
        return

    def save_node_redshift(self, node, id, update):
        """Saves the Redshift node to disk - does not add to library"""
        # Filepath where to save stuff
        file_name = (
            self.get_path()
            + self.settings.get_asset_dir()
            + str(id)
            + self.settings.get_ext()
        )

        # interface-stuff
        parms_file_name = (
            self.get_path() + self.settings.get_asset_dir() + str(id) + ".interface"
        )
        children = node.children()

        interface_file = open(parms_file_name, "w")
        # interface_file.write(node.parmTemplateGroup().asCode())
        interface_file.write(node.asCode())

        node.saveItemsToFile(children, file_name, save_hda_fallbacks=False)

        # If this is not a manual update and renderOnImport is off, finish here
        if not update:
            if not self.renderOnImport:
                return True

        # Create Thumbnail
        sc = thumbNailScene.ThumbNailScene()
        sc.setup("Redshift")
        thumb = sc.get_node()
        thumb.parm("mat").set(node.path())

        # Build path
        path = (
            self.get_path()
            + self.settings.get_img_dir()
            + str(id)
            + self.settings.get_img_ext()
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

    def save_node_octane(self, node, id, update):
        # Filepath where to save stuff
        file_name = (
            self.get_path()
            + self.settings.get_asset_dir()
            + str(id)
            + self.settings.get_ext()
        )

        # interface-stuff
        parms_file_name = (
            self.get_path() + self.settings.get_asset_dir() + str(id) + ".interface"
        )
        children = node.children()

        interface_file = open(parms_file_name, "w")
        # interface_file.write(node.parmTemplateGroup().asCode())
        interface_file.write(node.asCode())

        node.saveItemsToFile(children, file_name, save_hda_fallbacks=False)

        # If this is not a manual update and renderOnImport is off, finish here
        if not update:
            if not self.renderOnImport:
                return True

        # Create Thumbnail
        sc = thumbNailScene.ThumbNailScene()
        sc.setup("Octane")
        thumb = sc.get_node()
        thumb.parm("mat").set(node.path())
        # Build path
        path = (
            self.get_path()
            + self.settings.get_img_dir()
            + str(id)
            + self.settings.get_img_ext()
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
        # thumb.destroy()
        return True

    def save_node_arnold(self, node, id, update):  # ARNOLD
        """Saves the Arnold node to disk - does not add to library"""
        # Filepath where to save stuff
        file_name = (
            self.get_path()
            + self.settings.get_asset_dir()
            + str(id)
            + self.settings.get_ext()
        )

        # interface-stuff
        parms_file_name = (
            self.get_path() + self.settings.get_asset_dir() + str(id) + ".interface"
        )
        children = node.children()

        interface_file = open(parms_file_name, "w")
        interface_file.write(node.asCode())

        node.saveItemsToFile(children, file_name, save_hda_fallbacks=False)

        # If this is not a manual update and renderOnImport is off, finish here
        if not update:
            if not self.renderOnImport:
                return True

        # Create Thumbnail
        sc = thumbNailScene.ThumbNailScene()
        sc.setup("Arnold")
        thumb = sc.get_node()
        thumb.parm("mat").set(node.path())

        # Build path
        path = self.get_path() + self.settings.get_img_dir() + str(id)

        #  Set Rendersettings and Object Exclusions for Thumbnail Rendering
        thumb.parm("path").set(path + ".exr")
        thumb.parm("cop_out_img").set(path + self.settings.get_img_ext())

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

    def save_node_mantra(self, node, id, update):
        """Saves the Mantra node to disk - does not add to library"""
        # Filepath where to save stuff
        file_name = (
            self.get_path()
            + self.settings.get_asset_dir()
            + str(id)
            + self.settings.get_ext()
        )

        origNode = node
        builder = ""
        if node.type().name() != "materialbuilder":
            builder = hou.node("/mat").createNode("materialbuilder")
            for c in builder.children():
                c.destroy()
            hou.copyNodesTo((node,), builder)
            node = builder

        # interface-stuff
        parms_file_name = (
            self.get_path() + self.settings.get_asset_dir() + str(id) + ".interface"
        )
        children = node.children()

        interface_file = open(parms_file_name, "w")
        interface_file.write(node.asCode())

        node.saveItemsToFile(children, file_name, save_hda_fallbacks=False)

        node = origNode
        if builder != "":
            builder.destroy()

        # If this is not a manual update and renderOnImport is off, finish here
        if not update:
            if not self.renderOnImport:
                return True
        self.create_thumb_mantra(node, id)

        return True
