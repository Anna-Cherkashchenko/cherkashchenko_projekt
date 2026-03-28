import bpy

BUSH_LEAF_AMOUNT_VISIBLE = 0.45454543828964233
TREE_LEAF_OBJECT_PREFIX = "leaf_tree"
BUSH_LEAF_OBJECT_PREFIX = "leaf_bush"
BUSH_OBJECT_PREFIX = "bush"
FLOWER_COLLECTION_NAME = "Generated_Flowers"
SNOW_COLLECTION_NAME = "Snow"
SNOW_OBJECT_NAME = "SnowBall.001"
SNOW_EMITTER_NAME = "snow_plane"
SNOW_PARTICLE_MODIFIER_NAME = "snow_particle_system"
RAIN_OBJECT_NAME = "raindrop"
RAIN_EMITTER_NAME = "rain_plane"
RAIN_PARTICLE_MODIFIER_NAME = "rain_particle_system"

GREEN_MATERIAL_NAME = "leaf_summer"
AUTUMN_MATERIAL_NAME = "leaf_autumn"

GRASS_OBJECT_NAME = "grass"
GRASS_SUMMER_MATERIAL_NAME = "grass_summer"
GRASS_WINTER_MATERIAL_NAME = "grass_winter"


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

def clear_props():
    if hasattr(bpy.types.Scene, "forest_season"):
        del bpy.types.Scene.forest_season

def clear_tree_leaf_animation():
    for obj in bpy.data.objects:
        if obj.name.startswith(TREE_LEAF_OBJECT_PREFIX):
            if obj.animation_data:
                obj.animation_data_clear()

def clear_bush_animation():
    for obj in bpy.data.objects:
        if obj.name.startswith(BUSH_OBJECT_PREFIX):
            if obj.animation_data:
                obj.animation_data_clear()

def clear_growth_animation():
    clear_tree_leaf_animation()
    clear_bush_animation()

def set_tree_leaves_visible(visible: bool):
    for obj in bpy.data.objects:
        if obj.name.startswith(TREE_LEAF_OBJECT_PREFIX):
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

def set_snow_enabled(enabled: bool):
    col = bpy.data.collections.get(SNOW_COLLECTION_NAME)
    if col is not None:
        col.hide_viewport = not enabled
        col.hide_render = not enabled

    obj = bpy.data.objects.get(SNOW_OBJECT_NAME)
    if obj is not None:
        obj.hide_viewport = not enabled
        obj.hide_render = not enabled

    emitter = bpy.data.objects.get(SNOW_EMITTER_NAME)
    if emitter is None:
        return
    emitter.hide_viewport = not enabled
    emitter.hide_render = not enabled
    mod = emitter.modifiers.get(SNOW_PARTICLE_MODIFIER_NAME)
    if mod is None:
        return
    mod.show_viewport = enabled
    mod.show_render = enabled

def set_rain_visible(visible: bool):
    obj = bpy.data.objects.get(RAIN_OBJECT_NAME)
    if obj is None:
        return
    obj.hide_viewport = not visible
    obj.hide_render = not visible

def set_rain_particles_enabled(enabled: bool):
    obj = bpy.data.objects.get(RAIN_EMITTER_NAME)
    if obj is None:
        return
    mod = obj.modifiers.get(RAIN_PARTICLE_MODIFIER_NAME)
    if mod is None:
        return
    mod.show_viewport = enabled
    mod.show_render = enabled

def is_leaf_object(obj):
    return (
        obj.type == "MESH" and
        (
            obj.name.startswith(TREE_LEAF_OBJECT_PREFIX) or
            obj.name.startswith(BUSH_LEAF_OBJECT_PREFIX)
        )
    )

def switch_leaf_polygons_to_material(obj, target_material_name, seasonal_material_names):
    if obj.type != "MESH" or obj.data is None:
        return
    mesh = obj.data
    target_index = None
    seasonal_indices = []
    for i, mat in enumerate(mesh.materials):
        if mat is None:
            continue
        if mat.name == target_material_name:
            target_index = i
        if mat.name in seasonal_material_names:
            seasonal_indices.append(i)
    if target_index is None:
        return
    if not seasonal_indices:
        return
    for poly in mesh.polygons:
        if poly.material_index in seasonal_indices:
            poly.material_index = target_index

def set_leaf_materials_for_season(season):
    green_mat = bpy.data.materials.get(GREEN_MATERIAL_NAME)
    autumn_mat = bpy.data.materials.get(AUTUMN_MATERIAL_NAME)
    if green_mat is None:
        raise RuntimeError(f"Material '{GREEN_MATERIAL_NAME}' not found")
    if autumn_mat is None:
        raise RuntimeError(f"Material '{AUTUMN_MATERIAL_NAME}' not found")
    if season in {"SPRING", "SUMMER"}:
        target_material_name = GREEN_MATERIAL_NAME
    else:
        target_material_name = AUTUMN_MATERIAL_NAME
    seasonal_material_names = {GREEN_MATERIAL_NAME, AUTUMN_MATERIAL_NAME}
    for obj in bpy.data.objects:
        if is_leaf_object(obj):
            switch_leaf_polygons_to_material(obj, target_material_name, seasonal_material_names)

def set_grass_material_for_season(season):
    grass_obj = bpy.data.objects.get(GRASS_OBJECT_NAME)
    if grass_obj is None:
        raise RuntimeError(f"Grass object '{GRASS_OBJECT_NAME}' not found")
    if season in {"SPRING", "SUMMER"}:
        target_material_name = GRASS_SUMMER_MATERIAL_NAME
    else:
        target_material_name = GRASS_WINTER_MATERIAL_NAME
    seasonal_material_names = {GRASS_SUMMER_MATERIAL_NAME, GRASS_WINTER_MATERIAL_NAME}
    switch_leaf_polygons_to_material(
        grass_obj,
        target_material_name,
        seasonal_material_names
    )


class FOREST_OT_apply_season(bpy.types.Operator):
    bl_idname = "forest.apply_season"
    bl_label = "Apply Season"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        season = context.scene.forest_season
        clear_growth_animation()

        if season == "WINTER":
            set_tree_leaves_visible(False)
            set_bush_leaf_amount(0.0)
            set_collection_visibility(FLOWER_COLLECTION_NAME, False)
            set_snow_enabled(True)
            set_rain_visible(False)
            set_rain_particles_enabled(False)

        elif season == "AUTUMN":
            set_tree_leaves_visible(True)
            set_bush_leaf_amount(BUSH_LEAF_AMOUNT_VISIBLE)
            set_collection_visibility(FLOWER_COLLECTION_NAME, False)
            set_snow_enabled(False)
            set_rain_visible(True)
            set_rain_particles_enabled(True)

        elif season == "SPRING":
            set_tree_leaves_visible(True)
            set_bush_leaf_amount(BUSH_LEAF_AMOUNT_VISIBLE)
            set_collection_visibility(FLOWER_COLLECTION_NAME, True)
            set_snow_enabled(False)
            set_rain_visible(False)
            set_rain_particles_enabled(False)

        elif season == "SUMMER":
            set_tree_leaves_visible(True)
            set_bush_leaf_amount(BUSH_LEAF_AMOUNT_VISIBLE)
            set_collection_visibility(FLOWER_COLLECTION_NAME, True)
            set_snow_enabled(False)
            set_rain_visible(False)
            set_rain_particles_enabled(False)

        set_leaf_materials_for_season(season)
        set_grass_material_for_season(season)
        self.report({"INFO"}, f"Season applied: {season}")
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
