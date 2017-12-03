# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
	"name": "3DM Snow",
	"category": "3DMish",
	"author": "3DMish (Mish7913@gmail.com)",
	"version": (0, 1, 1),
	"blender": (2, 78, 5),
	"wiki_url": "",
	"tracker_url": "",
	"description": "Generate snow on mesh.",
	}

import bpy, math, bmesh, time
from mathutils import Vector
from bpy.props import *

def initSceneProperties():
	bpy.types.Scene.SnowQuantity = IntProperty(name = "Quantity", description = "Enter a Quantity", default = 1, min = 0, max = 100)
	bpy.types.Scene.SnowThickness = FloatProperty(name = "Thickness", description = "Enter a Thickness", default = 50, min = 1, max = 100)
	bpy.types.Scene.SnowSensitivity = FloatProperty(name = "Sensitivity", description = "Enter a Sensitivity", default = 0, min = 0, max = 1.0)
	return
initSceneProperties()

class MishSnowPanel(bpy.types.Panel):   
	bl_category 	= "3DMish"
	bl_label		= "3DM Snow"
	bl_space_type   = "VIEW_3D"
	bl_region_type  = "TOOLS"
	
	def draw(self, context):
		Mcol = self.layout.column(align=True)
		
		Mcol.prop(context.scene, 'SnowQuantity')
		Mcol.prop(context.scene, 'SnowThickness')
		Mcol.prop(context.scene, 'SnowSensitivity')
		Gcol = Mcol.row(align=True)
		Gcol.operator("3dmish.createsnow", text="Create snow", icon="FREEZE")
		Gcol.operator("3dmish.addsnowmaterial", text="", icon="MATERIAL_DATA")
		
class MishAddSnowMaterial(bpy.types.Operator):
	bl_idname   	= '3dmish.addsnowmaterial'
	bl_label		= 'Add Snow'
	bl_description  = 'Add Snow Material On Selected Object'

	def execute(self, context):
		if (bpy.context.selected_objects):
			if (bpy.context.scene.render.engine == 'CYCLES'):
				for obj in bpy.context.selected_objects:
					obj.data.materials.clear()
					obj.data.materials.append(MishSnowMaterialCycles())
			elif (bpy.context.scene.render.engine == 'BLENDER_RENDER'):
				for obj in bpy.context.selected_objects:
					obj.data.materials.clear()
					obj.data.materials.append(MishSnowMaterialBlenderRender())
		return {'FINISHED'}

