import math
import os

from scipy.spatial import ConvexHull
import numpy as np
import trimesh

MAX_COUNTER = 80
CoG_THRESHOLD = 4
AREA_COMBINE_THRESHOLD = 0.025


def unit_normal(a, b, c):
    """unit normal vector of plane defined by points a, b, and c"""
    x = np.linalg.det([[1, a[1], a[2]],
                       [1, b[1], b[2]],
                       [1, c[1], c[2]]])
    y = np.linalg.det([[a[0], 1, a[2]],
                       [b[0], 1, b[2]],
                       [c[0], 1, c[2]]])
    z = np.linalg.det([[a[0], a[1], 1],
                       [b[0], b[1], 1],
                       [c[0], c[1], 1]])
    magnitude = (x ** 2 + y ** 2 + z ** 2) ** .5
    return (x / magnitude, y / magnitude, z / magnitude)


def area(poly):
    """area of polygon poly"""
    if len(poly) < 3:  # not a plane - no area
        return 0

    total = [0, 0, 0]
    for i in range(len(poly)):
        vi1 = poly[i]
        if i is len(poly) - 1:
            vi2 = poly[0]
        else:
            vi2 = poly[i + 1]
        prod = np.cross(vi1, vi2)
        total[0] += prod[0]
        total[1] += prod[1]
        total[2] += prod[2]
    result = np.dot(total, unit_normal(poly[0], poly[1], poly[2]))
    return abs(result / 2)


def length(v):
    """length of vector"""
    return math.sqrt(np.dot(v, v))


def calc_angle(v1, v2):
    """angle between two vectors"""
    return np.arccos(np.clip(np.dot(v1, v2) /
                     (length(v1) * length(v2)), -1.0, 1.0))


def calculate_outside_normal(p0, p1, p2, central_point):
    """Function for swapping the normal, if it is pointing inside the model"""
    v1 = p1 - p0
    v2 = p2 - p0
    current_normal = np.cross(v1, v2)

    # check if normal points to the outside of the hull
    # this is the vector pointing from hull to center
    vec_to_center = central_point - p0
    # this angle should always be between 0 and 1.571
    angle_to_center = calc_angle(vec_to_center, current_normal)

    # if angle is smaller then 90 degrees,
    # the normal points to the inside of the hull
    if angle_to_center < 1.571:
        current_normal = current_normal * -1
    return current_normal


def calc_norm_and_area_lists(pts, hull, central_point):
    """create list of all facettes of the hull.
    Sum up faces with the same orientation
    because they belong to the same plane
    return the list of normals and list of areas"""
    list_of_areas = []
    list_of_all_normals = []
    list_of_corresp_simplices = []

    total_surface_area = 0

    # Loop through all simplices of the convex hull
    for s in hull.simplices:
        p1 = [pts[s, 0][0], pts[s, 1][0], pts[s, 2][0]]
        p2 = [pts[s, 0][1], pts[s, 1][1], pts[s, 2][1]]
        p3 = [pts[s, 0][2], pts[s, 1][2], pts[s, 2][2]]
        poly = [p1, p2, p3]

        # Area of the current polygon
        facette_area = area(poly)
        total_surface_area += facette_area

        # Calculate the normal of a facette, pointing outside
        facette_normal = calculate_outside_normal(pts[s][0], pts[s][1],
                                                  pts[s][2], central_point)

        # First element has to be appended manually
        if (len(list_of_all_normals) == 0):
            list_of_all_normals.append(facette_normal)
            list_of_areas.append(facette_area)
            list_of_corresp_simplices.append([list(np.array(s))])
        else:
            # loop through list of normals
            for j in range(len(list_of_all_normals)):
                angle = calc_angle(facette_normal, list_of_all_normals[j])

                """In this case the current facette is in the same
                plane as a previous one and the areas will be combined"""
                if angle < AREA_COMBINE_THRESHOLD:
                    list_of_areas[j] += facette_area
                    list_of_corresp_simplices[j].append(list(np.array(s)))
                    break
                elif(j == (len(list_of_all_normals) - 1)):
                    """In this case there has not been a
                    facette of the same plane in the list yet"""
                    list_of_all_normals.append(facette_normal)
                    list_of_areas.append(facette_area)
                    list_of_corresp_simplices.append([list(np.array(s))])
                    break

    return list_of_all_normals,
    list_of_areas,
    list_of_corresp_simplices,
    total_surface_area


