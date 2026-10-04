# To use EfficientNetB0 for classifying 1000 classes of images from imagenet, we can use Imagenet weights.

from tensorflow.keras.applications import EfficientNetB0

model = EfficientNetB0(weights='imagenet')  # trained on 1000 classes of Imagenet dataset

model.summary()  # summary of the model

import cv2
import numpy as np
from matplotlib.pyplot import imread
from matplotlib.pyplot import imshow
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.imagenet_utils import decode_predictions
from tensorflow.keras.applications.imagenet_utils import preprocess_input

img_path = 'unseen_imagenet.jfif'

img = cv2.imread(img_path)
img = cv2.resize(img, (224, 224))

x = np.expand_dims(img, axis=0)
x = preprocess_input(x)

print('Input image shape:', x.shape)

my_image = imread(img_path)
imshow(my_image)