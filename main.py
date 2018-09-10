import pynder

from helpers import get_access_token, get_login_credentials



email, password, FBID = get_login_credentials()
FBTOKEN = get_access_token(email, password)
session = pynder.Session(facebook_id=FBID,
                         facebook_token=FBTOKEN)
print("Session started..")


def lambda_handler(event, context):
    users = session.nearby_users()
    for user in users:
        print(user.id)
        user.like()

