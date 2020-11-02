# WARNING:
# Blender might not release memory even if you delete an object,
# so rendering a large number of object in one run may occupy a lot of memory.
# If this happens, it is better to split the list into multiple runs..
import sys
import bpy
import os.path
import math

C = bpy.context
D = bpy.data
scene = D.scenes['Scene']

# cameras: a list of camera positions
# a camera position is defined by two parameters: (theta, phi),
# where we fix the "r" of (r, theta, phi) in spherical coordinate system.

# 5 orientations: front, right, back, left, top
cameras = [
    (60, 0), (60, 90), (60, 180), (60, 270),
    (0, 0)
]
num_of_instances = 300
# 12 orientations around the object with 30-deg elevation
cameras = [(60, i) for i in range(0, 360, 30)]
print(cameras)
additional_cameras = [(i, 90) for i in range(0, 360, 30)]
cameras = cameras + additional_cameras
print(additional_cameras)
render_setting = scene.render

# output image size = (W, H)
w = 500
h = 500
render_setting.resolution_x = w
render_setting.resolution_y = h


def install_off_addon():
    try:
        bpy.ops.wm.addon_install(
            overwrite=False,
            filepath=os.path.dirname(__file__) +
            '/blender-off-addon/import_off.py'
        )
        bpy.ops.wm.addon_enable(module='import_off')
    except Exception:
        print("""Import blender-off-addon failed.
              Did you pull the blender-off-addon submodule?
              $ git submodule update --recursive --remote
              """)
        exit(-1)


def init_camera():
    cam = D.objects['Camera']
    # select the camera object
    scene.objects.active = cam
    cam.select = True

    # set the rendering mode to orthogonal and scale
    C.object.data.type = 'PERSP'
    C.object.data.lens = 5.5


def fix_camera_to_origin():
    origin_name = 'Origin'

    # create origin
    try:
        origin = D.objects[origin_name]
    except KeyError:
        bpy.ops.object.empty_add(type='SPHERE')
        D.objects['Empty'].name = origin_name
        origin = D.objects[origin_name]

    origin.location = (0, 0, 0)

    cam = D.objects['Camera']
    scene.objects.active = cam
    cam.select = True

    if 'Track To' not in cam.constraints:
        bpy.ops.object.constraint_add(type='TRACK_TO')

    cam.constraints['Track To'].target = origin
    cam.constraints['Track To'].track_axis = 'TRACK_NEGATIVE_Z'
    cam.constraints['Track To'].up_axis = 'UP_Y'


def render_model(model_name, save_dir_rotnet, input_dir):
    print("Input dir is: ", input_dir)
    rot_num, rot_step_size, full_path, num_orient = get_rot_num(model_name,
                                                                input_dir)
    image_subdir_rotnet = os.path.join(save_dir_rotnet, model_name)
    counter = 0
    rot_num = math.ceil(rot_num)

    count = 0
    for filename in os.listdir(full_path):
        print(filename)
        if filename.startswith("orientation"):
            os.rename(os.path.join(full_path, filename),
                      os.path.join(full_path,
                                   model_name + "_" + str(count) + ".obj"))
            count = count + 1

    for k in range(0, num_orient):
        full_file_path = os.path.join(full_path,
                                      model_name + "_" + str(k) + ".obj")
        print(full_file_path)

        init_camera()
        fix_camera_to_origin()
        if os.path.isfile(full_file_path):
            cc1 = 0
            loaded_model = load_model(full_file_path)
            center_model(loaded_model)
            normalize_model(loaded_model)
            obj = D.objects[loaded_model]
            obj.rotation_euler.x -= math.pi / 2
            mat = bpy.data.materials.new('MaterialName')
            mat.diffuse_color = (1.0, 1.0, 1.0)
            mat.diffuse_shader = 'LAMBERT'
            mat.diffuse_intensity = 1.0
            # get the material
            mat = bpy.data.materials['MaterialName']
            # assign material to object
            obj.data.materials.append(mat)

            print(full_file_path)
            for j in range(0, rot_num):
                cc1 = cc1 + 1
                rot = j * rot_step_size
                # cameras = [(60, i + rot) for i in range(0, 360, 30)]
                cc = 0

                for i in range(0, 360, 30):
                    cc = cc + 1
                    c = (45, i + rot)
                    move_camera(c)
                    render()

                    save(image_subdir_rotnet,
                         '%s_%s_%s' % (model_name,
                                       str(math.ceil(cc1+counter)).zfill(4),
                                       str(cc).zfill(3)))

            delete_model(loaded_model)

        counter = counter + cc1