class MishCreateSnow(bpy.types.Operator):
	bl_idname   	= '3dmish.createsnow'
	bl_label		= 'Create snow'
	bl_description  = 'Create snow on mesh'

	def execute(self, context):
		if (bpy.context.selected_objects):
			sobj = bpy.context.active_object;
			if (bpy.context.active_object == bpy.context.selected_objects[len(bpy.context.selected_objects)-1]):
				bpy.ops.object.duplicate(); bpy.ops.object.convert(target='MESH'); bpy.ops.object.join();
				robj = bpy.context.active_object; bpy.ops.object.duplicate(); bobj = bpy.context.active_object;
				bpy.ops.object.select_all(action='DESELECT'); robj.select = True; bpy.ops.object.mode_set(mode = 'EDIT');
				obj = bpy.context.active_object;

				bm = bmesh_copy_from_object(obj, transform=True, triangulate=False); bm.normal_update()
				fo = [ele.index for ele in bm.faces if Vector((0, 0, -1.0)).angle(ele.normal, 4.0) < ((math.pi / 2.0) - (bpy.context.scene.SnowSensitivity - 0.5))]
				bpy.ops.mesh.select_all(action='DESELECT'); obj_e = bpy.context.edit_object
				
				for i in fo:
					mesh = bmesh.from_edit_mesh(obj_e.data)
					for fm in mesh.faces:
						if (fm.index == i):
							fm.select = True
					bmesh.update_edit_mesh(obj_e.data, True)
				
				bme = bmesh.from_edit_mesh(obj_e.data); faces_select = [f for f in bme.faces if f.select] 
				bmesh.ops.delete(bme, geom=faces_select, context=5); bmesh.update_edit_mesh(obj_e.data, True)
				bpy.ops.object.mode_set(mode = 'OBJECT')
				m3dball = bpy.data.metaballs.new("3dmSnowball")
				m3dballobj = bpy.data.objects.new("3dmSnowballObject", m3dball)
				bpy.context.scene.objects.link(m3dballobj)
				m3dball.resolution = (bpy.context.scene.SnowThickness / 30)+0.01; m3dball.render_resolution = 0.2; m3dball.threshold = 1.3
				element = m3dball.elements.new()
				element.co = [0.0, 0.0, 0.0]; element.radius = 1.5; element.stiffness = 0.75
				m3dballobj.scale = [0.09, 0.09, 0.09];
				
				bpy.context.scene.objects.active = obj; bpy.ops.object.particle_system_add()
				m3dPsys = obj.particle_systems[-1]; m3dPsys.name = '3DM.Snow'
				
				m3dPset = m3dPsys.settings; m3dPset.type = 'HAIR'; m3dPset.name = '3DM.SnowSystem'
				m3dPset.hair_length = ( (obj.dimensions[0] + obj.dimensions[1] + obj.dimensions[2])-(bpy.context.scene.SnowThickness / 100)+0.01 )
				m3dPset.use_render_emitter = True; m3dPset.render_type = 'OBJECT'; m3dPset.dupli_object = m3dballobj
				m3dPset.particle_size = (bpy.context.scene.SnowThickness / 100)+0.01
				m3dPset.child_type = 'INTERPOLATED'
				m3dPset.child_nbr = bpy.context.scene.SnowQuantity

				
				bpy.ops.object.select_all(action='DESELECT');
				m3dSnowMesh = m3dballobj.to_mesh(bpy.context.scene, False, 'PREVIEW')
				m3dSnowObj = bpy.data.objects.new("3dmSnow", m3dSnowMesh)
				bpy.context.scene.objects.link(m3dSnowObj); m3dSnowObj.scale = [0.09, 0.09, 0.09];
				m3dSnowObj.select = True;
				bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY'); bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
				
				bpy.ops.object.select_all(action='DESELECT');
				obj.select = True; bpy.ops.object.particle_system_remove(); obj.select = True; bpy.ops.object.delete();
				bpy.ops.object.select_all(action='DESELECT');
				m3dballobj.select = True; bpy.ops.object.delete();
				
				bpy.ops.object.select_all(action='DESELECT'); sobj.select = True;
				
				bpy.ops.object.select_all(action='DESELECT'); bobj.select = True; bpy.ops.object.delete();
				bpy.ops.object.select_all(action='DESELECT'); robj.select = True; bpy.ops.object.delete();
				bpy.ops.object.select_all(action='DESELECT'); m3dSnowObj.select = True;
				
				m3dSnowObj.modifiers.new("3DM Decimate", 'DECIMATE');
				m3dSnowObj.modifiers["3DM Decimate"].ratio = 0.5
				m3dSnowObj.modifiers["3DM Decimate"].show_expanded = False
				m3dSnowObj.modifiers.new("3DM Subsurf", 'SUBSURF');
				m3dSnowObj.modifiers["3DM Subsurf"].show_viewport = False
				m3dSnowObj.modifiers["3DM Subsurf"].show_expanded = False

		return {'FINISHED'}

def MishSnowMaterialBlenderRender():
	m3dSnow = bpy.data.materials.new("3dmSnow"); m3dSnow.diffuse_color  = (1, 1, 1);  m3dSnow.diffuse_shader  = 'LAMBERT';
	m3dSnow.diffuse_intensity  = 1.0; m3dSnow.specular_color = (1, 1, 1); m3dSnow.specular_shader = 'COOKTORR';
	m3dSnow.specular_intensity = 0; m3dSnow.specular_hardness = 5; m3dSnow.alpha = 1; m3dSnow.use_shadeless = 0; m3dSnow.ambient = 1;
	
	m3dSnowTextureClouds = bpy.data.textures.new('3dmSnowTextureClouds', type = 'CLOUDS');
	m3dSnowTextureClouds.noise_scale = 0.0001
	m3dSnowTextureClouds.noise_depth = 6
	m3dSnowTextureClouds.contrast = 5
	m3dSnowTextureClouds.intensity = 0
	m3dSnow.texture_slots.add().texture = m3dSnowTextureClouds;

	m3dSnow.texture_slots[0].texture_coords = 'OBJECT'
	m3dSnow.texture_slots[0].use_map_color_diffuse = False
	m3dSnow.texture_slots[0].use_map_specular = True
	m3dSnow.texture_slots[0].specular_factor = 1

	m3dSnowTextureClouds2 = bpy.data.textures.new('3dmSnowTextureClouds2', type = 'CLOUDS');
	m3dSnowTextureClouds2.noise_scale = 0.1
	m3dSnowTextureClouds2.noise_depth = 3
	m3dSnow.texture_slots.add().texture = m3dSnowTextureClouds2;

	m3dSnow.texture_slots[1].texture_coords = 'OBJECT'
	m3dSnow.texture_slots[1].use_map_color_diffuse = False
	m3dSnow.texture_slots[1].normal_factor = 0.05
	m3dSnow.texture_slots[1].use_map_normal = True

	return m3dSnow