def sort_planes_via_area(list_of_areas, list_of_all_normals,
                         list_of_corresp_simplices):
    """The biggest MAX_COUNTER faces of
    the convex hull will be considered later"""
    counter = MAX_COUNTER
    if len(list_of_all_normals) < MAX_COUNTER:
        counter = len(list_of_all_normals)

    # arrays for saving the important information
    biggest_areas = [0] * counter
    simplices_list = [None] * counter
    normal_list = [[0, 0, 0]] * counter

    # loop over all facettes of the convex hull
    for i in range(len(list_of_areas)):
        for j in range(len(biggest_areas)):
            tmp = biggest_areas[j]
            tmp_simplice = simplices_list[j]
            tmp_normal = normal_list[j]
            if list_of_areas[i] > biggest_areas[j]:
                if j == 0:
                    biggest_areas[j] = list_of_areas[i]
                    simplices_list[j] = list_of_corresp_simplices[i]
                    normal_list[j] = list_of_all_normals[i]
                else:
                    biggest_areas[j - 1] = tmp
                    biggest_areas[j] = list_of_areas[i]
                    simplices_list[j - 1] = tmp_simplice
                    simplices_list[j] = list_of_corresp_simplices[i]
                    normal_list[j - 1] = tmp_normal
                    normal_list[j] = list_of_all_normals[i]

    return biggest_areas, normal_list, simplices_list


def load_mesh_and_move_to_origin(object_path):
    """load mesh and directly shift it to the origin"""
    mesh = trimesh.load(object_path)

    to_origin, extents = trimesh.bounds.oriented_bounds(mesh, 1, True, None)
    mesh.apply_transform(to_origin)

    return mesh


def load_mesh_rotate_with_normal_and_shift_bb(object_path, normal):
    """load mesh, rotate it and shift it to the origin"""
    mesh = load_mesh_and_move_to_origin(object_path)

    # calculate the rotation vector and rotation angle around this vector
    rot_vec = trimesh.transformations.vector_product([normal[0], normal[1],
                                                      normal[2]],
                                                     [0, 0, -1])
    rot_angle = trimesh.transformations.angle_between_vectors([normal[0],
                                                               normal[1],
                                                               normal[2]],
                                                              [0, 0, -1])

    if rot_vec[0] == 0 and rot_vec[1] == 0 and rot_vec[2] == 0:
        rot_vec[0] = 1
        mesh.apply_transform(trimesh.transformations.rotation_matrix(rot_angle,
                                                                     rot_vec))
    else:
        mesh.apply_transform(trimesh.transformations.rotation_matrix(rot_angle,
                                                                     rot_vec))

    bounds = trimesh.bounds.corners(mesh.bounding_box.bounds)
    min_z = min(bounds[:, 2])

    trans_mat = np.identity(4)
    trans_mat[2, 3] -= min_z

    mesh.apply_transform(trans_mat)

    return mesh


def update_lowest_CoG(lowest_CoG, current_CoG):
    """update the CoG list"""
    if lowest_CoG == 0:
        lowest_CoG = current_CoG[2]
    else:
        if current_CoG[2] < lowest_CoG:
            lowest_CoG = current_CoG[2]

    return lowest_CoG


def make_directory(path):
    try:
        os.mkdir(path)
    except OSError:
        print("Folder %s already exists" % path)
    else:
        print("Successfully created the directory %s " % path)


def stability_check(mesh, center, simplices_list, total_surface):
    """Function for checking stability of an orientation"""
    pts = mesh.vertices

    stable_position_found = False
    for s in simplices_list:
        p1 = [pts[s, 0][0], pts[s, 1][0], pts[s, 2][0]]
        p2 = [pts[s, 0][1], pts[s, 1][1], pts[s, 2][1]]
        p3 = [pts[s, 0][2], pts[s, 1][2], pts[s, 2][2]]

        tmp1 = float((p2[1] - p3[1]) * (center[0] - p3[0]) +
                     (p3[0] - p2[0]) * (center[1] - p3[1]))
        tmp2 = (p2[1] - p3[1]) * (p1[0] - p3[0])
        tmp3 = tmp2 + (p3[0] - p2[0]) * (p1[1] - p3[1])

        alpha = tmp1 / tmp3

        beta_tmp1 = float((p3[1] - p1[1]) * (center[0] - p3[0]) +
                          (p1[0] - p3[0]) * (center[1] - p3[1]))

        beta_tmp2 = (p2[1] - p3[1]) * (p1[0] - p3[0])
        beta_tmp3 = (p3[0] - p2[0]) * (p1[1] - p3[1])

        beta = beta_tmp1 / (beta_tmp2 + beta_tmp3)
        gamma = 1.0 - alpha - beta

        # When alpha, beta and gamma are bigger or equal than 0,
        # the projection of CoG is inside the polygon touching the surface
        if(alpha >= 0 and beta >= 0 and gamma >= 0):
            stable_position_found = True
            break

    return stable_position_found


def reduce_list_with_stability_criterion(object_path, list_of_normals,
                                         list_of_CoGs, list_of_facettes,
                                         total_surface):
    """Check all orietations regarding their stability and
    return reduced lists of possible orientations"""
    indicee_list = []

    """Check if x-y-position of the CoGs lies inside the polygone.
    If true, the object is in a stable position"""
    for i in range(len(list_of_normals)):
        mesh = load_mesh_rotate_with_normal_and_shift_bb(object_path,
                                                         list_of_normals[i])

        # Stability check
        is_stable = stability_check(mesh, list_of_CoGs[i],
                                    list_of_facettes[i], total_surface)

        if is_stable is True:
            indicee_list.append(i)
            print('The object is in a stable position for orienation ', i)
        else:
            print('The object is not in a stable position for orienation ', i)

    return indicee_list


