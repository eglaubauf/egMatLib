"""
Generates a Thumbnail Scene and allows for Rendering Material Preview
"""

import importlib
import hou
from matlib.render import shaderball_scene

importlib.reload(shaderball_scene)


class ThumbNailScene:
    """
    Generates a Thumbnail Scene and allows for Rendering Material Preview
    """

    def __init__(self, renderer: str = "Mantra", ballmode: int = 0):
        # Render Independemt Setup
        self.geo_node = hou.node("/obj").createNode("subnet")
        self.renderer = renderer

        viewer = hou.ui.curDesktop().paneTabOfType(hou.paneTabType.SceneViewer)
        if not viewer:
            return False

        self.display = viewer.getOCIODisplay()
        self.view = viewer.getOCIOView()

        self.space = "ACESCg"
        for s in hou.Color.ocio_spaces():
            if "acescg" in s.lower():
                self.space = s
                break

        self.build_parm_templates()

        self.geo_node.parm("path").set("$HIP/render/$HIPNAME.$OS.$F4.exr")
        self.geo_node.parm("cop_out_img").set("$HIP/render/$HIPNAME.$OS.$F4.png")
        self.geo_node.parm("resx").set(512)
        self.geo_node.parm("resy").set(512)
        self.geo_node.parm("lights").set("*")

        if "Mantra" in renderer:
            self.shaderball = shaderball_scene.ShaderBallSetup(
                self.renderer, self.geo_node, ballmode
            )

            self.build_scene()
            self.shaderball.get_geo_node().parm("mat_ball").set(
                self.geo_node.parm("mat")
            )
            self.comp.parm("execute").set(self.geo_node.parm("render"))

        elif "Redshift" in renderer:
            self.shaderball = shaderball_scene.ShaderBallSetup(
                self.renderer, self.geo_node, ballmode
            )

            self.build_scene()
            self.shaderball.get_geo_node().parm("mat_ball").set(
                self.geo_node.parm("mat")
            )
            self.rop.parm("execute").set(self.geo_node.parm("render"))

        elif "Arnold" in renderer:
            self.shaderball = shaderball_scene.ShaderBallSetup(
                self.renderer, self.geo_node, ballmode
            )

            self.build_scene()
            self.shaderball.get_geo_node().parm("mat_ball").set(
                self.geo_node.parm("mat")
            )
            self.shell.parm("execute").set(self.geo_node.parm("render"))

        elif "Octane" in renderer:
            self.shaderball = shaderball_scene.ShaderBallSetup(
                self.renderer, self.geo_node, ballmode
            )

            self.build_scene()
            self.shaderball.get_geo_node().parm("mat_ball").set(
                self.geo_node.parm("mat")
            )
            self.rop.parm("execute").set(self.geo_node.parm("render"))

    def build_parm_templates(self) -> None:
        """
        Build ParmTemplate for Population of Parameters
        """
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

    def build_scene(self) -> None:
        """
        Build the entire Scene with Lights, Camera, Rops and Cops
        """
        self.ropnet = self.geo_node.createNode("ropnet")
        self.copnet = self.geo_node.createNode("cop2net")

        self.build_lights()
        self.build_cam()
        self.build_rops()
        self.build_cops()

        self.geo_node.layoutChildren()

    def build_lights(self) -> None:
        """
        Build Lights for the set Renderer
        """
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
                "$EGMATLIB/scripts/python/matlib/res/img/photo_studio_01_4k_ACEScg.hdr"
            )

        elif "Arnold" in self.renderer:
            # Lights
            self.lgt_right = self.geo_node.createNode("arnold_light")
            self.lgt_right.setName("Right")
            self.lgt_env = self.geo_node.createNode("arnold_light")
            self.lgt_right.setName("Env")
            self.lgt_left = self.geo_node.createNode("arnold_light")
            self.lgt_right.setName("Left")

            # Right
            self.lgt_right.parm("tx").set(0.182989)
            self.lgt_right.parm("ty").set(0.400678)
            self.lgt_right.parm("tz").set(-0.637707)

            self.lgt_right.parm("rx").set(-164.722)
            self.lgt_right.parm("ry").set(0)
            self.lgt_right.parm("rz").set(0)

            self.lgt_right.parm("ar_light_type").set(3)
            self.lgt_right.parm("ar_intensity").set(0.5)
            self.lgt_right.parm("ar_samples").set(3)

            # Left
            self.lgt_left.parm("tx").set(0.00626206)
            self.lgt_left.parm("ty").set(0.290401)
            self.lgt_left.parm("tz").set(0.562686)

            self.lgt_left.parm("rx").set(180)
            self.lgt_left.parm("ry").set(180)
            self.lgt_left.parm("rz").set(0)

            self.lgt_right.parm("ar_light_type").set(3)
            self.lgt_right.parm("ar_intensity").set(0.2)
            self.lgt_right.parm("ar_samples").set(3)
            self.lgt_right.parm("ar_quad_sizex").set(0.4)
            self.lgt_right.parm("ar_quad_sizey").set(0.74)

            # Env
            self.lgt_env.parm("ry").set(-60)
            self.lgt_env.parm("ar_light_type").set(6)
            self.lgt_env.parm("ar_light_color_type").set(1)
            self.lgt_env.parm("ar_intensity").set(0.2)
            self.lgt_env.parm("ar_samples").set(3)
            self.lgt_env.parm("ar_light_color_texture").set(
                "$EGMATLIB/scripts/python/matlib/res/img/photo_studio_01_4k_ACEScg.tx"
            )

        elif "Octane" in self.renderer:
            # Lights
            self.lgt_right = self.geo_node.createNode("octane_light")
            self.lgt_right.setName("Right")
            self.lgt_left = self.geo_node.createNode("octane_light")
            self.lgt_right.setName("Left")

            # Right
            self.lgt_right.parm("tx").set(0.182989)
            self.lgt_right.parm("ty").set(0.400678)
            self.lgt_right.parm("tz").set(-0.637707)

            self.lgt_right.parm("rx").set(-164.722)
            self.lgt_right.parm("ry").set(-11.677)
            self.lgt_right.parm("rz").set(0)

            self.lgt_right.parm("sx").set(0.5)
            self.lgt_right.parm("sy").set(0.5)
            self.lgt_right.parm("sz").set(0.5)

            self.lgt_right.parm("NT_EMIS_BLACKBODY1_power").set(30)

            # Left
            self.lgt_left.parm("tx").set(-0.0788468)
            self.lgt_left.parm("ty").set(0.247556)
            self.lgt_left.parm("tz").set(0.562686)

            self.lgt_left.parm("sx").set(0.28)
            self.lgt_left.parm("sy").set(0.5)
            self.lgt_left.parm("sz").set(0.5)

            self.lgt_left.parm("NT_EMIS_BLACKBODY1_power").set(15)

            # Do weird Octane Domelight as shader
            self.mat_net = self.geo_node.createNode("matnet")

            # Octane Current
            target = self.mat_net.createNode("octane_mat_renderTarget")

            if "::2.0" in target.type().name():
                # Octane FUTURE
                target.parm("kernelMenu").set(3)
                target.parm("environmentMenu").set(6)

                target.parm("maxsamples").set(200)
                target.parm("textureEnvPower").set(0.2)
                target.parm("textureEnvironmentFilename").set(
                    "$EGMATLIB/scripts/python/matlib/res/img/photo_studio_01_4k_ACEScg.hdr"
                )
                target.parm("colorSpace").set("NAMED_COLOR_SPACE_ACESCG")
                target.setName("Octane_RenderTarget")
            elif "::2.2" in target.type().name():
                # Octane 2026
                target.parm("kernelMenu").set(3)
                target.parm("environmentMenu").set(6)

                target.parm("maxsamples").set(200)
                target.parm("textureEnvPower_1").set(0.2)
                target.parm("textureEnvFilename_1").set(
                    "$EGMATLIB/scripts/python/matlib/res/img/photo_studio_01_4k_ACEScg.hdr"
                )
                target.parm("textureEnvColorSpace_1").set("NAMED_COLOR_SPACE_ACESCG")
                target.setName("Octane_RenderTarget")
            elif "::2.1" in target.type().name():
                # Octane 2025
                target.parm("kernelMenu").set(3)
                target.parm("environmentMenu").set(6)

                target.parm("maxsamples").set(200)
                target.parm("textureEnvPower").set(0.2)
                target.parm("textureEnvironmentFilename").set(
                    "$EGMATLIB/scripts/python/matlib/res/img/photo_studio_01_4k_ACEScg.hdr"
                )
                target.parm("colorSpace").set("NAMED_COLOR_SPACE_ACESCG")
                target.setName("Octane_RenderTarget")

            else:
                # Octane Current
                target.parm("parmKernel").set(1)
                target.parm("parmEnvironment").set(1)

                target.parm("maxSamples2").set(200)
                target.parm("power4").set(0.2)
                target.parm("A_FILENAME4").set(
                    "$EGMATLIB/scripts/python/matlib/res/img/photo_studio_01_4k_ACEScg.hdr"
                )
                target.parm("colorSpace2").set("NAMED_COLOR_SPACE_ACESCG")

            target.setName("Octane_RenderTarget")

    def build_cam(self) -> None:
        """
        Build Camera for the set Renderer
        """
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
        self.cam.parm("resx").set(
            self.geo_node.parm("resx"), follow_parm_reference=False
        )
        self.cam.parm("resy").set(
            self.geo_node.parm("resy"), follow_parm_reference=False
        )

        self.cam.parm("focus").set(0.188163)
        self.cam.parm("fstop").set(1000)

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

    def build_rops(self) -> None:
        """
        Build Rops for the set Renderer
        """

        if "Mantra" in self.renderer:
            # RopNet Setup
            self.rop = self.ropnet.createNode("ifd")
            self.comp = self.ropnet.createNode("comp")
            self.comp.setNextInput(self.rop)

            self.rop.parm("camera").set("../../RenderCam")

            self.rop.parm("vm_writecheckpoint").set(0)

            self.rop.parm("vm_renderengine").set("pbrraytrace")
            self.rop.parm("vm_samplesx").set(3)
            self.rop.parm("vm_samplesy").set(3)
            self.rop.parm("vm_variance").set(0.025)

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

            self.rop.parm("vm_picture").set("`chs('../../path')`")
            self.comp.parm("coppath").set("../../exr_to_png/OUT")
            self.comp.parm("copoutput").set(self.geo_node.parm("cop_out_img"))
            self.comp.parm("convertcolorspace").set(0)

            self.comp.parm("convertcolorspace").set(3)
            self.comp.parm("ocio_display").set(self.display)
            self.comp.parm("ocio_view").set(self.view)

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

        if "Arnold" in self.renderer:
            # RopNet Setup
            self.rop = self.ropnet.createNode("arnold")
            self.comp = self.ropnet.createNode("comp")
            self.comp.setNextInput(self.rop)

            self.rop.parm("camera").set("../../RenderCam")

            self.rop.parm("ar_AA_samples").set(4)
            self.rop.parm("ar_GI_total_depth").set(4)
            self.rop.parm("ar_GI_transmission_depth").set(4)
            self.rop.parm("ar_threads").set(-1)
            self.rop.parm("ar_skip_license_check").set(1)

            self.rop.parm("excludeobject").set(self.geo_node.parm("obj_exclude"))
            self.rop.parm("alights").set(self.geo_node.parm("lights"))

            self.comp.parm("coppath").set("../../exr_to_png/OUT")
            self.comp.parm("copoutput").set(self.geo_node.parm("cop_out_img"))
            self.comp.parm("convertcolorspace").set(0)

            self.comp.parm("convertcolorspace").set(3)
            self.comp.parm("ocio_display").set(self.display)
            self.comp.parm("ocio_view").set(self.view)

            self.comp.parm("trange").set(0)

            self.shell = self.ropnet.createNode("shell")
            self.shell.parm("tpostrender").set(1)
            self.shell.parm("lpostrender").set("python")
            self.shell.parm("postrender").set(
                """path = hou.getenv("EGMATLIB") + "/lib/"
f = open(path + "done.txt", "w")
f.close()
"""
            )
            self.shell.setNextInput(self.comp)

        if "Octane" in self.renderer:
            # RopNet Setup
            self.rop = self.ropnet.createNode("Octane_ROP")

            self.rop.parm("HO_renderCamera").set("../../RenderCam")
            # self.rop.parm("HO_iprCamera").set("../../RenderCam")
            self.rop.parm("HO_renderTarget").set("../../matnet1/Octane_RenderTarget")

            self.rop.parm("HO_renderToMPlay").set(0)

            self.rop.parm("HO_img_colorSpace").set(5)
            self.rop.parm("HO_img_ocioColorSpace").set(114)

            self.rop.parm("HO_img_fileFormat").set(0)

            self.rop.parm("HO_mbDeformations").set(0)
            self.rop.parm("HO_mbFur").set(0)
            self.rop.parm("HO_mbInstances").set(0)
            self.rop.parm("HO_mbParticles").set(0)

            self.rop.parm("HO_img_deepFile").set("deep filename")

            self.rop.parm("HO_objects_exclude").set(self.geo_node.parm("obj_exclude"))

            self.rop.parm("HO_img_fileName").set(
                self.geo_node.parm("path"), follow_parm_reference=False
            )

    def build_cops(self) -> None:
        """
        Build COPs for the set Renderer
        """
        if "Mantra" in self.renderer or "Arnold" in self.renderer:
            # CopNet Setup
            self.copnet.setName("exr_to_png")

            cop_file = self.copnet.createNode("file")
            cop_file.parm("nodename").set(0)
            cop_file.parm("filename1").set(self.rop.parm("vm_picture"))
            cop_file.parm("colorspace").set(3)  # Set to OpenColorIO
            cop_file.parm("ocio_space").set(self.space)

            if "Redshift" in self.renderer:
                self.rop.parm("vm_picture").set(
                    self.geo_node.parm("path"), follow_parm_reference=False
                )
            elif "Arnold" in self.renderer:
                self.rop.parm("ar_picture").set(
                    self.geo_node.parm("path"), follow_parm_reference=False
                )

            self.cop_out = self.copnet.createNode("null")
            self.cop_out.setInput(0, cop_file)

            self.cop_out.setGenericFlag(hou.nodeFlag.Display, True)
            self.cop_out.setGenericFlag(hou.nodeFlag.Render, True)
            self.cop_out.setName("OUT", True)

    def get_node(self) -> hou.Node:
        """
        Get the currently attached GeoNode
        """
        return self.geo_node
