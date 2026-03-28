import bpy
import random

FLOWER_COLLECTION = "Generated_Flowers"

TREE_LEAF_OBJECT_PREFIX = "leaf_tree"
BUSH_OBJECT_PREFIX = "bush"
BUSH_LEAF_INPUT = "Input_6"
BUSH_LEAF_AMOUNT_VISIBLE = 0.45454543828964233

def clear_animation_for_collection(collection_name):
    col = bpy.data.collections.get(collection_name)
    if col is None:
        return
    for obj in col.objects:
        if obj.animation_data:
            obj.animation_data_clear()

def animate_collection_growth(collection_name, start_frame, end_frame, start_scale=0.01, random_offset=0):
    col = bpy.data.collections.get(collection_name)
    if col is None:
        raise RuntimeError(f"Collection '{collection_name}' not found")

    for obj in col.objects:
        if obj.type not in {"MESH", "EMPTY", "CURVE", "ARMATURE"}:
            continue

        original_scale = obj.scale.copy()
        offset = random.randint(0, random_offset) if random_offset > 0 else 0

        f1 = start_frame + offset
        f2 = end_frame + offset

        obj.scale = (start_scale, start_scale, start_scale)
        obj.keyframe_insert(data_path="scale", frame=f1)

        obj.scale = original_scale
        obj.keyframe_insert(data_path="scale", frame=f2)

def get_tree_leaf_objects():
    leaf_objects = []
    for obj in bpy.data.objects:
        if obj.name.startswith(TREE_LEAF_OBJECT_PREFIX):
            leaf_objects.append(obj)
    if not leaf_objects:
        raise RuntimeError(f"No tree leaf objects found with prefix '{TREE_LEAF_OBJECT_PREFIX}'")
    return leaf_objects

def clear_tree_leaf_animation():
    leaf_objects = get_tree_leaf_objects()
    for obj in leaf_objects:
        if obj.animation_data:
            obj.animation_data_clear()

def animate_tree_leaf_appearance(start_frame, end_frame, random_offset=0):
    leaf_objects = get_tree_leaf_objects()

    for obj in leaf_objects:
        offset = random.randint(0, random_offset) if random_offset > 0 else 0
        f1 = start_frame + offset
        f2 = end_frame + offset

        obj.hide_viewport = True
        obj.hide_render = True
        obj.keyframe_insert(data_path="hide_viewport", frame=f1)
        obj.keyframe_insert(data_path="hide_render", frame=f1)

        obj.hide_viewport = False
        obj.hide_render = False
        obj.keyframe_insert(data_path="hide_viewport", frame=f2)
        obj.keyframe_insert(data_path="hide_render", frame=f2)

def get_bush_objects():
    bush_objects = []
    for obj in bpy.data.objects:
        if obj.name.startswith(BUSH_OBJECT_PREFIX):
            bush_objects.append(obj)
    if not bush_objects:
        raise RuntimeError(f"No bush objects found with prefix '{BUSH_OBJECT_PREFIX}'")
    return bush_objects

def clear_bush_leaf_animation():
    bush_objects = get_bush_objects()
    for obj in bush_objects:
        if obj.animation_data:
            obj.animation_data_clear()

def animate_bush_leaf_growth(start_frame, end_frame, start_value=0.0, end_value=BUSH_LEAF_AMOUNT_VISIBLE, random_offset=0):
    bush_objects = get_bush_objects()
    found_input = False

    for obj in bush_objects:
        for mod in obj.modifiers:
            if mod.type != "NODES":
                continue
            if BUSH_LEAF_INPUT not in mod.keys():
                continue

            found_input = True
            offset = random.randint(0, random_offset) if random_offset > 0 else 0
            f1 = start_frame + offset
            f2 = end_frame + offset

            mod[BUSH_LEAF_INPUT] = start_value
            obj.keyframe_insert(data_path=f'modifiers["{mod.name}"]["{BUSH_LEAF_INPUT}"]', frame=f1)

            mod[BUSH_LEAF_INPUT] = end_value
            obj.keyframe_insert(data_path=f'modifiers["{mod.name}"]["{BUSH_LEAF_INPUT}"]', frame=f2)

    if not found_input:
        raise RuntimeError(f"No Geometry Nodes input '{BUSH_LEAF_INPUT}' found on bushes")


