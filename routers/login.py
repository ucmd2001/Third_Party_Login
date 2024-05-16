import logging
import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import requests
import json
from pydantic import BaseModel
from utils.verify import decode_id_token
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/login",
    tags=["login"],
    responses={404: {"description": "LINE Login not found"}},
)


def load_users():
    with open("users.json", "r") as file:
        return json.load(file)

def save_users(data):
    with open("users.json", "w") as file:
        json.dump(data, file, indent=4)


@router.post("/")
async def read_users(code: str, state: str):
    client_id = os.getenv('LINE_LOGIN_CLIENT_ID')
    secret = os.getenv('LINE_LOGIN_SECRET')
    r_uri = os.getenv('LINE_LOGIN_URI')
    response = requests.post(
        "https://api.line.me/oauth2/v2.1/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": r_uri,
            "client_id": client_id,
            "client_secret": secret,
        }, headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    payload = response.json()
    token = payload.get("id_token")

    if token is None:
        logger.info('Token payload is empty: ' + str(payload))
        return JSONResponse(status_code=400, content={'result': payload.get('error_description', 'Unknown error')})

    try:
        verify_result = decode_id_token(token, client_id, secret)
        logger.info('LINE login result: ' + str(verify_result))
        
        # 保存用户信息到 JSON
        users_data = load_users()
        users_data["users"].append({
            'uid': verify_result.get('sub'),
            'name': verify_result.get('name'),
            'picture': verify_result.get('picture')
        })
        save_users(users_data)

        return {
            'uid': verify_result.get('sub'),
            'name': verify_result.get('name'),
            'picture': verify_result.get('picture')
        }
    except Exception as e:
        logger.warning('Login warning: ' + str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.get("/uri")
def get_line_login_link():
    r_uri = os.environ.get("LINE_LOGIN_URI")
    client = os.environ.get("LINE_LOGIN_CLIENT_ID")
    state = "nostate" # it will be random value
    uri = f"https://access.line.me/oauth2/v2.1/authorize?response_type=code&client_id={client}&redirect_uri={r_uri}&scope=profile%20openid%20email&state={state}&initial_amr_display=lineqr"
    logger.info('Login url is: ' + uri)
    return {'result': uri}