def remove_redundancy(object_path, biggest_areas, normal_list, facette_list):
    """list of sizes of curved parts for checking
    if they have already been added"""
    size_save_round_part = []
    round_part_count = []
    reduced_biggest_area_list = []
    reduced_normal_list = []
    reduced_facette_list = []
    CoG_list = []
    lowest_CoG = 0

    for i in range(len(biggest_areas)):
        # i = len(biggest_areas) - 1 - j
        # Check for round surfaces.
        curved_facette_already_added = False
        for k in range(len(size_save_round_part)):
            if (biggest_areas[i] < size_save_round_part[k] * 1.075 and
                    biggest_areas[i] > size_save_round_part[k] * 0.925):

                """ 3 different orientations of round structures are
                saved to get different views but still avoid to have
                too many different orientations stored"""
                round_part_count[k] += 1
                if round_part_count[k] > 2:
                    curved_facette_already_added = True

        if not curved_facette_already_added:
            size_save_round_part.append(biggest_areas[i])
            round_part_count.append(0)

            # store the polygon areas, normals, and facettes in an reduced list
            reduced_biggest_area_list.append(biggest_areas[i])
            reduced_normal_list.append(normal_list[i])
            reduced_facette_list.append(facette_list[i])

            mesh = load_mesh_rotate_with_normal_and_shift_bb(object_path,
                                                             normal_list[i])

            current_CoG = mesh.center_mass
            CoG_list.append(current_CoG)
            lowest_CoG = update_lowest_CoG(lowest_CoG, current_CoG)

    return reduced_biggest_area_list,
    reduced_normal_list,
    reduced_facette_list,
    CoG_list,
    lowest_CoG


def create_training_orientations(object_path):
    """Main function for creation of physically sound
    training data for a 3D object"""
    mesh = load_mesh_and_move_to_origin(object_path)

    # load points of mesh
    pts = mesh.vertices
    hull = ConvexHull(pts)

    # Calculation of the center of the convex hull and the bounding box
    mean_vec = [0, 0, 0]
    for v in hull.vertices:
        mean_vec += pts[v]
    central_point = mean_vec / hull.vertices.size

    """Create list of all facettes of the hull.
    Sum up faces with the same orientation"""
    list_of_all_normals, list_of_all_areas, list_of_corresp_simp, total_surf = calc_norm_and_area_lists(pts, hull, central_point)

    print(len(list_of_all_areas), " different facettes exist")

    """Calculation of the normals, biggest areas and corresponding facettes
    sorted by area. We focus on the biggest planes because they are more
    likely to be planes where the object is lying on. This first lists
    contain the MAX_COUNTER biggest planes of the convex hull,
    which are generally possible planes where the object can lie on"""
    biggest_areas, normal_list, facette_list = sort_planes_via_area(list_of_all_areas, list_of_all_normals, list_of_corresp_simp)

    print(len(biggest_areas), " different planes exist")

    reduced_biggest_area_list, reduced_normal_list, reduced_facette_list, CoG_list, lowest_CoG = remove_redundancy(object_path, biggest_areas, normal_list, facette_list)

    print(len(reduced_biggest_area_list), " different planes exist after reduction")

    """Check if x-y-position of the CoGs lies inside the polygone.
    If true, the object is in a stable position"""
    list_of_stable_indicees = reduce_list_with_stability_criterion(object_path, reduced_normal_list, CoG_list, reduced_facette_list, total_surf)

    print("Stable indicees are: ", list_of_stable_indicees)

    list_of_stable_and_low_indicees = []
    # Check the z-position of the CoGs compared to the lowest CoG
    for i in list_of_stable_indicees:
        if CoG_list[i][2] > (lowest_CoG * CoG_THRESHOLD):
            print('CoG is very high: ', CoG_list[i][2])
        else:
            print('CoG is relatively low: ', CoG_list[i][2])
            list_of_stable_and_low_indicees.append(i)

    naming_counter = 0
    for i in range(len(list_of_stable_and_low_indicees)):
        indicee = list_of_stable_and_low_indicees[i]
        # checking for nearly same orientations
        already_exists = False
        for j in range(i + 1, len(list_of_stable_and_low_indicees)):
            indicee_2 = list_of_stable_and_low_indicees[j]
            angle = calc_angle(reduced_normal_list[indicee],
                               reduced_normal_list[indicee_2])
            if (angle < 0.05):
                already_exists = True
                break

        if (already_exists is False):
            mesh = load_mesh_rotate_with_normal_and_shift_bb(object_path,
                                                             reduced_normal_list[indicee])
            folder_path = object_path[:-4]
            if (naming_counter == 0):
                make_directory(folder_path)
            export_path = (folder_path + '/orientation_' +
                           str(naming_counter) + ".obj")
            mesh.export(export_path)
            naming_counter += 1


path = "path/to/models/"


filelist = []
for filename in os.listdir(path):
    filelist.append(path + filename)


for file_path in filelist:
    print('Currently the object ', file_path, ' is processed.')
    create_training_orientations(file_path)