class FOREST_OT_animate_tree_growth(bpy.types.Operator):
    bl_idname = "forest.animate_tree_growth"
    bl_label = "Animate Tree Growth"
    bl_options = {"REGISTER", "UNDO"}

    start_frame: bpy.props.IntProperty(name="Start Frame", default=1, min=1)
    end_frame: bpy.props.IntProperty(name="End Frame", default=20, min=1)
    start_scale: bpy.props.FloatProperty(name="Start Scale", default=0.01, min=0.0)
    random_offset: bpy.props.IntProperty(name="Random Offset", default=10, min=0, max=200)

    def execute(self, context):
        season = context.scene.forest_season
        if season != "SPRING":
            self.report({"WARNING"}, "Tree growth animation runs only in Spring")
            return {"CANCELLED"}
        try:
            clear_tree_leaf_animation()
            animate_tree_leaf_appearance(self.start_frame, self.end_frame, self.random_offset)
        except Exception as e:
            self.report({"ERROR"}, str(e))
            return {"CANCELLED"}
        self.report({"INFO"}, "Tree leaf appearance animation created")
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class FOREST_OT_animate_bush_growth(bpy.types.Operator):
    bl_idname = "forest.animate_bush_growth"
    bl_label = "Animate Bush Growth"
    bl_options = {"REGISTER", "UNDO"}

    start_frame: bpy.props.IntProperty(name="Start Frame", default=1, min=1)
    end_frame: bpy.props.IntProperty(name="End Frame", default=20, min=1)
    start_scale: bpy.props.FloatProperty(name="Start Scale", default=0.01, min=0.0)
    random_offset: bpy.props.IntProperty(name="Random Offset", default=10, min=0, max=200)

    def execute(self, context):
        season = context.scene.forest_season
        if season != "SPRING":
            self.report({"WARNING"}, "Bush growth animation runs only in Spring")
            return {"CANCELLED"}
        try:
            clear_bush_leaf_animation()
            animate_bush_leaf_growth(self.start_frame, self.end_frame, 0.0, BUSH_LEAF_AMOUNT_VISIBLE, self.random_offset)
        except Exception as e:
            self.report({"ERROR"}, str(e))
            return {"CANCELLED"}
        self.report({"INFO"}, "Bush leaf growth animation created")
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class FOREST_OT_animate_flower_growth(bpy.types.Operator):
    bl_idname = "forest.animate_flower_growth"
    bl_label = "Animate Flower Growth"
    bl_options = {"REGISTER", "UNDO"}

    start_frame: bpy.props.IntProperty(name="Start Frame", default=1, min=1)
    end_frame: bpy.props.IntProperty(name="End Frame", default=20, min=1)
    start_scale: bpy.props.FloatProperty(name="Start Scale", default=0.01, min=0.0)
    random_offset: bpy.props.IntProperty(name="Random Offset", default=15, min=0, max=200)

    def execute(self, context):
        season = context.scene.forest_season
        if season != "SPRING":
            self.report({"WARNING"}, "Flower growth animation runs only in Spring")
            return {"CANCELLED"}
        try:
            clear_animation_for_collection(FLOWER_COLLECTION)
            animate_collection_growth(FLOWER_COLLECTION, self.start_frame, self.end_frame, self.start_scale, self.random_offset)
        except Exception as e:
            self.report({"ERROR"}, str(e))
            return {"CANCELLED"}
        self.report({"INFO"}, "Flower growth animation created")
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class FOREST_OT_animate_all_growth(bpy.types.Operator):
    bl_idname = "forest.animate_all_growth"
    bl_label = "Animate All Growth"
    bl_options = {"REGISTER", "UNDO"}

    start_frame: bpy.props.IntProperty(name="Start Frame", default=1, min=1)
    tree_end: bpy.props.IntProperty(name="Trees End", default=20, min=1)
    bush_end: bpy.props.IntProperty(name="Bushes End", default=20, min=1)
    flower_end: bpy.props.IntProperty(name="Flowers End", default=20, min=1)
    start_scale: bpy.props.FloatProperty(name="Start Scale", default=0.01, min=0.0)
    random_offset: bpy.props.IntProperty(name="Random Offset", default=10, min=0, max=200)

    def execute(self, context):
        season = context.scene.forest_season
        if season != "SPRING":
            self.report({"WARNING"}, "Growth animation runs only in Spring")
            return {"CANCELLED"}
        try:
            clear_tree_leaf_animation()
            clear_bush_leaf_animation()
            clear_animation_for_collection(FLOWER_COLLECTION)
            animate_tree_leaf_appearance(self.start_frame, self.tree_end, self.random_offset)
            animate_bush_leaf_growth(self.start_frame, self.bush_end, 0.0, BUSH_LEAF_AMOUNT_VISIBLE, self.random_offset)
            animate_collection_growth(FLOWER_COLLECTION, self.start_frame, self.flower_end, self.start_scale, self.random_offset)
        except Exception as e:
            self.report({"ERROR"}, str(e))
            return {"CANCELLED"}
        self.report({"INFO"}, "Leaf and flower growth animation created for Spring")
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


classes = (
    FOREST_OT_animate_tree_growth,
    FOREST_OT_animate_bush_growth,
    FOREST_OT_animate_flower_growth,
    FOREST_OT_animate_all_growth,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
