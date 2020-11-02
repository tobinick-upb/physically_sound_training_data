import math
import os
import random
from datetime import datetime

import trimesh

MAX_COUNTER = 100


def make_directory(path):
    try:
        os.mkdir(path)
    except OSError:
        print("Creation of the directory %s failed" % path)
    else:
        print("Successfully created the directory %s " % path)


def load_mesh_and_move_to_origin(object_path):
    print("obj path is: ", object_path)
    mesh = trimesh.load(object_path)
    # Move the object to the origin

    to_origin, extents = trimesh.bounds.oriented_bounds(mesh, 1, True, None)
    mesh.apply_transform(to_origin)

    return mesh


def create_training_orientations(object_path):
    mesh = load_mesh_and_move_to_origin(object_path)
    folder_path = object_path[:-4]
    make_directory(folder_path)

    random.seed(datetime.now())

    amount_of_orientations = MAX_COUNTER

    for i in range(amount_of_orientations):
        theta = 2 * math.pi * random.random()
        random.seed(datetime.now())
        phi = math.acos(1 - 2 * random.random())
        normal_x = math.sin(phi) * math.cos(theta)
        normal_y = math.sin(phi) * math.sin(theta)
        normal_z = math.cos(phi)

        rot_vec = trimesh.transformations.vector_product([normal_x,
                                                          normal_y,
                                                          normal_z],
                                                         [0, 0, -1])
        rot_angle = trimesh.transformations.angle_between_vectors([normal_x,
                                                                   normal_y,
                                                                   normal_z],
                                                                  [0, 0, -1])

        mesh.apply_transform(trimesh.transformations.rotation_matrix(rot_angle,
                                                                     rot_vec))

        export_path = folder_path + '/orientation_' + str(i) + ".obj"
        mesh.export(export_path)


path = "path/to/models/"

filelist = []
for filename in os.listdir(path):
    filelist.append(path + filename)

for file_path in filelist:
    print('Currently the object ', file_path, ' is processed.')
    create_training_orientations(file_path)
