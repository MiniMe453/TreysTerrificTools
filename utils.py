import bpy
import os
import ntpath
import re
import configparser
from random import random

PKG = __package__

def read_resource_database(addonFolders):
    """Reads all items from rdb file, in case rdb file exists"""
    """Returns {"RID":"Absolute Path"}"""
    from struct import unpack

    rdb = {}
    for addon in addonFolders:
        if os.path.isfile(addon.addon_folder + "resourceDatabase.rdb"):
            rd_file = open(addon.addon_folder + "resourceDatabase.rdb", "rb")

            form = rd_file.read(4).decode()
            file_length = unpack("i", rd_file.read(4))
            rdbc = rd_file.read(4).decode()
            cache_file_version = unpack("I", rd_file.read(4))
            file_size = unpack("Q", rd_file.read(8))

            (items_count,) = unpack("I", rd_file.read(4))

            for i in range(0,items_count):
                (strint_length,) = unpack("i", rd_file.read(4))

                relative_path = rd_file.read(strint_length).decode()
                # print(relative_path)

                (item_flag,) = unpack("h", rd_file.read(2))
                # print(item_flag & (1<<0), item_flag & (1<<1), item_flag & (1<<2), item_flag & (1<<3))

                resource_guid = []
                for i in range(0,8):
                    xx = rd_file.read(1)
                    # convert each byte in to hex
                    resource_guid.append(xx.hex())
                # reverse, join items into string and upper case letters
                resource_guid = "".join(resource_guid[::-1]).upper()
                
                if item_flag & (1<<1) == 2:
                    unpack("2I", rd_file.read(4+4))
                    # print("... has metafile")
                if item_flag & (1<<2) == 4:
                    unpack("2I", rd_file.read(4+4))
                    # print("... has resource")
                    rdb[resource_guid] = (addon.addon_folder + relative_path[:-1]).replace("/","\\")

            rd_file.close()
        else:
            print("\"resourceDatabase.rdb\" not found in " + addon.addon_folder)
    return rdb

def show_message_box(messageArray, title = "Trey's Terrific Tools", icon='INFO'):
    def draw(self, context):
        for message in messageArray:
            self.layout.label(text=message)
    
    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

def load_settings(name, isArray = False):
    config = configparser.ConfigParser()
    try:
        config.read(__file__[:-9] + "\\settings.ini")
        returnValue = config['DEFAULT'][name]
        if(isArray):
            returnValue = eval(returnValue)
        return returnValue
    except:
        return ""

def save_settings(name, property):
    config = configparser.ConfigParser()
    try:
        config.read(__file__[:-9] + "\\settings.ini")
        config['DEFAULT'][name] = property
    except:
        print("no settings file found")
    with open(__file__[:-9] + "\\settings.ini", 'w') as configfile:
        config.write(configfile)

def ttt_load_layer_presets_config():
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname,'config/layerpresets.txt')

    f = open(filename)
    file = f.read().split("\n")
    f.close()

    return file

def ttt_get_layer_presets():
    layerPresets = []

    i = 0
    for line in ttt_load_layer_presets_config():
        splitLine = line.split(",")
        layerPresets.append((splitLine[0],splitLine[0],splitLine[1],i))
        i += 1
        print(splitLine[0])
    
    return layerPresets

def ttt_layerspresets_items_callback(self, context):
    items = bpy.types.Scene.ttt_layerpresets_enum
    return items

def ttt_gamemat_items_callback(self, context):
    items = bpy.types.Scene.ttt_gamemats_enum
    return items

def ttt_update_layer_preset_enum(self, context):
    layerPresetIndex = context.scene.ttt_collision_data["ttt_layerpresets"]
    selectedPreset= bpy.types.Scene.ttt_layerpresets_enum[layerPresetIndex][1]
    print(selectedPreset)

def ttt_update_gamemats_enum(self,context):
    gameMatIndex = context.scene.ttt_collision_data["ttt_gamemats"]
    if(gameMatIndex == 0):
        return
    print(bpy.types.Scene.ttt_gamemats_enum[gameMatIndex][2])

