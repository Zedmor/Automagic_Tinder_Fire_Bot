#! /usr/bin/python3
import datetime
import re

import logging
from io import BytesIO

from PIL import Image

import numpy as np

from io_helpers import save_image
from main import extract_faces, SVR_CLASSIFIER, convert_face_features

import requests
from selenium import webdriver
from selenium.common.exceptions import *
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import argparse
from time import sleep

logging.basicConfig(level=logging.INFO)

def log_in_with_facebook(driver, email, password):
    while True:
        try:
            button = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'color-provider-facebook')]")))
            button.click()
            break
        except NoSuchElementException:
            pass

    # switch to facebook window
    driver.switch_to.window(driver.window_handles[1])

    # try to enter email until it loads
    while True:
        try:
            driver.find_element_by_xpath("//input[@id='email']").send_keys(email)
            break
        except NoSuchElementException as e:
            pass

    # enter password and click submit
    driver.find_element_by_xpath("//input[@id='pass']").send_keys(password)
    driver.find_element_by_xpath("//input[@id='u_0_0']").click()

    try:
        # try to click continue until it loads
        while True:
            try:
                driver.find_element_by_xpath("//button[contains(text(), 'Continue as')]").click()
                break
            except NoSuchElementException:
                pass
    except:
        pass

    # back to main window
    driver.switch_to.window(driver.window_handles[0])

def dismiss_match(driver):
    try:
        driver.find_element_by_xpath("//*[contains(@class, 'button--transparent')]").click()
        return True
    except NoSuchElementException:
        return False



def all_done(driver):
    # check to see if we are all caught up
    try:
        driver.find_element_by_xpath("//*[contains(text(), 'all caught up')]")
        return True
    except NoSuchElementException:
        pass
    try:
        driver.find_element_by_xpath("//*[contains(text(), 'bees in your area')]")
        return True
    except NoSuchElementException:
        pass

    return False


def size(url):
    try:
        url_size = re.findall('wm_offs=(\d+)x(\d+)', url)
        return max(map(int, url_size[0]))
    except:
        return 0


def analyze_images(images):
    runtime = datetime.datetime.now().isoformat()
    urls = [url for url in images if size(url) > 72]
    likes = []
    images = []

    for photo in urls:
        try:
            response = requests.get(photo)
            image = Image.open(BytesIO(response.content)).convert('RGB')
            faces = extract_faces(image)
            for face in faces:
                likes.append(SVR_CLASSIFIER.predict(np.asarray(convert_face_features(face))))
                images.append(face)
        except Exception as e:
            logging.error(e)
    if likes:
        logging.info('All ratings {}'.format(likes))
        max_like = max(likes)
        formatted_max_like = "{0:.2f}".format(float(max_like))
        if max_like > 3.5:
            logging.info(f'Like, rating {formatted_max_like}')
            save_image(images[likes.index(max_like)], '{}_{}.jpg'.format(formatted_max_like, runtime), 'autolike')
            return True
        else:
            logging.info(f'Dislike, rating {max_like}')
            save_image(images[likes.index(max_like)], '{}_{}.jpg'.format(formatted_max_like, runtime), 'autodislike')
            return False
    else:
        logging.info('Dislike - No faces')
        return False


def like(driver):
    try:
        images = driver.find_elements_by_tag_name('img')
        urls = [image.get_attribute('src') for image in images]
        return analyze_images(urls)
    except StaleElementReferenceException as e:
        logging.error(e)
        return False


def swipe_left(driver):
    try:
        # dismiss_match(driver)
        driver.find_element_by_xpath("//div[contains(@class, 'encounters-action--dislike')]").click()
        return True
    except Exception as e:
        logging.error(e)
    return not all_done(driver)

def swipe_right(driver):
    try:
        # dismiss_match(driver)
        driver.find_element_by_xpath("//div[contains(@class, 'encounters-action--like')]").click()
        return True
    except Exception as e:
        logging.error(e)

    return not all_done(driver)


if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser(description="Auto swiper for bumble. Pass your Facebook email and password.")
    parser.add_argument('email', metavar='email', type=str, nargs=1,
            help='Your Facebook email')
    parser.add_argument('password', metavar='password', type=str, nargs=1,
            help='Your Facebook password')

    args     = parser.parse_args()
    email    = args.email
    password = args.password

    # open driver
    driver = webdriver.Firefox()
    driver.get("https://bumble.com/login")

    log_in_with_facebook(driver, email, password)

    # keep swiping right until we're caught up
    while True:
        # refresh page until we get new matches
        if like(driver):
            result = swipe_right(driver)
        else:
            result = swipe_left(driver)

        if not result:
            print("All caught up... Refreshing until matches available... Ctrl-C to quit.")
            driver.execute_script("location.reload(true);")
            sleep(5)

    driver.close()
