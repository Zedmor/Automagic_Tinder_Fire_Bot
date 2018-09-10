from skimage.io import imsave

base_folder = "data"


def save_image(image, name, target_dir):
    filename = base_folder

    filename += '/' + target_dir + '/'

    file_url_list = name.split("/")
    filename += file_url_list[-1]

    print(filename)

    imsave(filename, image)
