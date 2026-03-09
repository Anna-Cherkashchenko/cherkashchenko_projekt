import bpy

BUSH_LEAF_AMOUNT_VISIBLE = 0.45454543828964233
TREE_LEAVES_PREFIX = "leaves"
BUSH_OBJECT_PREFIX = "Bush"
FLOWER_COLLECTION_NAME = "Generated_Flowers"

GREEN_MATERIAL_NAME = "Leaf"
AUTUMN_MATERIAL_NAME = "Leaf.001"


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


def set_leaf_materials_for_season(season):
    green_mat = bpy.data.materials.get(GREEN_MATERIAL_NAME)
    autumn_mat = bpy.data.materials.get(AUTUMN_MATERIAL_NAME)

    if green_mat is None:
        raise RuntimeError(f"Material '{GREEN_MATERIAL_NAME}' not found")
    if autumn_mat is None:
        raise RuntimeError(f"Material '{AUTUMN_MATERIAL_NAME}' not found")

    if season in {"SPRING", "SUMMER"}:
        target_mat = green_mat
    else:
        target_mat = autumn_mat

    possible_old_names = {GREEN_MATERIAL_NAME, AUTUMN_MATERIAL_NAME}

    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        if not obj.data or not hasattr(obj.data, "materials"):
            continue

        for i, mat in enumerate(obj.data.materials):
            if mat and mat.name in possible_old_names:
                obj.data.materials[i] = target_mat


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

        set_leaf_materials_for_season(season)

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

        box_season = layout.box()
        box_season.label(text="Season")
        box_season.prop(sc, "forest_season")
        box_season.operator("forest.apply_season", icon="FILE_REFRESH")

        box_animal = layout.box()
        box_animal.label(text="Animal")
        box_animal.prop(sc, "forest_animal")
        box_animal.operator("forest.update_animal", icon="OUTLINER_OB_ARMATURE")

        box_scatter = layout.box()
        box_scatter.label(text="Scatter Objects")

        row = box_scatter.row(align=True)
        row.operator("object.scatter_trees", icon="OUTLINER_OB_GROUP_INSTANCE")
        row.operator("object.clear_trees", icon="TRASH")

        row = box_scatter.row(align=True)
        row.operator("object.scatter_bushes", icon="OUTLINER_OB_GROUP_INSTANCE")
        row.operator("object.clear_bushes", icon="TRASH")

        row = box_scatter.row(align=True)
        row.operator("object.scatter_flowers", icon="OUTLINER_OB_GROUP_INSTANCE")
        row.operator("object.clear_flowers", icon="TRASH")

        box_growth = layout.box()
        box_growth.label(text="Growth Animation")
        box_growth.operator("forest.animate_all_growth", icon="GRAPH")


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
