import json

from skimage.io import imsave

base_folder = "data"


def save_image(image, name, target_dir):
    filename = base_folder

    filename += '/' + target_dir + '/'

    file_url_list = name.split("/")
    filename += file_url_list[-1]

    imsave(filename, image)

def save_data(data, name, target_dir):
    filename = base_folder

    filename += '/' + target_dir + '/'

    file_url_list = name.split("/")
    filename += file_url_list[-1]

    with open(filename, 'w') as data_file:
        json.dump(data, data_file)
