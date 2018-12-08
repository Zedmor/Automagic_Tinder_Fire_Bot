from io import BytesIO

import requests

import caffe
import json
import pickle

from PIL import Image
from theano.tensor.nnet import relu
import boto3
import cv2
import numpy as np
import pynder
from skimage.io import imread
from skimage.transform import resize
from lasagne.utils import floatX
import common
from helpers import get_access_token
from io_helpers import save_image


caffe.set_mode_gpu()
model_dir = '/home/zedmor/Development/SCUT/vgg_face_caffe/'
net_caffe = caffe.Net(model_dir + 'VGG_FACE_deploy.prototxt', model_dir + 'VGG_FACE.caffemodel', caffe.TEST)

def convert_face_features(img):
    mean_rgb = np.array([129.1863, 104.7624, 93.5940])  # see vgg face matlab demo

    im = np.copy(img * 256)
    im = im - mean_rgb
    # convert to the caffe format
    im = np.swapaxes(np.swapaxes(im, 1, 2), 0, 1)  # -> channels x height x width
    im = im[::-1, :, :]  # RGB -> BGR
    im = floatX(im[np.newaxis])  # add axis -> 1 x channels x height x width

    out1 = net_caffe.forward(data=im, end='pool5')
    #    feat_maps.append(out1['pool5'].flatten())
    out2 = net_caffe.forward(data=im, end='fc6')
    return np.concatenate((out1['pool5'].flatten(), 2 * relu(out2['fc6'].flatten())))


def extract_faces(img):
    img = np.array(img)
    face_cascade = cv2.CascadeClassifier('utils/haarcascade_frontalface_default.xml')
    eye_cascade = cv2.CascadeClassifier('utils/haarcascade_eye.xml')
    imageDataFin = []

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray)

    for (x, y, w, h) in faces:
        roi_gray = gray[y:y + h, x:x + w]
        roi_color = img[y:y + h, x:x + w]

        eyes = eye_cascade.detectMultiScale(roi_gray)

        if len(eyes) >= 1:
            im = resize(roi_color, (224, 224))
            imageDataFin.append(im)

    return imageDataFin


def i_like(face):
    clf = pickle.load(open('/home/zedmor/Development/beauty_vision/svr.model', 'rb'))
    return clf.predict(np.asarray(convert_face_features(face)))


def main():
    session = boto3.session.Session()

    secret_name = 'zedmor-facebook'
    secret = json.loads(common.get_secret(secret_name, session))
    print(len(secret))

    # FBTOKEN = get_access_token(secret['email'], secret['password'])

    FBTOKEN = "EAAGm0PX4ZCpsBAIf01ZB8HZCsTsq0EUZBhrtvvjO2OVbQtKZBkZAl8JDo5d7vO6P5Foe5Htv90EJOzePCE4jpa8pIi8jAlTHiUG7qvM7JM2PnSkZB6AeWA3Bfd0J5qUZBJ5EpKkL9JJCHUehemIOcEhhlEZBA4cQHPvfHtp0TzCzhnZBycJ2sCa8egPYVjUrTo3ZBkIfCob6nNYZCWgSTdIolXnYNZAYr7TeC2gsZD"
    print(FBTOKEN[:5])
    session = pynder.Session(facebook_id=secret['FBID'],
                             facebook_token=FBTOKEN)

    print("Session started..")
    total_likes = 0
    total_dislikes = 0

    while True:
        users = session.nearby_users()
        for user in users:
            with open('tinder.log', 'a+') as log:
                print(user.id)
                photos = user.get_photos()
                print("Fetched user photos..")
                likes = []
                images = []
                for photo in photos:
                    try:
                        response = requests.get(photo)
                        image = Image.open(BytesIO(response.content)).convert('RGB')
                        faces = extract_faces(image)
                        for face in faces:
                            like = i_like(face)
                            likes.append(like)
                            images.append(face)
                    except:
                        pass
                if likes:
                    max_like = max(likes)
                    print(user.id, max_like)
                    if max_like > 3.7:
                        user.like()
                        save_image(images[likes.index(max_like)], '{}_{}.jpg'.format(str(max_like), user.id), 'autolike')
                        total_likes += 1
                    else:
                        user.dislike()
                        save_image(images[likes.index(max_like)], '{}_{}.jpg'.format(str(max_like), user.id), 'autodislike')
                        total_dislikes += 1
                    log.write("Total users: {}, likes: {}, dislikes: {}. Like % {}\n".format(total_likes + total_dislikes,
                                                                                             total_likes, total_dislikes,
                                                                                             float(total_likes) / (total_dislikes + total_likes)))
                else:
                    user.dislike()
                    total_dislikes += 1



if __name__ == "__main__":
    main()
