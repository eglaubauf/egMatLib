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
        self.renderer = renderer
        self.build_parm_templates()

        self.geo_node.parm("path").set("$HIP/render/$HIPNAME.$OS.$F4.exr")
        self.geo_node.parm("cop_out_img").set("$HIP/render/$HIPNAME.$OS.$F4.png")
        self.geo_node.parm("resx").set(512)
        self.geo_node.parm("resy").set(512)
        self.geo_node.parm("lights").set("*")

        if "Mantra" in renderer:

            self.shaderBall = shaderBallScene.ShaderBallSetup()
            self.shaderBall.setup(self.renderer, self.geo_node)

            self.build_scene()
            self.shaderBall.get_geo_node().parm("mat_ball").set(
                self.geo_node.parm("mat")
            )
            self.comp.parm("execute").set(self.geo_node.parm("render"))

        elif "Redshift" in renderer:

            self.shaderBall = shaderBallScene.ShaderBallSetup()
            self.shaderBall.setup(self.renderer, self.geo_node)

            self.build_scene()
            self.shaderBall.get_geo_node().parm("mat_ball").set(
                self.geo_node.parm("mat")
            )
            self.rop.parm("execute").set(self.geo_node.parm("render"))

        return self.geo_node

    def build_parm_templates(self):
        # Add Parms on top
        name = "Thumbnail_" + self.renderer
        self.geo_node.setName(name, True)

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

        self.build_lights()
        self.build_cam()
        self.build_rops()
        self.build_cops()

        self.geo_node.layoutChildren()

    def build_lights(self):

        if "Mantra" in self.renderer:
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

        elif "Redshift" in self.renderer:
            # Lights
            self.lgt_right = self.geo_node.createNode("rslight")
            self.lgt_right.setName("Right")
            self.lgt_env = self.geo_node.createNode("rslightdome::2.0")
            self.lgt_right.setName("Env")
            self.lgt_left = self.geo_node.createNode("rslight")
            self.lgt_right.setName("Left")

            # Right
            self.lgt_right.parm("tx").set(0.182989)
            self.lgt_right.parm("ty").set(0.400678)
            self.lgt_right.parm("tz").set(-0.637707)

            self.lgt_right.parm("rx").set(-164.722)
            self.lgt_right.parm("ry").set(-11.677)
            self.lgt_right.parm("rz").set(0)

            self.lgt_right.parm("RSL_intensityMultiplier").set(2)
            self.lgt_right.parm("Light1_exposure").set(1.5)
            self.lgt_right.parm("areasize1").set(0.5)
            self.lgt_right.parm("areasize2").set(0.5)
            self.lgt_right.parm("areasize3").set(0.5)
            self.lgt_right.parm("RSL_samples").set(128)
            self.lgt_right.parm("RSL_cameraScale").set(0)

            # Left
            self.lgt_left.parm("tx").set(0.00626206)
            self.lgt_left.parm("ty").set(0.290401)
            self.lgt_left.parm("tz").set(0.562686)

            self.lgt_left.parm("rx").set(0)
            self.lgt_left.parm("ry").set(0)
            self.lgt_left.parm("rz").set(0)

            self.lgt_left.parm("RSL_intensityMultiplier").set(7.1)
            self.lgt_left.parm("Light1_exposure").set(0)
            self.lgt_left.parm("areasize1").set(0.28)
            self.lgt_left.parm("areasize2").set(0.5)
            self.lgt_left.parm("areasize3").set(0.5)
            self.lgt_left.parm("RSL_samples").set(128)
            self.lgt_left.parm("RSL_cameraScale").set(0)

            # DomeLight
            self.lgt_env.parm("light_intensity").set(0.3)
            self.lgt_env.parm("ry").set(17.6)
            self.lgt_env.parm("env_map").set(
                "$EGMATLIB/img/photo_studio_01_4k_ACEScg.hdr"
            )

    def build_cam(self):
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

        if "Redshift" in self.renderer:
            self.cam.setSelected(True, True)
            hou.hscript("Redshift_cameraSpareParameters -C 1")
            self.geo_node.setSelected(True, True)

    def build_rops(self):

        if "Mantra" in self.renderer:
            # RopNet Setup
            self.rop = self.ropnet.createNode("ifd")
            self.comp = self.ropnet.createNode("comp")
            self.comp.setNextInput(self.rop)

            self.rop.parm("camera").set("../../RenderCam")

            self.rop.parm("vm_writecheckpoint").set(0)

            self.rop.parm("vm_renderengine").set("pbrraytrace")
            self.rop.parm("vm_samplesx").set(4)
            self.rop.parm("vm_samplesy").set(4)

            self.rop.parm("vm_reflectlimit").set(1)
            self.rop.parm("vm_refractlimit").set(2)
            self.rop.parm("vm_diffuselimit").set(1)
            self.rop.parm("vm_ssslimit").set(1)
            self.rop.parm("vm_volumelimit").set(1)

            self.rop.parm("vm_usemaxthreads").set(2)

            self.rop.parm("excludeobject").set(self.geo_node.parm("obj_exclude"))
            self.rop.parm("alights").set(self.geo_node.parm("lights"))
            self.rop.parm("soho_autoheadlight").set(0)

            self.rop.parm("soho_foreground").set(1)

            self.comp.parm("coppath").set("../../exr_to_png/OUT")
            self.comp.parm("copoutput").set(self.geo_node.parm("cop_out_img"))
            self.comp.parm("convertcolorspace").set(0)
            self.comp.parm("trange").set(0)

        elif "Redshift" in self.renderer:
            self.rop = self.ropnet.createNode("Redshift_ROP")
            self.rop.parm("RS_renderCamera").set("../../RenderCam")
            self.rop.parm("RS_OCIOColorCorrection").set(1)
            self.rop.parm("RS_addDefaultLight").set(1)
            self.rop.parm("RS_outputFileFormat").set(3)
            self.rop.parm("RS_renderToMPlay").set(0)
            self.rop.parm("RS_nonBlockingRendering").set(0)

            self.rop.parm("RS_PFX_MPL_exposure").set(0)
            self.rop.parm("RS_PFX_MPL_effects").set(0)
            self.rop.parm("RS_PFX_HDR_exposure").set(0)
            self.rop.parm("RS_PFX_MPL_effects").set(0)
            self.rop.parm("RS_PFX_LDR_exposure").set(0)

            self.rop.parm("RS_objects_exclude").set(self.geo_node.parm("obj_exclude"))
            self.rop.parm("RS_lights_candidate").set(self.geo_node.parm("lights"))
            self.rop.parm("RS_outputFileNamePrefix").set(
                self.geo_node.parm("path"), follow_parm_reference=False
            )

    def build_cops(self):

        if "Mantra" in self.renderer:
            # CopNet Setup
            self.copnet.setName("exr_to_png")

            self.cop_file = self.copnet.createNode("file")

            self.cop_file.parm("nodename").set(0)
            self.cop_file.parm("overridedepth").set(2)
            self.cop_file.parm("depth").set(4)

            self.cop_file.parm("filename1").set(self.rop.parm("vm_picture"))
            self.rop.parm("vm_picture").set(
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

    def get_node(self):
        return self.geo_node