def MishSnowMaterialCycles():
	m3dSnow = bpy.data.materials.new("3dmSnow"); m3dSnow.use_nodes = True;
	m3dSnowNodes = m3dSnow.node_tree.nodes
	m3dSnowLinks = m3dSnow.node_tree.links

	while(m3dSnowNodes): m3dSnowNodes.remove(m3dSnowNodes[0])
	
	m3dSnowOut  = m3dSnowNodes.new("ShaderNodeOutputMaterial")
	m3dSnowOut.location = 680, 100
	m3dSnowGlossy = m3dSnowNodes.new("ShaderNodeBsdfGlossy")
	m3dSnowGlossy.location = -80, 60
	m3dSnowGlossy.inputs[1].default_value = 0.5
	m3dSnowDiffuse = m3dSnowNodes.new("ShaderNodeBsdfDiffuse")
	m3dSnowDiffuse.location = -80, 200
	m3dSnowMixShader1 = m3dSnowNodes.new("ShaderNodeMixShader")
	m3dSnowMixShader1.location = 120, 180
	m3dSnowMixShader1.inputs[0].default_value = 0.5
	m3dSnowAddShader = m3dSnowNodes.new("ShaderNodeAddShader")
	m3dSnowAddShader.location = 300, 160
	m3dSnowAddReroute1 = m3dSnowNodes.new("NodeReroute")
	m3dSnowAddReroute1.location = -100, 80
	m3dSnowAddReroute2 = m3dSnowNodes.new("NodeReroute")
	m3dSnowAddReroute2.location = -100, -40
	m3dSnowMixShader2 = m3dSnowNodes.new("ShaderNodeMixShader")
	m3dSnowMixShader2.location = 500, 140
	m3dSnowMixShader2.inputs[0].default_value = 0.2
	m3dSnowMixMath = m3dSnowNodes.new("ShaderNodeMath")
	m3dSnowMixMath.location = 500, 0
	m3dSnowMixMath.operation = 'MULTIPLY'
	m3dSnowMixMath.inputs[1].default_value = 0.5
	m3dSnowMixSubsurface = m3dSnowNodes.new("ShaderNodeSubsurfaceScattering")
	m3dSnowMixSubsurface.location = 300, 40
	m3dSnowMixSubsurface.falloff = 'CUBIC'
	m3dSnowMixSubsurface.inputs[1].default_value = 0.1
	m3dSnowAddReroute3 = m3dSnowNodes.new("NodeReroute")
	m3dSnowAddReroute3.location = 280, -180
	m3dSnowAddReroute4 = m3dSnowNodes.new("NodeReroute")
	m3dSnowAddReroute4.location = 460, -180
	m3dSnowAddNoise1 = m3dSnowNodes.new("ShaderNodeTexNoise")
	m3dSnowAddNoise1.location = 120, 40
	m3dSnowAddNoise1.inputs[1].default_value = 4
	m3dSnowAddNoise1.inputs[2].default_value = 16
	m3dSnowMixShader3 = m3dSnowNodes.new("ShaderNodeMixShader")
	m3dSnowMixShader3.location = 120, -140
	m3dSnowAddReroute5 = m3dSnowNodes.new("NodeReroute")
	m3dSnowAddReroute5.location = -300, -100
	m3dSnowAddReroute6 = m3dSnowNodes.new("NodeReroute")
	m3dSnowAddReroute6.location = 80, -100
	m3dSnowAddReroute7 = m3dSnowNodes.new("NodeReroute")
	m3dSnowAddReroute7.location = -260, -120
	m3dSnowAddReroute8 = m3dSnowNodes.new("NodeReroute")
	m3dSnowAddReroute8.location = 80, -120
	m3dSnowGlossy2 = m3dSnowNodes.new("ShaderNodeBsdfGlossy")
	m3dSnowGlossy2.location = -80, -140
	m3dSnowGlossy2.inputs[1].default_value = 0.2
	m3dSnowTransparent = m3dSnowNodes.new("ShaderNodeBsdfTransparent")
	m3dSnowTransparent.location = -80, -300
	m3dSnowBump = m3dSnowNodes.new("ShaderNodeBump")
	m3dSnowBump.location = -260, 200
	m3dSnowBump.inputs[0].default_value = 0.1
	m3dSnowNormalMap = m3dSnowNodes.new("ShaderNodeNormalMap")
	m3dSnowNormalMap.location = -260, -140
	m3dSnowAddNoise2 = m3dSnowNodes.new("ShaderNodeTexNoise")
	m3dSnowAddNoise2.location = -460, 200
	m3dSnowAddNoise2.inputs[1].default_value = 150
	m3dSnowAddNoise2.inputs[2].default_value = 2
	m3dSnowAddVoronoi = m3dSnowNodes.new("ShaderNodeTexVoronoi")
	m3dSnowAddVoronoi.location = -460, 0
	m3dSnowAddVoronoi.coloring = 'CELLS'
	m3dSnowAddVoronoi.inputs[1].default_value = 200
	m3dSnowAddReroute9 = m3dSnowNodes.new("NodeReroute")
	m3dSnowAddReroute9.location = -300, -160
	m3dSnowAddReroute10 = m3dSnowNodes.new("NodeReroute")
	m3dSnowAddReroute10.location = -480, -160
	m3dSnowAddReroute11 = m3dSnowNodes.new("NodeReroute")
	m3dSnowAddReroute11.location = -480, -100
	m3dSnowAddReroute12 = m3dSnowNodes.new("NodeReroute")
	m3dSnowAddReroute12.location = -480, 100
	m3dSnowAddReroute13 = m3dSnowNodes.new("NodeReroute")
	m3dSnowAddReroute13.location = -280, -40
	m3dSnowAddReroute14 = m3dSnowNodes.new("NodeReroute")
	m3dSnowAddReroute14.location = -280, -240
	m3dSnowAddTexCoord = m3dSnowNodes.new("ShaderNodeTexCoord")
	m3dSnowAddTexCoord.location = -640, 200

	m3dSnowLinks.new(m3dSnowMixShader1.inputs[1], m3dSnowDiffuse.outputs['BSDF'])
	m3dSnowLinks.new(m3dSnowMixShader1.inputs[2], m3dSnowGlossy.outputs['BSDF'])
	m3dSnowLinks.new(m3dSnowAddShader.inputs[0], m3dSnowMixShader1.outputs['Shader'])
	m3dSnowLinks.new(m3dSnowAddShader.inputs[1], m3dSnowMixShader3.outputs['Shader'])
	m3dSnowLinks.new(m3dSnowGlossy2.inputs[2], m3dSnowNormalMap.outputs['Normal'])
	m3dSnowLinks.new(m3dSnowBump.inputs[2], m3dSnowAddNoise2.outputs['Fac'])
	m3dSnowLinks.new(m3dSnowAddReroute1.inputs[0], m3dSnowBump.outputs['Normal'])
	m3dSnowLinks.new(m3dSnowAddReroute2.inputs[0], m3dSnowAddReroute1.outputs[0])
	m3dSnowLinks.new(m3dSnowAddReroute7.inputs[0], m3dSnowAddVoronoi.outputs[1])
	m3dSnowLinks.new(m3dSnowAddReroute12.inputs[0], m3dSnowAddTexCoord.outputs['Object'])
	m3dSnowLinks.new(m3dSnowAddReroute6.inputs[0], m3dSnowAddReroute5.outputs[0])
	m3dSnowLinks.new(m3dSnowAddReroute5.inputs[0], m3dSnowAddReroute9.outputs[0])
	m3dSnowLinks.new(m3dSnowAddReroute14.inputs[0], m3dSnowAddReroute13.outputs[0])
	m3dSnowLinks.new(m3dSnowNormalMap.inputs[1], m3dSnowAddReroute14.outputs[0])
	m3dSnowLinks.new(m3dSnowAddVoronoi.inputs[0], m3dSnowAddReroute11.outputs[0])
	m3dSnowLinks.new(m3dSnowAddReroute13.inputs[0], m3dSnowAddVoronoi.outputs[0])
	m3dSnowLinks.new(m3dSnowAddReroute9.inputs[0], m3dSnowAddReroute10.outputs[0])
	m3dSnowLinks.new(m3dSnowAddReroute10.inputs[0], m3dSnowAddReroute11.outputs[0])
	m3dSnowLinks.new(m3dSnowAddReroute11.inputs[0], m3dSnowAddReroute12.outputs[0])
	m3dSnowLinks.new(m3dSnowAddNoise2.inputs[0], m3dSnowAddReroute12.outputs[0])
	m3dSnowLinks.new(m3dSnowAddReroute8.inputs[0], m3dSnowAddReroute7.outputs[0])
	m3dSnowLinks.new(m3dSnowMixShader3.inputs[0], m3dSnowAddReroute8.outputs[0])
	m3dSnowLinks.new(m3dSnowMixShader3.inputs[1], m3dSnowGlossy2.outputs['BSDF'])
	#m3dSnowLinks.new(m3dSnowMixShader3.inputs[2], m3dSnowTransparent.outputs['BSDF'])
	m3dSnowLinks.new(m3dSnowAddNoise1.inputs[0], m3dSnowAddReroute6.outputs[0])
	m3dSnowLinks.new(m3dSnowDiffuse.inputs[2], m3dSnowAddReroute1.outputs[0])
	m3dSnowLinks.new(m3dSnowGlossy.inputs[2], m3dSnowAddReroute2.outputs[0])
	m3dSnowLinks.new(m3dSnowMixShader2.inputs[1], m3dSnowAddShader.outputs['Shader'])
	m3dSnowLinks.new(m3dSnowMixShader2.inputs[2], m3dSnowMixSubsurface.outputs['BSSRDF'])
	m3dSnowLinks.new(m3dSnowOut.inputs[0], m3dSnowMixShader2.outputs['Shader'])
	m3dSnowLinks.new(m3dSnowOut.inputs[2], m3dSnowMixMath.outputs['Value'])
	m3dSnowLinks.new(m3dSnowAddReroute4.inputs[0], m3dSnowAddReroute3.outputs[0])
	m3dSnowLinks.new(m3dSnowMixMath.inputs[0], m3dSnowAddReroute4.outputs[0])
	m3dSnowLinks.new(m3dSnowAddReroute3.inputs[0], m3dSnowAddNoise1.outputs['Fac'])
	
	return m3dSnow

def bmesh_copy_from_object(obj, transform=True, triangulate=True, apply_modifiers=False):
	assert(obj.type == 'MESH')

	if apply_modifiers and obj.modifiers:
		import bpy
		me = obj.to_mesh(bpy.context.scene, True, 'PREVIEW', calc_tessface=False)
		bm = bmesh.new(); bm.from_mesh(me); bpy.data.meshes.remove(me)
		del bpy
	else:
		me = obj.data
		if obj.mode == 'EDIT': bm_orig = bmesh.from_edit_mesh(me); bm = bm_orig.copy()
		else: bm = bmesh.new(); bm.from_mesh(me)

	if transform: bm.transform(obj.matrix_world)
	if triangulate: bmesh.ops.triangulate(bm, faces=bm.faces)
	return bm
	
def register():
	bpy.utils.register_class(MishCreateSnow)
	bpy.utils.register_class(MishSnowPanel)
	bpy.utils.register_class(MishAddSnowMaterial)

def unregister():
	bpy.utils.unregister_class(MishCreateSnow)
	bpy.utils.unregister_class(MishSnowPanel)
	bpy.utils.unregister_class(MishAddSnowMaterial)

if __name__ == "__main__":
	register()
