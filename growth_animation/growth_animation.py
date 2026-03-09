import bpy
import random

TREE_COLLECTION = "Generated_Trees"
BUSH_COLLECTION = "Generated_Bushes"
FLOWER_COLLECTION = "Generated_Flowers"


def clear_animation_for_collection(collection_name):
    col = bpy.data.collections.get(collection_name)
    if col is None:
        return

    for obj in col.objects:
        if obj.animation_data and obj.animation_data.action:
            action = obj.animation_data.action
            for fcurve in list(action.fcurves):
                if fcurve.data_path == "scale":
                    action.fcurves.remove(fcurve)


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


class FOREST_OT_animate_tree_growth(bpy.types.Operator):
    bl_idname = "forest.animate_tree_growth"
    bl_label = "Animate Tree Growth"
    bl_options = {"REGISTER", "UNDO"}

    start_frame: bpy.props.IntProperty(name="Start Frame", default=1, min=1)
    end_frame: bpy.props.IntProperty(name="End Frame", default=80, min=1)
    start_scale: bpy.props.FloatProperty(name="Start Scale", default=0.01, min=0.0)
    random_offset: bpy.props.IntProperty(name="Random Offset", default=10, min=0, max=200)

    def execute(self, context):
        season = context.scene.forest_season

        if season != "SPRING":
            self.report({"WARNING"}, "Tree growth animation runs only in Spring")
            return {"CANCELLED"}

        try:
            clear_animation_for_collection(TREE_COLLECTION)
            animate_collection_growth(
                TREE_COLLECTION,
                self.start_frame,
                self.end_frame,
                self.start_scale,
                self.random_offset
            )
        except Exception as e:
            self.report({"ERROR"}, str(e))
            return {"CANCELLED"}

        self.report({"INFO"}, "Tree growth animation created")
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class FOREST_OT_animate_bush_growth(bpy.types.Operator):
    bl_idname = "forest.animate_bush_growth"
    bl_label = "Animate Bush Growth"
    bl_options = {"REGISTER", "UNDO"}

    start_frame: bpy.props.IntProperty(name="Start Frame", default=1, min=1)
    end_frame: bpy.props.IntProperty(name="End Frame", default=60, min=1)
    start_scale: bpy.props.FloatProperty(name="Start Scale", default=0.01, min=0.0)
    random_offset: bpy.props.IntProperty(name="Random Offset", default=10, min=0, max=200)

    def execute(self, context):
        season = context.scene.forest_season

        if season != "SPRING":
            self.report({"WARNING"}, "Bush growth animation runs only in Spring")
            return {"CANCELLED"}

        try:
            clear_animation_for_collection(BUSH_COLLECTION)
            animate_collection_growth(
                BUSH_COLLECTION,
                self.start_frame,
                self.end_frame,
                self.start_scale,
                self.random_offset
            )
        except Exception as e:
            self.report({"ERROR"}, str(e))
            return {"CANCELLED"}

        self.report({"INFO"}, "Bush growth animation created")
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class FOREST_OT_animate_flower_growth(bpy.types.Operator):
    bl_idname = "forest.animate_flower_growth"
    bl_label = "Animate Flower Growth"
    bl_options = {"REGISTER", "UNDO"}

    start_frame: bpy.props.IntProperty(name="Start Frame", default=1, min=1)
    end_frame: bpy.props.IntProperty(name="End Frame", default=40, min=1)
    start_scale: bpy.props.FloatProperty(name="Start Scale", default=0.01, min=0.0)
    random_offset: bpy.props.IntProperty(name="Random Offset", default=15, min=0, max=200)

    def execute(self, context):
        season = context.scene.forest_season

        if season != "SPRING":
            self.report({"WARNING"}, "Flower growth animation runs only in Spring")
            return {"CANCELLED"}

        try:
            clear_animation_for_collection(FLOWER_COLLECTION)
            animate_collection_growth(
                FLOWER_COLLECTION,
                self.start_frame,
                self.end_frame,
                self.start_scale,
                self.random_offset
            )
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
    tree_end: bpy.props.IntProperty(name="Trees End", default=80, min=1)
    bush_end: bpy.props.IntProperty(name="Bushes End", default=60, min=1)
    flower_end: bpy.props.IntProperty(name="Flowers End", default=40, min=1)
    start_scale: bpy.props.FloatProperty(name="Start Scale", default=0.01, min=0.0)
    random_offset: bpy.props.IntProperty(name="Random Offset", default=10, min=0, max=200)

    def execute(self, context):
        season = context.scene.forest_season

        if season != "SPRING":
            self.report({"WARNING"}, "Growth animation runs only in Spring")
            return {"CANCELLED"}

        try:
            clear_animation_for_collection(TREE_COLLECTION)
            clear_animation_for_collection(BUSH_COLLECTION)
            clear_animation_for_collection(FLOWER_COLLECTION)

            animate_collection_growth(
                TREE_COLLECTION,
                self.start_frame,
                self.tree_end,
                self.start_scale,
                self.random_offset
            )

            animate_collection_growth(
                BUSH_COLLECTION,
                self.start_frame,
                self.bush_end,
                self.start_scale,
                self.random_offset
            )

            animate_collection_growth(
                FLOWER_COLLECTION,
                self.start_frame,
                self.flower_end,
                self.start_scale,
                self.random_offset
            )

        except Exception as e:
            self.report({"ERROR"}, str(e))
            return {"CANCELLED"}

        self.report({"INFO"}, "Growth animation created for Spring")
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