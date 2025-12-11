import os
import time
import hou

from matlib.core import material
from matlib.render import nodes, thumbnail_scene
from matlib.prefs import prefs


class ThumbNailRenderer:
    def __init__(
        self, preferences: prefs.Prefs, mat: material.Material | None = None
    ) -> None:
        self._mat = mat
        self._preferences = preferences
        self._builder = None

    def create_thumbnail(self) -> None:
        node_handler = nodes.NodeHandler(self._preferences)
        if self._mat:
            node_handler.import_asset_to_scene(self._mat)

        if "MaterialX" in self._mat.renderer:
            self.context = hou.node("/stage")
        else:
            self.context = hou.node("/mat")

        with hou.InterruptableOperation(
            "Rendering", "Performing Tasks", open_interrupt_dialog=True
        ):
            if self._mat.renderer == "MaterialX":
                self.create_thumb_mtlx(node_handler.builder_node, self._mat.mat_id)
            elif self._mat.renderer == "Mantra":
                self.create_thumb_mantra(node_handler.builder_node, self._mat.mat_id)
            elif self._mat.renderer == "Redshift":
                self.create_thumb_redshift(node_handler.builder_node, self._mat.mat_id)
            elif self._mat.renderer == "Octane":
                self.create_thumb_octane(node_handler.builder_node, self._mat.mat_id)
            elif self._mat.renderer == "Arnold":
                self.create_thumb_arnold(node_handler.builder_node, self._mat.mat_id)

            else:
                pass
        node_handler.cleanup()

    def create_thumb_mtlx(self, node: hou.Node, asset_id: str) -> bool:
        # Build path
        path = (
            self._preferences.dir + self._preferences.img_dir + str(asset_id) + ".exr"
        )

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

        nodes = hou.copyNodesTo((node.children()), lib)  # type: ignore
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

        preferences = net.createNode("karmarenderproperties")
        preferences.parm("camera").set("/shaderBallScene/cameras/RenderCam")
        preferences.parm("res_mode").set("manual")
        preferences.parm("res_mode").pressButton()
        preferences.parm("resolutionx").set(self._preferences.rendersize)
        preferences.parm("resolutiony").deleteAllKeyframes()
        preferences.parm("resolutiony").set(self._preferences.rendersize)
        preferences.parm("engine").set("xpu")
        preferences.parm("engine").pressButton()
        preferences.parm("pathtracedsamples").set(32)  # TODO: set to 256 again
        preferences.parm("enabledof").set(0)
        preferences.parm("enablemblur").set(0)
        preferences.parm("picture").set(path)
        preferences.setFirstInput(lib)

        rop = net.createNode("usdrender_rop")
        rop.parm("renderer").set("BRAY_HdKarmaXPU")  # KarmaXPU
        rop.setFirstInput(preferences)
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
            self._preferences.dir
            + self._preferences.img_dir
            + str(asset_id)
            + self._preferences.img_ext
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
        path = self._preferences.dir + self._preferences.img_dir + str(asset_id)

        #  Set Renderpreferences and Object Exclusions for Thumbnail Rendering
        thumb.parm("path").set(path + ".exr")
        thumb.parm("cop_out_img").set(path + self._preferences.img_ext)
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

    def create_thumb_redshift(self, node: hou.Node, asset_id: str) -> bool:

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

    def create_thumb_octane(self, node: hou.Node, asset_id: str) -> bool:
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

    def create_thumb_arnold(self, node: hou.Node, asset_id: str) -> bool:
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
