import hou
import shaderBallScene
import importlib

importlib.reload(shaderBallScene)


class ThumbNailScene:

    def __init__(self):
        pass

    def setup(self, renderer="Mantra"):

        # Render Independemt Setup
        self.geo_node = hou.node("/obj").createNode("subnet")
        self.build_parm_templates()

        self.geo_node.parm("path").set("$HIP/render/$HIPNAME.$OS.$F4.exr")
        self.geo_node.parm("cop_out_img").set("$HIP/render/$HIPNAME.$OS.$F4.png")
        self.geo_node.parm("resx").set(512)
        self.geo_node.parm("resy").set(512)
        self.geo_node.parm("lights").set("*")

        if "Mantra" in renderer:

            self.shaderBall = shaderBallScene.ShaderBallSetup()
            self.shaderBall.setup(renderer, self.geo_node)

            self.renderer = renderer

            self.build_scene()
            self.shaderBall.get_geo_node().parm("mat_ball").set(
                self.geo_node.parm("mat")
            )
            self.comp.parm("execute").set(self.geo_node.parm("render"))

        return self.geo_node

    def build_parm_templates(self):
        # Add Parms on top
        self.geo_node.setName("Thumbnail_Mantra", True)

        data_template = hou.StringParmTemplate(
            "mat",
            "ShaderBall Material",
            1,
            string_type=hou.stringParmType.NodeReference,
        )
        self.geo_node.addSpareParmTuple(data_template)

        data_template = hou.FloatParmTemplate("res", "Resolution", 2)
        self.geo_node.addSpareParmTuple(data_template)

        data_template = hou.StringParmTemplate(
            "obj_exclude",
            "Exclude Objects",
            1,
            string_type=hou.stringParmType.NodeReference,
        )
        self.geo_node.addSpareParmTuple(data_template)

        data_template = hou.StringParmTemplate(
            "lights",
            "Lights",
            1,
            string_type=hou.stringParmType.NodeReference,
        )
        self.geo_node.addSpareParmTuple(data_template)

        data_template = hou.StringParmTemplate(
            "path",
            "Render Path",
            1,
            string_type=hou.stringParmType.FileReference,
        )
        self.geo_node.addSpareParmTuple(data_template)

        data_template = hou.StringParmTemplate(
            "cop_out_img",
            "Output Picture",
            1,
            string_type=hou.stringParmType.FileReference,
        )
        self.geo_node.addSpareParmTuple(data_template)

        data_template = hou.ButtonParmTemplate("render", "Render", script_callback=None)
        self.geo_node.addSpareParmTuple(data_template)

    def build_scene(self):

        self.ropnet = self.geo_node.createNode("ropnet")
        self.copnet = self.geo_node.createNode("cop2net")

        # Lights
        self.lgt_right = self.geo_node.createNode("hlight::2.0")
        self.lgt_right.setName("Right")
        self.lgt_env = self.geo_node.createNode("envlight")
        self.lgt_right.setName("Env")
        self.lgt_left = self.geo_node.createNode("hlight::2.0")
        self.lgt_right.setName("Left")

        # Right
        self.lgt_right.parm("tx").set(0.182989)
        self.lgt_right.parm("ty").set(0.400678)
        self.lgt_right.parm("tz").set(-0.637707)

        self.lgt_right.parm("rx").set(-164.722)
        self.lgt_right.parm("ry").set(0)
        self.lgt_right.parm("rz").set(0)

        self.lgt_right.parm("light_type").set(2)
        self.lgt_right.parm("light_intensity").set(0.5)
        self.lgt_right.parm("areasize1").set(0.25)
        self.lgt_right.parm("areasize2").set(0.25)
        self.lgt_right.parm("singlesided").set(1)

        # Left
        self.lgt_left.parm("tx").set(0.00626206)
        self.lgt_left.parm("ty").set(0.290401)
        self.lgt_left.parm("tz").set(0.562686)

        self.lgt_left.parm("rx").set(180)
        self.lgt_left.parm("ry").set(180)
        self.lgt_left.parm("rz").set(0)

        self.lgt_left.parm("light_type").set(2)
        self.lgt_left.parm("light_intensity").set(0.06)
        self.lgt_left.parm("areasize1").set(0.5)
        self.lgt_left.parm("areasize2").set(0.5)
        self.lgt_left.parm("singlesided").set(1)

        # Cam
        self.cam = self.geo_node.createNode("cam")

        self.cam.parm("tx").set(0.235797)
        self.cam.parm("ty").set(0.130498)
        self.cam.parm("tz").set(0.0811536)

        self.cam.parm("rx").set(-12.578)
        self.cam.parm("ry").set(71.1787)
        self.cam.parm("rz").set(0)

        self.cam.parm("aperture").set(36)
        self.cam.parm("near").set(0.002)
        self.cam.parm("far").set(2000)
        self.cam.parm("resx").set(512)
        self.cam.parm("resy").set(512)
        self.cam.setName("RenderCam", True)

        # Rot cam to match shaderball
        null = self.geo_node.createNode("null")
        self.cam.parm("keeppos").set(1)
        self.cam.setInput(0, null, 0)
        null.parm("ry").set(180)

        # RopNet Setup
        self.ifd = self.ropnet.createNode("ifd")
        self.comp = self.ropnet.createNode("comp")
        self.comp.setNextInput(self.ifd)

        self.ifd.parm("camera").set("../../RenderCam")

        self.ifd.parm("vm_writecheckpoint").set(0)

        self.ifd.parm("vm_renderengine").set("pbrraytrace")
        self.ifd.parm("vm_samplesx").set(4)
        self.ifd.parm("vm_samplesy").set(4)

        self.ifd.parm("vm_reflectlimit").set(1)
        self.ifd.parm("vm_refractlimit").set(2)
        self.ifd.parm("vm_diffuselimit").set(1)
        self.ifd.parm("vm_ssslimit").set(1)
        self.ifd.parm("vm_volumelimit").set(1)

        self.ifd.parm("vm_usemaxthreads").set(2)

        self.ifd.parm("excludeobject").set(self.geo_node.parm("obj_exclude"))
        self.ifd.parm("alights").set(self.geo_node.parm("lights"))
        self.ifd.parm("soho_autoheadlight").set(0)

        self.ifd.parm("soho_foreground").set(1)

        self.comp.parm("coppath").set("../../exr_to_png/OUT")
        self.comp.parm("copoutput").set(self.geo_node.parm("cop_out_img"))
        self.comp.parm("convertcolorspace").set(0)
        self.comp.parm("trange").set(0)

        # CopNet Setup
        self.copnet.setName("exr_to_png")

        self.cop_file = self.copnet.createNode("file")

        self.cop_file.parm("nodename").set(0)
        self.cop_file.parm("overridedepth").set(2)
        self.cop_file.parm("depth").set(4)

        self.cop_file.parm("filename1").set(self.ifd.parm("vm_picture"))
        self.ifd.parm("vm_picture").set(
            self.geo_node.parm("path"), follow_parm_reference=False
        )

        # Vopnet
        self.cop_vop = self.copnet.createNode("vopcop2filter")
        gn = self.cop_vop.node("global1")
        o = self.cop_vop.node("output1")
        ftv = self.cop_vop.createNode("floattovec")
        ocio = self.cop_vop.createNode("ocio_transform")
        vtf = self.cop_vop.createNode("vectofloat")

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

        self.cop_out = self.copnet.createNode("null")

        self.cop_vop.setInput(0, self.cop_file)
        self.cop_out.setInput(0, self.cop_vop)

        self.cop_out.setGenericFlag(hou.nodeFlag.Display, True)
        self.cop_out.setGenericFlag(hou.nodeFlag.Render, True)
        self.cop_out.setName("OUT", True)

        self.geo_node.layoutChildren()

    def get_node(self):

        return self.geo_node
