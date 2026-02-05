import bpy
import random
from math import radians
from mathutils import Vector

# =======================
# CONFIG / NAMES
# =======================
TERRAIN_NAME = "Plane"          # terrain object name
NO_TREES_VGROUP = "NoTrees"     # vertex group on terrain (path / forbidden zone)

TREE_NAME = "tree"              # source tree object name
BUSH_NAME = "Bush"              # source bush object name

TREE_COLLECTION = "Generated_Trees"
BUSH_COLLECTION = "Generated_Bushes"


# =======================
# HELPERS
# =======================
def get_or_create_collection(name: str):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


def get_collection(name: str):
    return bpy.data.collections.get(name)


def clear_collection(col):
    if col is None:
        return
    for obj in list(col.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def raycast_to_terrain(terrain, x, y, z_start):
    """
    Raycast from (x, y, z_start) straight down.
    Returns (location, face_index) if it hit the terrain, else (None, None).
    """
    depsgraph = bpy.context.evaluated_depsgraph_get()
    origin = (x, y, z_start)
    direction = (0.0, 0.0, -1.0)

    hit, location, normal, face_index, hit_obj, matrix = bpy.context.scene.ray_cast(
        depsgraph, origin, direction
    )

    if hit and hit_obj and hit_obj.name == terrain.name:
        return location, face_index
    return None, None


def vgroup_weight_at_face_avg(terrain, vgroup_name, face_index):
    """
    Returns average vertex-group weight for the polygon that was hit.
    If group doesn't exist -> 0.0
    """
    vg = terrain.vertex_groups.get(vgroup_name)
    if vg is None:
        return 0.0

    me = terrain.data
    poly = me.polygons[face_index]
    weights = []

    for vid in poly.vertices:
        try:
            w = vg.weight(vid)
        except RuntimeError:
            w = 0.0
        weights.append(w)

    return sum(weights) / len(weights) if weights else 0.0


# If you want STRICTER "no trees on path", use max instead of average:
def vgroup_weight_at_face_max(terrain, vgroup_name, face_index):
    vg = terrain.vertex_groups.get(vgroup_name)
    if vg is None:
        return 0.0

    me = terrain.data
    poly = me.polygons[face_index]
    weights = []

    for vid in poly.vertices:
        try:
            w = vg.weight(vid)
        except RuntimeError:
            w = 0.0
        weights.append(w)

    return max(weights) if weights else 0.0


# Choose which method you want:
VGROUP_WEIGHT_FUNC = vgroup_weight_at_face_avg
# Uncomment for stricter path blocking:
# VGROUP_WEIGHT_FUNC = vgroup_weight_at_face_max


def scatter_on_terrain(
    source_obj_name: str,
    target_collection_name: str,
    count: int,
    area: float,
    z_start: float,
    min_scale: float,
    max_scale: float,
    path_threshold: float,
    min_distance: float
):
    """
    Core scatter function used by both Trees and Bushes operators.
    """
    terrain = bpy.data.objects.get(TERRAIN_NAME)
    src = bpy.data.objects.get(source_obj_name)

    if terrain is None:
        raise RuntimeError(f"Terrain '{TERRAIN_NAME}' not found.")
    if src is None:
        raise RuntimeError(f"Source object '{source_obj_name}' not found.")
    if max_scale < min_scale:
        raise RuntimeError("Max scale must be >= Min scale.")

    col = get_or_create_collection(target_collection_name)
    clear_collection(col)

    placed_positions = []
    placed = 0
    tries = 0
    max_tries = count * 40  # safety

    while placed < count and tries < max_tries:
        tries += 1
        x = random.uniform(-area, area)
        y = random.uniform(-area, area)

        loc, face_index = raycast_to_terrain(terrain, x, y, z_start)
        if loc is None:
            continue

        # Forbidden zone (path)
        w = VGROUP_WEIGHT_FUNC(terrain, NO_TREES_VGROUP, face_index)
        if w > path_threshold:
            continue

        # Minimal distance
        if min_distance > 0.0:
            loc_vec = Vector(loc)
            too_close = any((loc_vec - p).length < min_distance for p in placed_positions)
            if too_close:
                continue
            placed_positions.append(loc_vec)

        new_obj = src.copy()
        if src.data:
            new_obj.data = src.data.copy()

        new_obj.location = loc
        new_obj.rotation_euler[2] = radians(random.uniform(0, 360))
        s = random.uniform(min_scale, max_scale)
        new_obj.scale = (s, s, s)

        col.objects.link(new_obj)
        placed += 1

    return placed, tries


# =======================
# OPERATORS
# =======================
class OBJECT_OT_scatter_trees(bpy.types.Operator):
    bl_idname = "object.scatter_trees"
    bl_label = "Scatter Trees"
    bl_options = {"REGISTER", "UNDO"}

    count: bpy.props.IntProperty(name="Count (trees)", default=40, min=1, max=5000)
    area: bpy.props.FloatProperty(name="Area (+/- X,Y)", default=6.0, min=0.1, max=1000.0)
    z_start: bpy.props.FloatProperty(name="Ray start Z", default=1000.0, min=1.0, max=100000.0)

    min_scale: bpy.props.FloatProperty(name="Min scale", default=0.7, min=0.01, max=100.0)
    max_scale: bpy.props.FloatProperty(name="Max scale", default=1.2, min=0.01, max=100.0)

    path_threshold: bpy.props.FloatProperty(name="Path threshold (0..1)", default=0.5, min=0.0, max=1.0)
    min_distance: bpy.props.FloatProperty(name="Min distance (0 = off)", default=1.5, min=0.0, max=1000.0)

    def execute(self, context):
        try:
            placed, tries = scatter_on_terrain(
                source_obj_name=TREE_NAME,
                target_collection_name=TREE_COLLECTION,
                count=self.count,
                area=self.area,
                z_start=self.z_start,
                min_scale=self.min_scale,
                max_scale=self.max_scale,
                path_threshold=self.path_threshold,
                min_distance=self.min_distance
            )
        except Exception as e:
            self.report({"ERROR"}, str(e))
            return {"CANCELLED"}

        self.report({"INFO"}, f"Trees placed: {placed}/{self.count} into '{TREE_COLLECTION}' (tries={tries})")
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class OBJECT_OT_clear_trees(bpy.types.Operator):
    bl_idname = "object.clear_generated_trees"
    bl_label = "Clear Trees"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        col = get_collection(TREE_COLLECTION)
        if col is None:
            self.report({"INFO"}, f"Collection '{TREE_COLLECTION}' not found.")
            return {"FINISHED"}
        clear_collection(col)
        self.report({"INFO"}, f"Cleared '{TREE_COLLECTION}'.")
        return {"FINISHED"}


class OBJECT_OT_scatter_bushes(bpy.types.Operator):
    bl_idname = "object.scatter_bushes"
    bl_label = "Scatter Bushes"
    bl_options = {"REGISTER", "UNDO"}

    count: bpy.props.IntProperty(name="Count (bushes)", default=20, min=1, max=5000)
    area: bpy.props.FloatProperty(name="Area (+/- X,Y)", default=6.0, min=0.1, max=1000.0)
    z_start: bpy.props.FloatProperty(name="Ray start Z", default=1000.0, min=1.0, max=100000.0)

    # bushes usually smaller
    min_scale: bpy.props.FloatProperty(name="Min scale", default=0.4, min=0.01, max=100.0)
    max_scale: bpy.props.FloatProperty(name="Max scale", default=0.8, min=0.01, max=100.0)

    path_threshold: bpy.props.FloatProperty(name="Path threshold (0..1)", default=0.5, min=0.0, max=1.0)
    min_distance: bpy.props.FloatProperty(name="Min distance (0 = off)", default=1.0, min=0.0, max=1000.0)

    def execute(self, context):
        try:
            placed, tries = scatter_on_terrain(
                source_obj_name=BUSH_NAME,
                target_collection_name=BUSH_COLLECTION,
                count=self.count,
                area=self.area,
                z_start=self.z_start,
                min_scale=self.min_scale,
                max_scale=self.max_scale,
                path_threshold=self.path_threshold,
                min_distance=self.min_distance
            )
        except Exception as e:
            self.report({"ERROR"}, str(e))
            return {"CANCELLED"}

        self.report({"INFO"}, f"Bushes placed: {placed}/{self.count} into '{BUSH_COLLECTION}' (tries={tries})")
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class OBJECT_OT_clear_bushes(bpy.types.Operator):
    bl_idname = "object.clear_generated_bushes"
    bl_label = "Clear Bushes"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        col = get_collection(BUSH_COLLECTION)
        if col is None:
            self.report({"INFO"}, f"Collection '{BUSH_COLLECTION}' not found.")
            return {"FINISHED"}
        clear_collection(col)
        self.report({"INFO"}, f"Cleared '{BUSH_COLLECTION}'.")
        return {"FINISHED"}


# =======================
# MENU
# =======================
def menu_func(self, context):
    self.layout.separator()
    self.layout.operator(OBJECT_OT_scatter_trees.bl_idname, icon="OUTLINER_OB_GROUP_INSTANCE")
    self.layout.operator(OBJECT_OT_clear_trees.bl_idname, icon="TRASH")
    self.layout.separator()
    self.layout.operator(OBJECT_OT_scatter_bushes.bl_idname, icon="OUTLINER_OB_GROUP_INSTANCE")
    self.layout.operator(OBJECT_OT_clear_bushes.bl_idname, icon="TRASH")


# =======================
# REGISTER
# =======================
classes = (
    OBJECT_OT_scatter_trees,
    OBJECT_OT_clear_trees,
    OBJECT_OT_scatter_bushes,
    OBJECT_OT_clear_bushes,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_object.append(menu_func)

def unregister():
    bpy.types.VIEW3D_MT_object.remove(menu_func)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
