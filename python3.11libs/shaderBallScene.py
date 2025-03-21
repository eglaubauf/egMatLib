import hou


class ShaderBallSetup:

    def __init__(self):
        pass

    def setup(self, renderer="Mantra", parent=hou.node("/obj")):

        self.geo_node = parent.createNode("geo")
        self.filecache = self.geo_node.createNode("filecache::2.0")

        self.split = self.geo_node.createNode("split")
        self.split.setInput(0, self.filecache, 0)

        self.mat_plane = self.geo_node.createNode("material")
        self.mat_ball = self.geo_node.createNode("material")

        self.mat_plane.setInput(0, self.split, 0)
        self.mat_ball.setInput(0, self.split, 1)

        self.merge = self.geo_node.createNode("merge")

        self.merge.setNextInput(self.mat_plane, 0)
        self.merge.setNextInput(self.mat_ball, 0)

        self.switch = self.geo_node.createNode("switch")
        self.switch.setNextInput(self.merge, 0)
        self.switch.setNextInput(self.mat_ball, 0)

        self.out = self.geo_node.createNode("null")
        self.out.setName("OUT", True)
        self.out.setInput(0, self.switch, 0)

        # Add Parms on top
        self.geo_node.setName("ShaderBallScene", True)

        data_template = hou.StringParmTemplate(
            "mat_ball",
            "ShaderBall Material",
            1,
            string_type=hou.stringParmType.NodeReference,
        )
        self.geo_node.addSpareParmTuple(data_template)

        toggle_template = hou.ToggleParmTemplate(
            "do_show_ball_only", "Show Ball Only", 1
        )
        self.geo_node.addSpareParmTuple(toggle_template)

        self.matnet = self.geo_node.createNode("matnet")
        self.apply_initial_materials(renderer)

        # Set Parms
        self.filecache.parm("loadfromdisk").set(1)
        self.filecache.parm("file").set("$EGMATLIB/geo/ShaderBallScene.bgeo.sc")
        self.filecache.parm("filemethod").set(1)
        self.filecache.parm("timedependent").set(0)

        self.split.parm("group").set("Plane")
        self.split.parm("grouptype").set(4)

        self.mat_plane.parm("shop_materialpath1").set("../matnet1/Plane")

        # TO BE FILLED BY USER
        self.mat_ball.parm("shop_materialpath1").set(self.geo_node.parm("mat_ball"))
        self.switch.parm("input").set(self.geo_node.parm("do_show_ball_only"))
        self.geo_node.parm("do_show_ball_only").set(0)

        self.out.setGenericFlag(hou.nodeFlag.Display, True)
        self.out.setGenericFlag(hou.nodeFlag.Render, True)

        self.geo_node.layoutChildren()

    def apply_initial_materials(self, renderer):

        if "Mantra" in renderer:
            self.mat = self.matnet.createNode("principledshader::2.0")

            self.mat.parm("basecolorr").set(1)
            self.mat.parm("basecolorg").set(1)
            self.mat.parm("basecolorb").set(1)
            self.mat.parm("basecolor_usePointColor").set(0)
            self.mat.parm("basecolor_useTexture").set(1)
            self.mat.parm("basecolor_texture").set("$EGMATLIB/img/FloorTexture.rat")

            self.mat.parm("rough").set(0)
            self.mat.parm("reflect").set(0)

            self.mat.setName("Plane", True)

        elif "Redshift" in renderer:

            self.mat = self.matnet.createNode("redshift_vopnet")

            rsmat = self.mat.node("StandardMaterial1")
            rsmat.parm("refl_weight").set(0)

            tex = self.mat.createNode("redshift::TextureSampler")
            tex.parm("tex0").set("$EGMATLIB/img/FloorTexture.exr")

            rsmat.setInput(0, tex, 0)

            self.mat.setName("Plane", True)

        elif "Arnold" in renderer:

            self.mat = self.matnet.createNode("arnold_materialbuilder")
            out = self.mat.node("OUT_material")

            amat = self.mat.createNode("arnold::standard_surface")
            amat.parm("specular").set(0)

            tex = self.mat.createNode("arnold::image")
            tex.parm("filename").set("$EGMATLIB/img/FloorTexture.tx")

            amat.setInput(0, tex, 0)
            out.setInput(0, amat, 0)

            self.mat.setName("Plane", True)

    def apply_materials(self, material):

        pass

    def get_geo_node(self):

        return self.geo_node
