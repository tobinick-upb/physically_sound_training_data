# physically_sound_training_data
Code and Data corresponding to the paper "Generating Physically Sound Training Data for Image Recognition of Additively Manufactured Parts"


### Blender Phong Shading for image rendering

The training images are rendered using Blender Phong Shading, which can be downloaded from the following link. 

https://github.com/WeiTang114/BlenderPhong

The script phong_multi_for_rotnet.py can be used for the creation of training images.

### Image Augmentation

For augmentation, we have used the albumentations library.

https://github.com/albumentations-team/albumentations

It can be used via the image_augmentation.py script.

### RotationNet:

For our evaluation we used RotationNet. It can be downloaded via:  

https://github.com/kanezaki/rotationnet

### Raw data sets:

The raw data sets Random30, Random50, Random100, Similar10, Similar30 and Similar50 and the images of the physical objects used for evaluation can be downloaded from 

https://zenodo.org/record/4108973#.X5-_ilBCeUk

Besides the data sets, the link contains the prototxt files which define the network architecture of RotationNet, the prototxt files defining the solver parameters and example lists for the training data access.

The dependencies for using Blender, Albumentations and RotationNet can be found at the corresponding links.
