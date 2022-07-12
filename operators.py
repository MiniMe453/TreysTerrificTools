import bpy
from enum import Enum
from . import utils

#class CollisionTypes(Enum):
 #   Sphere = 1
  #  Capsule = 2
   # Cylinder = 3
    #Box = 4
    #sConvex_Hull = 5

class TTT_OT_TestOperator(bpy.types.Operator):
    bl_idname = "view3d.ttt_test_operator"
    bl_label = "Test operator"
    bl_description = "Run a test"
    bl_options = {"REGISTER","UNDO"}

    testitems_enum : bpy.props.EnumProperty(
        name="Collision Layers",
        description="select an option",
        items=[
            ("01","FireGeo",""),
            ("02","Dynamic",""),
            ("03","Car",""),
            ("04","BuildingFire",""),
            ("05","Building","")
        ]
    )

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self,"testitems_enum")

class TTT_OT_TestCollisionEnum(bpy.types.Operator):
    bl_idname = "view3d.ttt_set_collision_properties"
    bl_label = "Set collision properties"
    bl_description = "change a mesh value"
    bl_options = {"REGISTER","UNDO"}

    def execute(self,context):
        selected = list(bpy.context.view_layer.objects.selected)
        generatedColliders = []

        for obj in selected:
            colliderObj = utils.ttt_generate_collider(context, obj)
            utils.ttt_update_gamemats(context, colliderObj)
            colliderObj["CollisionLayer"] = utils.ttt_get_currently_selected_layer_preset(context)
            generatedColliders.append(colliderObj)
    
        return{'FINISHED'}
    
    def invoke(self, context, event):
        selected = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
        if(selected == []):
            utils.show_message_box(["No object is selected!"])
            return {'CANCELLED'}
       
        layerPresets = utils.ttt_get_layer_presets()
        bpy.types.Scene.ttt_layerpresets_enum = layerPresets

        enum_gamemats_items = []
        enum_gamemats_items.append(("None","None","",0))
        gamematerials = utils.ttt_get_game_materials()
        i = 1
        for materials in gamematerials:
            enum_gamemats_items.append((gamematerials[materials][0],gamematerials[materials][1],gamematerials[materials][2],i))
            i += 1

        bpy.types.Scene.ttt_gamemats_enum = enum_gamemats_items

        enum_collidertypes_items = utils.ttt_get_collider_types()
        bpy.types.Scene.ttt_collider_types_enum = enum_collidertypes_items

        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        box = row.box()
        box.alignment = "CENTER"
        box.prop(context.scene.ttt_collision_data, "ttt_collidertypes")
        box.prop(context.scene.ttt_collision_data, "ttt_gamemats")
        box.prop(context.scene.ttt_collision_data, "ttt_layerpresets")

class TTT_ColliderEnumItems(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        bpy.types.Scene.ttt_collision_data = bpy.props.PointerProperty(type=TTT_ColliderEnumItems)

    @classmethod
    def unregister(cls):
        del bpy.types.Scene.ttt_collision_data

    ttt_gamemats : bpy.props.EnumProperty(items=utils.ttt_gamemat_items_callback, name = "Game Material", update = utils.ttt_update_gamemats_enum)
    ttt_layerpresets : bpy.props.EnumProperty(items=utils.ttt_layerspresets_items_callback, name = "Layer Presets", update = utils.ttt_update_layer_preset_enum)
    ttt_collidertypes : bpy.props.EnumProperty(items=utils.ttt_collider_types_callback, name = "Collider Types", update = utils.ttt_collider_types_update)