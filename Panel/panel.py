import bpy

BUSH_LEAF_AMOUNT_VISIBLE = 0.45454543828964233
TREE_LEAVES_PREFIX = "leaves"
BUSH_OBJECT_PREFIX = "Bush"
FLOWER_COLLECTION_NAME = "Generated_Flowers"


def ensure_props():
    bpy.types.Scene.forest_season = bpy.props.EnumProperty(
        name="Season",
        items=[
            ("SPRING", "Spring", ""),
            ("SUMMER", "Summer", ""),
            ("AUTUMN", "Autumn", ""),
            ("WINTER", "Winter", ""),
        ],
        default="SUMMER"
    )

    bpy.types.Scene.forest_animal = bpy.props.EnumProperty(
        name="Animal",
        items=[
            ("NONE", "None", ""),
            ("FOX", "Fox", ""),
            ("RABBIT", "Rabbit", ""),
        ],
        default="NONE"
    )


def clear_props():
    if hasattr(bpy.types.Scene, "forest_season"):
        del bpy.types.Scene.forest_season
    if hasattr(bpy.types.Scene, "forest_animal"):
        del bpy.types.Scene.forest_animal


def set_tree_leaves_visible(visible: bool):
    for obj in bpy.data.objects:
        if obj.name.startswith(TREE_LEAVES_PREFIX):
            obj.hide_viewport = not visible
            obj.hide_render = not visible


def set_bush_leaf_amount(value: float):
    for obj in bpy.data.objects:
        if obj.name.startswith(BUSH_OBJECT_PREFIX):
            for mod in obj.modifiers:
                if mod.type != "NODES":
                    continue

                if "Input_6" in mod.keys():
                    mod["Input_6"] = value

            obj.update_tag()

    bpy.context.view_layer.update()


def set_collection_visibility(collection_name: str, visible: bool):
    col = bpy.data.collections.get(collection_name)
    if col is None:
        return

    for obj in col.objects:
        obj.hide_viewport = not visible
        obj.hide_render = not visible


class FOREST_OT_apply_season(bpy.types.Operator):
    bl_idname = "forest.apply_season"
    bl_label = "Apply Season"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        season = context.scene.forest_season

        if season == "WINTER":
            set_tree_leaves_visible(False)
            set_bush_leaf_amount(0.0)
            set_collection_visibility(FLOWER_COLLECTION_NAME, False)

        elif season == "AUTUMN":
            set_tree_leaves_visible(True)
            set_bush_leaf_amount(BUSH_LEAF_AMOUNT_VISIBLE)
            set_collection_visibility(FLOWER_COLLECTION_NAME, False)

        elif season == "SPRING":
            set_tree_leaves_visible(True)
            set_bush_leaf_amount(BUSH_LEAF_AMOUNT_VISIBLE)
            set_collection_visibility(FLOWER_COLLECTION_NAME, True)

        elif season == "SUMMER":
            set_tree_leaves_visible(True)
            set_bush_leaf_amount(BUSH_LEAF_AMOUNT_VISIBLE)
            set_collection_visibility(FLOWER_COLLECTION_NAME, True)

        self.report({"INFO"}, f"Season applied: {season}")
        return {"FINISHED"}


class FOREST_OT_update_animal(bpy.types.Operator):
    bl_idname = "forest.update_animal"
    bl_label = "Update Animal"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        self.report({"INFO"}, f"Update Animal: {context.scene.forest_animal}")
        return {"FINISHED"}


class FOREST_PT_panel(bpy.types.Panel):
    bl_label = "Forest Controls"
    bl_idname = "FOREST_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Forest"

    def draw(self, context):
        layout = self.layout
        sc = context.scene

        layout.prop(sc, "forest_season")
        layout.operator("forest.apply_season", icon="FILE_REFRESH")

        layout.separator()

        layout.prop(sc, "forest_animal")
        layout.operator("forest.update_animal", icon="OUTLINER_OB_ARMATURE")

        layout.separator()

        box = layout.box()
        box.label(text="Scatter Objects")

        row = box.row(align=True)
        row.operator("object.scatter_trees", icon="OUTLINER_OB_GROUP_INSTANCE")
        row.operator("object.clear_trees", icon="TRASH")

        row = box.row(align=True)
        row.operator("object.scatter_bushes", icon="OUTLINER_OB_GROUP_INSTANCE")
        row.operator("object.clear_bushes", icon="TRASH")

        row = box.row(align=True)
        row.operator("object.scatter_flowers", icon="OUTLINER_OB_GROUP_INSTANCE")
        row.operator("object.clear_flowers", icon="TRASH")


classes = (
    FOREST_OT_apply_season,
    FOREST_OT_update_animal,
    FOREST_PT_panel,
)


def register():
    ensure_props()
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
    clear_props()


if __name__ == "__main__":
    register()