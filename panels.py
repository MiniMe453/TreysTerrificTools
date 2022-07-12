from bpy.types import Panel, Scene
from bpy.props import StringProperty,BoolProperty,FloatProperty,EnumProperty
from . import operators

class TTT_PT_CollisionSetup(Panel):
    bl_category = "Trey's Terrific Tools"
    bl_label = "Collision Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        row = layout.row()
        row.operator("view3d.ttt_set_collision_properties", text = "Set up Collision Layers")

        row = layout.row()
        row.operator("view3d.ttt_move_obj_to_collection", text="Move objects to collections")