import logging
from operator import itemgetter

import boto3
import pynder
import requests
import robobrowser
import re
import json
import os
import random

import common

MOBILE_USER_AGENT = "Tinder/7.5.3 (iPhone; iOS 10.3.2; Scale/2.00)"

logging.basicConfig(level=logging.INFO)

FB_AUTH = "https://www.facebook.com/v2.6/dialog/oauth?redirect_uri=fb464891386855067%3A%2F%2Fauthorize%2F&scope=user_birthday%2Cuser_photos%2Cuser_education_history%2Cemail%2Cuser_relationship_details%2Cuser_friends%2Cuser_work_history%2Cuser_likes&response_type=token%2Csigned_request&client_id=464891386855067&ret=login&fallback_redirect_uri=221e1158-f2e9-1452-1a05-8983f99f7d6e&ext=1556057433&hash=Aea6jWwMP_tDMQ9y"

def get_pynder_session(secret):
    try:
        with open('output/fbtoken.json') as fbtoken_file:
            fbtoken = json.load(fbtoken_file)['token']
            logging.info('Getting session using saved facebook token')
            return pynder.Session(facebook_id=secret['FBID'], facebook_token=fbtoken)
    except Exception as e:
        logging.error('Token do not work', e)
        fbtoken = get_access_token(secret['email'], secret['password'])
        with open('output/fbtoken.json', 'w') as fbtoken_file:
            json.dump({'token': fbtoken}, fbtoken_file)
        logging.info('New token successfully retrieved')

        return pynder.Session(facebook_id=secret['FBID'], facebook_token={'token': fbtoken})


def get_access_token(email, password):
    browser = robobrowser.RoboBrowser(history=True, user_agent=MOBILE_USER_AGENT, parser="lxml")
    browser.open(FB_AUTH)
    # First we submit the login form
    f = browser.get_form("login_form")
    f["email"] = email
    f["pass"] = password
    browser.submit_form(f)

    try:
        # Now we *should* be redirected to the Tinder app dialogue. If we don't see this
        # form that means that the user did not type the right password
        f = browser.get_form("platformDialogForm")
        if f is None:
            return {"error": "Login failed. Check your username and password."}
        browser.submit_form(f, submit=f.submit_fields['__CONFIRM__'])
        access_token = re.search(r"access_token=([\w\d]+)", browser.response.content.decode()).groups()[0]
        return access_token
    # FIXME: Learn how to submit the form correctly so that we don't have to do this
    # clowny exception handling
    except requests.exceptions.InvalidSchema as e:
        access_token = re.search(r"access_token=([\w\d]+)", str(e)).groups()[0]
        return access_token
    except Exception as e:
        return {"error": f"access token could not be retrieved: {repr(e)}"}

def get_login_credentials():
    logging.info("Checking for credentials..")
    if os.path.exists('/home/zedmor/.config/fb.json'):
        logging.info("Auth.json existed..")
        with open('/home/zedmor/.config/fb.json') as data_file:
            data = json.load(data_file)
            if "email" in data and "password" in data and "FBID" in data:
                return data
            else:
                print("Invalid auth.json file.")
    else:
        session = boto3.session.Session()

        secret_name = 'zedmor-facebook'
        return json.loads(common.get_secret(secret_name, session))

    print("Auth.json missing or invalid. Please enter your credentials.")


# token = get_access_token('zedmor@gmail.com', 'olya-love-me')
#
# print(token)
