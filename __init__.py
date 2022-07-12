#This requires the BlenderEnfusionTools-Data from Bohemia Interactive
#to work properly. 
#
#Special thanks to Bohemia for provided many of the functions used
#inside this code.

bl_info = {
    "name" : "Trey's Terrific Tools",
    "author" : "Trey Ramm",
    "description" : "",
    "blender" : (2, 80, 0),
    "version" : (0, 0, 1),
    "location" : "",
    "warning" : "",
    "category" : "Generic"
}

from bpy.types import AddonPreferences, Operator
from bpy.props import StringProperty, EnumProperty, CollectionProperty, IntProperty, BoolProperty

# # ----------------------------------------------
# # Import modules
# # ----------------------------------------------
if "bpy" in locals():
    import imp

    imp.reload(utils)
    imp.reload(operators)
    imp.reload(panels)
   # imp.reload(overlays)
    #imp.reload(p3d_import.import_operators)
    #imp.reload(Shaders.pbrbasic_panel)
    #imp.reload(Shaders.pbrmulti_panel)
    #imp.reload(Shaders.pbrdecal_panel)
    #imp.reload(Shaders.pbrbasicglass_panel)
    #imp.reload(Shaders.pbrbasic_props)
    #imp.reload(Shaders.pbrmulti_props)
    #imp.reload(Shaders.pbrdecal_props)
    #imp.reload(Shaders.pbrbasicglass_props)
    print("Trey's Terrific Tools: Reloaded multifiles")
else:
    from . import operators
    from . import panels
    from . import utils
    #from . import overlays
    ##from . p3d_import import import_operators
    #from . Shaders import pbrbasic_panel, pbrdecal_panel, pbrmulti_panel, pbrbasicglass_panel
    #from . Shaders import pbrbasic_props, pbrdecal_props, pbrmulti_props, pbrbasicglass_props

import bpy
# from . import utils
# from . import panels
# from . import operators

#from .utils import update_debug_channel, load_settings, save_settings

PKG = __package__

class TTT_OT_AddAddonFolder(Operator):
    bl_idname = "preferences.add_addon_folder"
    bl_label = "Add Addon Folder"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        addon_prefs = context.preferences.addons[PKG].preferences
        emptySlot = False
        for fp in addon_prefs.addonfolders:
            if fp.addon_folder == "":
                emptySlot = True
        if not emptySlot:
            item = addon_prefs.addonfolders.add()

        return {'FINISHED'}

class TTT_OT_RemoveAddonFolder(Operator):
    bl_idname = "preferences.remove_addon_folder"
    bl_label = "Add Addon Folder"
    bl_options = {"REGISTER", "UNDO"}

    index : IntProperty()
    
    def execute(self, context):
        addon_prefs = context.preferences.addons[PKG].preferences
        if len(addon_prefs.addonfolders) == 1:
            # if there's only on item left don't remove it, just clear string property
            addon_prefs.addonfolders[0].addon_folder = ""
        else:
            addon_prefs.addonfolders.remove(self.index)
        return {'FINISHED'}


class TTT_Enf_Addon_Folders(bpy.types.PropertyGroup):
    addon_folder: StringProperty(subtype='DIR_PATH')

class TTT_Preferences(AddonPreferences):
    bl_idname = __name__

    materialConversionPath: StringProperty(
        name="Material conversion table",
        subtype='FILE_PATH',
        default=__file__[:-12] + "\\p3d_import\\data\\conversion_gameMaterials.txt",
        )

    addonfolders: CollectionProperty(name="File paths",type=TTT_Enf_Addon_Folders)

    # https://blender.stackexchange.com/questions/220630/how-do-i-add-a-list-of-paths-in-the-blender-preferences-manually
            
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "materialConversionPath")

        box = layout.box()
        box.label(text="Addon Folders:")
        for i, addon in enumerate(self.addonfolders):
            row = box.row()
            row.alert = not addon.addon_folder
            row.prop(addon,"addon_folder",text="")
            row.operator("preferences.remove_addon_folder", text="", icon='X', emboss=False).index = i

        row = box.row()
        row.alignment = 'RIGHT'
        row.operator("preferences.add_addon_folder", text="", icon='ADD')
        
        # Check if default values are used. If not, update settings stored in config.ini
        if( self.materialConversionPath == __file__[:-12] + "\\p3d_import\\data\\conversion_gameMaterials.txt"):
            setting = utils.load_settings("materialConversionFile")
            if setting != "" :
                self.materialConversionPath = setting
        else:
            utils.save_settings("materialConversionPath",self.materialConversionPath)

        # Save or restore previous addon folders
        # if(len(self.addonfolders) == 0):
        #     setting = utils.load_settings("addonfolders",True)
        #     if setting != [] :
        #         i = 0
        #         for addon in setting:
        #             self.addonfolders.add()
        #             self.addonfolders[i].addon_folder = addon
        #             i += 1
        # else:        
        #     addons_array = []    
        #     for addon in self.addonfolders:
        #         addons_array.append(addon.addon_folder)
        #     utils.save_settings("addonfolders",str(addons_array))

classes = [
    TTT_Enf_Addon_Folders,
    TTT_OT_AddAddonFolder,
    TTT_OT_RemoveAddonFolder,
    TTT_Preferences,
    operators.TTT_ColliderEnumItems,
    operators.TTT_OT_TestOperator,
    operators.TTT_OT_TestCollisionEnum,
    operators.TTT_MoveObjectsToCollection,
    panels.TTT_PT_CollisionSetup
    
]

def register():

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():

    for cls in classes:
        bpy.utils.unregister_class(cls)