def render_model_variable_angle(model_name, save_dir_rotnet, input_dir):
    print("Input dir is: ", input_dir)
    rot_num, rot_step_size, full_path, num_orient = get_rot_num(model_name,
                                                                input_dir)
    image_subdir_rotnet = os.path.join(save_dir_rotnet, model_name)
    counter = 0
    rot_num = math.ceil(rot_num)

    count = 0
    for filename in os.listdir(full_path):
        print(filename)
        if filename.startswith("orientation"):
            os.rename(os.path.join(full_path, filename),
                      os.path.join(full_path,
                                   model_name + "_" + str(count) + ".obj"))
            count = count + 1

    for k in range(0, num_orient):
        full_file_path = os.path.join(full_path,
                                      model_name + "_" + str(k) + ".obj")
        print(full_file_path)

        init_camera()
        fix_camera_to_origin()
        if os.path.isfile(full_file_path):
            cc1 = 0
            loaded_model = load_model(full_file_path)
            center_model(loaded_model)
            normalize_model(loaded_model)
            obj = D.objects[loaded_model]
            obj.rotation_euler.x -= math.pi / 2
            mat = bpy.data.materials.new('MaterialName')
            mat.diffuse_color = (1.0, 1.0, 1.0)
            mat.diffuse_shader = 'LAMBERT'
            mat.diffuse_intensity = 1.0
            # get the material
            mat = bpy.data.materials['MaterialName']
            # assign material to object
            obj.data.materials.append(mat)

            print(full_file_path)
            for j in range(0, rot_num):
                cc1 = cc1 + 1
                rot = j * rot_step_size
                # cameras = [(60, i + rot) for i in range(0, 360, 30)]
                cc = 0

                for i in range(0, 360, 30):
                    cc = cc + 1
                    vert_angle = 45
                    if (i % 60 == 0):
                        vert_angle = 35
                    else:
                        vert_angle = 55

                    c = (vert_angle, i + rot)
                    move_camera(c)
                    render()

                    save(image_subdir_rotnet,
                         '%s_%s_%s' % (model_name,
                                       str(math.ceil(cc1+counter)).zfill(4),
                                       str(cc).zfill(3)))

            delete_model(loaded_model)

        counter = counter + cc1


def get_rot_num(path, input_dir):
    DIR = os.path.dirname(__file__) + '/' + input_dir
    print("DIR is: ",  path)
    name1 = os.path.basename(path).split('.')[0]
    path = os.path.join(DIR, name1)
    print("path is: ",  path)
    print(sum([len(files) for r, d, files in os.walk(path)]))
    num_orientation = sum([len(files) for r, d, files in os.walk(path)])
    rot_num = num_of_instances / num_orientation
    rot_step_size = 30 / rot_num
    return rot_num, rot_step_size, path, num_orientation


def load_model(path):
    d = os.path.dirname(path)
    ext = path.split('.')[-1]

    name = os.path.basename(path).split('.')[0]
    # get_rot_num(name)
    # handle weird object naming by Blender for stl files
    if ext == 'stl':
        name = name.title().replace('_', ' ')

    if name not in D.objects:
        print('loading :' + name)
        if ext == 'stl':
            bpy.ops.import_mesh.stl(filepath=path, directory=d,
                                    filter_glob='*.stl')
        elif ext == 'off':
            bpy.ops.import_mesh.off(filepath=path, filter_glob='*.off')
        elif ext == 'obj':
            bpy.ops.import_scene.obj(filepath=path, filter_glob='*.obj')
        else:
            print('Currently .{} file type is not supported.'.format(ext))
            exit(-1)
    return name


def delete_model(name):
    for ob in scene.objects:
        if ob.type == 'MESH' and ob.name.startswith(name):
            ob.select = True
        else:
            ob.select = False
    bpy.ops.object.delete()


def center_model(name):
    obj = D.objects[name]
    dim = obj.dimensions
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    # bpy.ops.object.origin_set(type='GEOMETRY_ORIGIN')
    print("Coming here : " + name + "   " + str(dim[2]))
    D.objects[name].location = (0, 0, 0)
    # only translating in z direction because all objects are already centered
    # bpy.ops.transform.translate(value=(0,0,-dim[2]/100))


def normalize_model(name):
    obj = D.objects[name]
    dim = obj.dimensions
    print('original dim:' + str(dim))
    if max(dim) > 0:
        dim = dim / max(dim)
    obj.dimensions = dim

    print('new dim:' + str(dim))


def move_camera(coord):
    def deg2rad(deg):
        return deg * math.pi / 180.

    r = 2.
    theta, phi = deg2rad(coord[0]), deg2rad(coord[1])
    loc_x = r * math.sin(theta) * math.cos(phi)
    loc_y = r * math.sin(theta) * math.sin(phi)
    loc_z = r * math.cos(theta)

    D.objects['Camera'].location = (loc_x, loc_y, loc_z)


def render():
    bpy.ops.render.render()


def save(image_dir, name):
    path = os.path.join(image_dir, name + '.png')
    D.images['Render Result'].save_render(filepath=path)
    print('save to ' + path)


def main():
    argv = sys.argv
    argv = argv[argv.index('--') + 1:]

    if len(argv) != 3:
        print('phong.py args: <3d mesh list file> <save dir rotnet>')
        exit(-1)

    models_list = argv[0]
    input_dir = models_list.split('\\')[0]
    save_dir_rotnet = argv[1]

    # blender has no native support for off files
    # install_off_addon()

    init_camera()
    fix_camera_to_origin()

    with open(models_list) as f:
        models = f.read().splitlines()

    for model in models:
        render_model(model, save_dir_rotnet, input_dir)


if __name__ == '__main__':
    main()
