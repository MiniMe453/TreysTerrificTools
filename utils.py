import bpy
import os
import ntpath
import re
import configparser
from random import random
import bmesh
from mathutils import Vector, Matrix
from scipy.fft import get_workers

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

def ttt_load_config_file(filen):
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname,'config/',filen)

    f = open(filename)
    file = f.read().split("\n")
    f.close()

    return file

def ttt_get_layer_presets():
    layerPresets = []

    i = 0
    for line in ttt_load_config_file('layerpresets.txt'):
        splitLine = line.split(",")
        layerPresets.append((splitLine[0],splitLine[0],splitLine[1],i))
        i += 1
    
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

def ttt_assgin_gamemat(name, obj):
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
        if obj.data.materials:
            obj.data.materials.clear()
        obj.data.materials.append(gamemat)

def ttt_update_gamemats(context, obj):
    gameMatIndex = context.scene.ttt_collision_data["ttt_gamemats"]
    if(gameMatIndex == 0):
        return
    ttt_assgin_gamemat(bpy.types.Scene.ttt_gamemats_enum[gameMatIndex][2],obj)

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

def ttt_get_collider_types():
    collidertypes = []

    i = 0
    for line in ttt_load_config_file('collidertypes.txt'):
        splitLine = line.split(",")
        collidertypes.append((splitLine[0],splitLine[1],splitLine[2],i))
        i += 1

    return collidertypes

def ttt_collider_types_callback(self, context):
    types = bpy.types.Scene.ttt_collider_types_enum
    return types

def ttt_collider_types_update(self, context):
    print("Collider Option Changed")

def ttt_generate_collider(context, obj):
    colliderTypeIndex = context.scene.ttt_collision_data["ttt_collidertypes"]
    selectedCollider = bpy.types.Scene.ttt_collider_types_enum[colliderTypeIndex][0]

    if(selectedCollider == "UCX"):
        return convexhull_collider(selectedCollider, obj)
    elif(selectedCollider == "UBX"):
        return box_collider(selectedCollider,obj)
    elif(selectedCollider == "USP"):
        return sphere_collider(selectedCollider,obj)
    else:
        print(selectedCollider)
        return obj

def box_collider(selectedCollider,obj):
    #[[dx,dy,dz],[minx,miny,minz],[maxx,maxy,maxz]]
    objSize = get_object_size(obj)

    new_name = "%s_%s" % (selectedCollider, obj.name)
    
    loc =  get_object_world_location(obj)
    
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=obj.rotation_euler)
    collider = bpy.context.object
    
    collider.name = new_name
    collider.dimensions = Vector((objSize[0][0], objSize[0][1], objSize[0][2]))
    
    return collider

#Code from Martynas Žiemys - https://blender.stackexchange.com/users/60759/martynas-%c5%bdiemys
def convexhull_collider(selectedCollider, obj):
    context = bpy.context
    scene = context.scene
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    copy = obj.copy()

    me = bpy.data.meshes.new("%s convexhull" % me.name)
    ch = bmesh.ops.convex_hull(bm, input=bm.verts,use_existing_faces=True)
    bmesh.ops.delete(
            bm,
            geom=ch["geom_unused"] + ch["geom_interior"] + ch["geom_holes"],
            context='VERTS',
            )
    bm.to_mesh(me)
    copy.name = "%s_%s" % (selectedCollider, obj.name)
    copy.data = me

    print(obj.users_collection)

    obj.users_collection[0].objects.link(copy)

    return copy

def sphere_collider(selectedCollider, obj):
    #X, Y, Z
    objSize = get_object_size(obj)[0]
    objRadius = max(objSize)/2
    location = get_object_world_location(obj)

    # Create an empty mesh and the object.
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=objRadius,location=location,rotation=obj.rotation_euler)
    collider = bpy.context.object

    collider.name = "%s_%s" % (selectedCollider,obj.name)

    return collider

def cylinder_collider(selectedCollider, obj):
    #X, Y, Z
    objSize = get_object_size(obj)[0]
    objRadius = max(objSize)/2
    location = get_object_world_location(obj)



    collider = bpy.context.object

    collider.name = "%s_%s" % (selectedCollider,obj.name)

    return collider

def get_object_size(obj):
    scale = obj.scale
    
    minx = obj.bound_box[0][0] * scale.x
    maxx = obj.bound_box[4][0] * scale.x
    miny = obj.bound_box[0][1] * scale.y
    maxy = obj.bound_box[2][1] * scale.y
    minz = obj.bound_box[0][2] * scale.z
    maxz = obj.bound_box[1][2] * scale.z
    dx = maxx - minx
    dy = maxy - miny
    dz = maxz - minz

    return [[dx,dy,dz],[minx,miny,minz],[maxx,maxy,maxz]]

def get_object_world_location(obj):
    objSize = get_object_size(obj)

    loc = Vector(((objSize[1][0] + 0.5* objSize[0][0]), (objSize[1][1] + 0.5* objSize[0][1]), (objSize[1][2] + 0.5* objSize[0][2])))
    loc.rotate(obj.rotation_euler)
    loc = loc + obj.location

    return loc



def ttt_get_selection_masks():
    selectionMasks = []

    i = 0
    
    for line in ttt_load_config_file("selectionmasks.txt"):
        selectionMasks.append((line, line, line, i))
        i += 1
    
    return selectionMasks

def ttt_selection_masks_callback(self, context):
    items = bpy.types.Scene.ttt_selectionmask_enum
    return items

def ttt_get_selection_mask(context):
    selectionMaskIndex = context.scene.ttt_collision_data["ttt_selectionmasks"]
    selectedMask = bpy.types.Scene.ttt_selectionmask_enum[selectionMaskIndex][0]
    return selectedMask

def ttt_selection_masks_update(self, context):
    selectionMaskIndex = context.scene.ttt_collision_data["ttt_selectionmasks"]
    selectedMask = bpy.types.Scene.ttt_selectionmask_enum[selectionMaskIndex][0]
    
    
    print(selectedMask)
    
    objs = bpy.context.selectable_objects

    for o in objs:
        o.select_set(False)

    if(selectedMask == "None"):
        return
    elif(selectedMask != "Colliders"):
        objs = [obj for obj in bpy.context.view_layer.objects if obj.name.find(selectedMask) != -1] 
    else:
        objs = [obj for obj in bpy.context.view_layer.objects if obj.name.find("_") == 3] 
            
 
    for o in objs:
        o.select_set(True)
