import bpy
import random
from math import radians
from mathutils import Vector

terrain_name = "Plane"
no_trees_vgroup = "NoTrees"

tree_name = "tree"
bush_name = "Bush"

tree_collection = "Generated_Trees"
bush_collection = "Generated_Bushes"


def get_or_create_collection(name):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


def get_collection(name):
    return bpy.data.collections.get(name)


def clear_collection(col):
    if col is None:
        return
    for obj in list(col.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def raycast_to_terrain(terrain, x, y, z_start):
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
    vg = terrain.vertex_groups.get(vgroup_name)
    if vg is None:
        return 0.0

    poly = terrain.data.polygons[face_index]
    weights = []

    for vid in poly.vertices:
        try:
            w = vg.weight(vid)
        except RuntimeError:
            w = 0.0
        weights.append(w)

    return sum(weights) / len(weights) if weights else 0.0


def copy_with_children(src_obj, target_collection):
    new_obj = src_obj.copy()
    target_collection.objects.link(new_obj)

    for child in src_obj.children:
        new_child = copy_with_children(child, target_collection)
        new_child.parent = new_obj
        new_child.matrix_parent_inverse = child.matrix_parent_inverse.copy()
        new_child.matrix_basis = child.matrix_basis.copy()

    return new_obj


def scatter_on_terrain(
    source_obj_name,
    target_collection_name,
    count,
    area,
    z_start,
    min_scale,
    max_scale,
    use_vgroup,
    path_threshold,
    min_distance
):
    terrain = bpy.data.objects.get(terrain_name)
    src = bpy.data.objects.get(source_obj_name)

    if terrain is None:
        raise RuntimeError("Terrain not found")
    if terrain.type != "MESH":
        raise RuntimeError("Terrain must be mesh")
    if src is None:
        raise RuntimeError("Source object not found")
    if max_scale < min_scale:
        raise RuntimeError("Invalid scale range")

    col = get_or_create_collection(target_collection_name)
    clear_collection(col)

    placed_positions = []
    placed = 0
    tries = 0
    max_tries = count * 40

    while placed < count and tries < max_tries:
        tries += 1

        x = random.uniform(-area, area)
        y = random.uniform(-area, area)

        loc, face_index = raycast_to_terrain(terrain, x, y, z_start)
        if loc is None:
            continue

        if use_vgroup:
            w = vgroup_weight_at_face_avg(terrain, no_trees_vgroup, face_index)
            if w > path_threshold:
                continue

        if min_distance > 0.0:
            loc_vec = Vector(loc)
            if any((loc_vec - p).length < min_distance for p in placed_positions):
                continue
            placed_positions.append(loc_vec)

        new_obj = copy_with_children(src, col)
        new_obj.location = loc
        new_obj.rotation_euler[2] = radians(random.uniform(0, 360))

        s = random.uniform(min_scale, max_scale)
        new_obj.scale = (s, s, s)

        placed += 1

    return placed, tries


class OBJECT_OT_scatter_trees(bpy.types.Operator):
    bl_idname = "object.scatter_trees"
    bl_label = "Scatter Trees"
    bl_options = {"REGISTER", "UNDO"}

    count: bpy.props.IntProperty(name="Count", default=40, min=1, max=5000)
    area: bpy.props.FloatProperty(name="Area", default=6.0, min=0.1)
    z_start: bpy.props.FloatProperty(name="Ray start Z", default=1000.0)

    min_scale: bpy.props.FloatProperty(name="Min scale", default=0.7, min=0.01)
    max_scale: bpy.props.FloatProperty(name="Max scale", default=1.2, min=0.01)

    use_vgroup: bpy.props.BoolProperty(name="Use NoTrees", default=True)
    path_threshold: bpy.props.FloatProperty(name="Threshold", default=0.5, min=0.0, max=1.0)

    min_distance: bpy.props.FloatProperty(name="Min distance", default=1.5, min=0.0)

    def execute(self, context):
        try:
            placed, tries = scatter_on_terrain(
                tree_name,
                tree_collection,
                self.count,
                self.area,
                self.z_start,
                self.min_scale,
                self.max_scale,
                self.use_vgroup,
                self.path_threshold,
                self.min_distance
            )
        except Exception as e:
            self.report({"ERROR"}, str(e))
            return {"CANCELLED"}

        self.report({"INFO"}, f"Trees placed: {placed}")
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class OBJECT_OT_clear_trees(bpy.types.Operator):
    bl_idname = "object.clear_trees"
    bl_label = "Clear Trees"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        clear_collection(get_collection(tree_collection))
        return {"FINISHED"}


class OBJECT_OT_scatter_bushes(bpy.types.Operator):
    bl_idname = "object.scatter_bushes"
    bl_label = "Scatter Bushes"
    bl_options = {"REGISTER", "UNDO"}

    count: bpy.props.IntProperty(name="Count", default=20, min=1, max=5000)
    area: bpy.props.FloatProperty(name="Area", default=6.0, min=0.1)
    z_start: bpy.props.FloatProperty(name="Ray start Z", default=1000.0)

    min_scale: bpy.props.FloatProperty(name="Min scale", default=0.4, min=0.01)
    max_scale: bpy.props.FloatProperty(name="Max scale", default=0.8, min=0.01)

    use_vgroup: bpy.props.BoolProperty(name="Use NoTrees", default=True)
    path_threshold: bpy.props.FloatProperty(name="Threshold", default=0.5, min=0.0, max=1.0)

    min_distance: bpy.props.FloatProperty(name="Min distance", default=1.0, min=0.0)

    def execute(self, context):
        try:
            placed, tries = scatter_on_terrain(
                bush_name,
                bush_collection,
                self.count,
                self.area,
                self.z_start,
                self.min_scale,
                self.max_scale,
                self.use_vgroup,
                self.path_threshold,
                self.min_distance
            )
        except Exception as e:
            self.report({"ERROR"}, str(e))
            return {"CANCELLED"}

        self.report({"INFO"}, f"Bushes placed: {placed}")
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class OBJECT_OT_clear_bushes(bpy.types.Operator):
    bl_idname = "object.clear_bushes"
    bl_label = "Clear Bushes"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        clear_collection(get_collection(bush_collection))
        return {"FINISHED"}


def menu_func(self, context):
    self.layout.separator()
    self.layout.label(text="Procedural Scatter")
    self.layout.operator(OBJECT_OT_scatter_trees.bl_idname)
    self.layout.operator(OBJECT_OT_clear_trees.bl_idname)
    self.layout.separator()
    self.layout.operator(OBJECT_OT_scatter_bushes.bl_idname)
    self.layout.operator(OBJECT_OT_clear_bushes.bl_idname)


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
