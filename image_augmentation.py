import sys
import getopt
import os
import io

import cv2
from matplotlib import pyplot as plt
import numpy as np

from albumentations import (
    HorizontalFlip, IAAPerspective, ShiftScaleRotate, CLAHE, RandomRotate90,
    Transpose, Blur, OpticalDistortion, GridDistortion,
    HueSaturationValue, IAAAdditiveGaussianNoise, GaussNoise,
    MotionBlur, MedianBlur, RandomBrightnessContrast, IAAPiecewiseAffine,
    IAASharpen, IAAEmboss, Flip, OneOf, Compose
)


READTHEDOCS_TEMPLATE_ALBU = (
    "[{name}](https://albumentations.readthedocs.io/en/" +
    "latest/api/augmentations.html#albumentations"
)
READTHEDOCS_TEMPLATE_IMGAUG = "[{name}](https://albumentations.readthedocs" + \
                              ".io/en/latest/api/imgaug.html#albumentations"
TRANSFORM_NAME_WITH_LINK_TEMPLATE = READTHEDOCS_TEMPLATE_ALBU + \
                                    ".augmentations.transforms.{name})"
IMGAUG_TRANSFORM_NAME_WITH_LINK_TEMPLATE = READTHEDOCS_TEMPLATE_IMGAUG + \
                                           ".imgaug.transforms.{name})"


def load_rgb_image(path):
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def get_figure(height=1080, width=1920, dpi=200):
    return plt.figure(figsize=(width / dpi, height / dpi))


def figure_to_numpy(figure, dpi=200):
    buf = io.BytesIO()
    figure.savefig(buf, format="png", dpi=dpi)
    buf.seek(0)
    image = np.frombuffer(buf.getvalue(), dtype=np.uint8)
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def apply_transform(
        image, transform_cls, args, targets=None, nrows=None,
        ncols=None, height=1080, width=1920, dpi=200
):

    args = [{"p": 0}] + list(args)
    targets = targets or {}
    total = len(args)

    if nrows is None:
        nrows = total // np.sqrt(total).astype(int)
    if ncols is None:
        ncols = total // nrows

    if nrows * ncols != total:
        ncols += 1

    nrows, ncols = min(nrows, ncols), max(nrows, ncols)

    result_args = []
    figure = get_figure(height, width, dpi)
    figure.tight_layout(pad=0)
    for i, args_i in enumerate(args, 1):
        if "p" not in args_i:
            args_i["p"] = 1

        if i == 1:
            title = f"{i}. Original"
        else:
            title = f"{i}."

        ax = figure.add_subplot(nrows, ncols, i)
        ax.set_title(title)
        ax.axis("off")
        ax.imshow(transform_cls(**args_i)(image=image, **targets)["image"])

        result_args.append(args_i)

    figure.canvas.draw()
    plt.axis("off")
    plt.subplots_adjust(left=0.01, right=0.99, bottom=0.1,
                        top=0.9, hspace=0.2, wspace=0.01)
    result_image = figure_to_numpy(figure, dpi)
    plt.close(figure)

    return result_args, result_image


def save_results(cls, text, image, save_path):
    with open(save_path, "a") as file:
        file.write("\n\n" + text)

    # image_path = os.path.split(save_path)[0]
    image_path = '/save/path'
    image_path = os.path.join(image_path, "{cls.__name__}.jpg")
    cv2.imwrite(image_path, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))


def create_docs_text(cls, args):
    name = cls.__name__
    module = cls.__module__

    docs_link = None
    if module == "albumentations.augmentations.transforms":
        docs_link = TRANSFORM_NAME_WITH_LINK_TEMPLATE.format(name=name)
    elif cls.__module__ == "albumentations.imgaug.transforms":
        docs_link = IMGAUG_TRANSFORM_NAME_WITH_LINK_TEMPLATE.format(name=name)

    text = f"[{name}]({docs_link})\n" + "-" * len(name) + "\n\n"

    for i, args_i in enumerate(args, 1):
        if args_i["p"] == 0:
            text += f"{i}. Original image\n"
            continue
        args_i = ", ".join(f"{key}={value}" for key, value in args_i.items())
        text += f"{i}. `{name}({args_i})`\n"

    text += f"\n![{name} image](images/augs_examples/{name}.jpg)\n"

    return text


def create_example(
        transform_cls, args, image_path, targets=None, nrows=None,
        ncols=None, height=1080, width=1920, dpi=200
):
    image = load_rgb_image(image_path)

    args, image = apply_transform(
        image=image,
        transform_cls=transform_cls,
        args=args,
        targets=targets,
        nrows=nrows,
        ncols=ncols,
        height=height,
        width=width,
        dpi=dpi,
    )
    text = create_docs_text(transform_cls, args)

    return text, image


def create_and_save(
        save_path,
        transform_cls,
        args,
        image_path,
        targets=None,
        nrows=None,
        ncols=None,
        height=1080,
        width=1920,
        dpi=200,
        show=False,
):
    text, image = create_example(
        transform_cls, args, image_path, targets=targets,
        nrows=nrows, ncols=ncols, height=height, width=width, dpi=dpi
    )

    save_results(transform_cls, text, image, save_path)


def main(argv):
    try:
        opts, args = getopt.getopt(argv, "hi:o:", ["ifile=", "ofile="])
    except getopt.GetoptError:
        print('example.py -i <inputfile> -o <outputfile>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('example.py -i <inputfile> -o <outputfile>')
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputpath = arg
        elif opt in ("-o", "--ofile"):
            outputpath = arg
    print('Input file is ', inputpath)
    print('Output file is ', outputpath)

    try:
        os.mkdir(outputpath)
    except OSError:
        print("Folder %s already exists " % outputpath)
    else:
        print("Successfully created the directory %s " % outputpath)

    for dirnames in os.listdir(inputpath):
        print("Current name is: ", inputpath + dirnames)
        if (os.path.isdir(inputpath + dirnames)):
            dirname_new = dirnames
        try:
            os.mkdir(outputpath + dirname_new)
        except OSError:
            print("Folder %s already exists " % outputpath + dirname_new)
        else:
            print("Successfully created the directory %s " % outputpath +
                  dirname_new)
        for filename in os.listdir(inputpath + dirnames):
            whole_path = inputpath + dirnames + '/' + filename
            if(whole_path.find('.png') != -1):
                image = load_rgb_image(inputpath + dirnames + '/' + filename)

                # aug = HorizontalFlip(p=1)
                # aug = IAAAdditiveGaussianNoise(p=1)
                # aug = RandomBrightnessContrast(p=1)
                # aug = Blur(blur_limit=(5, 5),p=1)
                # aug = CLAHE(p=1)
                # aug = IAASharpen(p=1)
                aug = Compose([OneOf([IAAAdditiveGaussianNoise(p=0.5),
                                      RandomBrightnessContrast(p=0.5)], 0.75),
                              OneOf([Blur(blur_limit=(5, 5),
                                          p=0.5), CLAHE(p=0.5)], 0.75)])
                image = aug(image=image)['image']
                # aug2 = CLAHE(p=1)
                # image = aug2(image=image)['image']

                cv2.imwrite(outputpath + dirname_new + '/' + filename,
                            cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
            else:
                print('wrong file type')


if __name__ == "__main__":
    main(sys.argv[1:])