def ttt_get_currently_selected_layer_preset(context):
    layerPresetIndex = context.scene.ttt_collision_data["ttt_layerpresets"]
    selectedPreset= bpy.types.Scene.ttt_layerpresets_enum[layerPresetIndex][1]
    return selectedPreset

def ttt_get_gamemats():
    return False

def ttt_assgin_gamemat(name):
    editMode = False
    gamemat = []
    index = 0

    # Some of the operations performed below have to be done in object mode
    # Check if Edit mode is active and store it in variable
    ob = bpy.context.active_object
    if ob.mode == 'EDIT':    
        editMode = True
        bpy.ops.object.mode_set(mode='OBJECT')

    # Check if selected material already exist in the scene
    materials_scene_dict = {mat.name: mat for i, mat, in enumerate(bpy.data.materials)}
    try:
        gamemat = materials_scene_dict[name]
        #print("material in scene found")
    except:
        gamemat = []
        #print("material in scene not found")

    # if wanted gamemat doesnt exist yet, create new one with random color
    if gamemat == []:
        gamemat = bpy.data.materials.new(name)
        gamemat.use_nodes = True
        randomColor = (random(), random(), random(), 1)
        gamemat.diffuse_color = randomColor
        gamemat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = randomColor

        index = len(ob.data.materials)+1

    # separate handling edit & object mode - in edit mode it is possible to asign material to current selection
    if editMode:    
        bpy.ops.object.mode_set(mode='OBJECT')
        polygon_data = ob.data.polygons
        if True in [x.select for x in polygon_data]:
            #print('Faces are Selected')
            bpy.ops.object.mode_set(mode='EDIT')
            # Check if material exist
            if(index == 0):
                materials_ob_dict = {mat.name: i for i, mat in enumerate(ob.data.materials)}
                try:
                    index = materials_ob_dict[name]
                    #print("material in object found")
                except:
                    ob.data.materials.append(gamemat)
                    index = len(ob.data.materials)-1
                    #print("material in object not found")
            else:
                ob.data.materials.append(gamemat)
                index = len(ob.data.materials)-1

            used_mats = [gamemat]
            for polygon in polygon_data:
                used_mats.append(ob.material_slots[polygon.material_index].material)
                #print(polygon.material_index)
                if(polygon.select == True):
                    polygon.material_index = index
                    #print("change to index " + str(index))

            ob.active_material_index = index
            bpy.ops.object.material_slot_assign()
            
            # Delete unused materials
            for idx, ms in enumerate(ob.material_slots):
                if not(ms.material in used_mats):
                    bpy.ops.object.mode_set(mode='OBJECT')
                    bpy.context.object.active_material_index = idx
                    bpy.ops.object.material_slot_remove()
                    bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.object.mode_set(mode='EDIT')
        else:
            print('No Faces Selected')
            bpy.ops.object.mode_set(mode='EDIT')
    else:
        selected = list(bpy.context.view_layer.objects.selected)

        for ob in selected:  # for selected objests delete all material slots and append wanted gamemat
            if ob.data.materials:
                ob.data.materials.clear()
            ob.data.materials.append(gamemat)

def ttt_update_gamemats(context):
    gameMatIndex = context.scene.ttt_collision_data["ttt_gamemats"]
    if(gameMatIndex == 0):
        return
    ttt_assgin_gamemat(bpy.types.Scene.ttt_gamemats_enum[gameMatIndex][2])

def ttt_get_game_materials():
    gamematerials = {}
    gamematerialsTemp = {}
    addonFolders = bpy.context.preferences.addons[PKG].preferences.addonfolders
    valid_folder = False

    for addon in addonFolders:
        if os.path.isdir(addon.addon_folder):
            valid_folder = True

    if not valid_folder:
        return gamematerialsTemp
        
    rdb = read_resource_database(addonFolders)
    for guid in rdb:
        filename = rdb[guid]
        if filename.lower().endswith('.gamemat'):
            name = os.path.basename(filename)
            name = name.replace(".gamemat","")
            name = name.capitalize()
            name_vis = name.replace("_"," ")
            #print(filename)
            gamematerials[name] = [name.lower() + "_" + guid.lower(),name_vis, name + "_" + guid]
    for i in sorted (gamematerials) :
        gamematerialsTemp[i] = gamematerials[i]
    return gamematerialsTemp