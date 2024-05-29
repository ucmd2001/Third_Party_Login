import logging
from fastapi import FastAPI, Request, Depends, APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os
import uvicorn
import requests
import base64
import hashlib
import hmac
import json
import time
from httpx import AsyncClient

load_dotenv(".local.env")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
oauth = OAuth()
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"))

oauth.register(
    name="line",
    client_id=os.getenv("LINE_CHANNEL_ID"),
    client_secret=os.getenv("LINE_CHANNEL_SECRET"),
    authorize_url="https://access.line.me/oauth2/v2.1/authorize",
    authorize_params=None,
    access_token_url="https://api.line.me/oauth2/v2.1/token",
    access_token_params=None,
    refresh_token_url=None,
    redirect_uri=os.getenv("LINE_REDIRECT_URI"),
    client_kwargs={"scope": "openid profile email"},
)

#首頁 ,
@app.get("/")
async def read_users(request: Request):
    user_info = request.session.get("user")
    profile_info = request.session.get("profile")
    if user_info and profile_info:
        print(user_info)
        print(profile_info)
        return JSONResponse(
            content={
                "message": "Success Get User info",
                "iss": user_info["iss"],
                "sub": user_info["sub"],
                "profile": profile_info,
            }
        )
    return JSONResponse(content={"message": "No user info found"})

#當用戶進入login , 重新導向至第三方頁面
@app.get("/login")
async def login(request: Request):
    redirect_uri = request.url_for("auth")
    print(f"Requset from Fronend: {request}")
    print(f"Generated redirect_uri: {redirect_uri}")
    return await oauth.line.authorize_redirect(request, redirect_uri)


@app.route("/line/auth")
async def auth(request: Request):
    code = request.query_params.get("code")
    print(code, '-------------------------------------------------')
    try:
        async with AsyncClient() as client:
            #前端重新導向並得到許可後, 拿取得的code換取 token 
            response = await client.post(
                "https://api.line.me/oauth2/v2.1/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": os.getenv("LINE_REDIRECT_URI"),
                    "client_id": os.getenv("LINE_CHANNEL_ID"),
                    "client_secret": os.getenv("LINE_CHANNEL_SECRET"),
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            token_data = response.json()
            id_token = token_data.get("id_token")
            access_token = token_data.get("access_token")
            logger.info(f"ID Token: {id_token}")
            logger.info(f"Access Token: {access_token}")

            #得到 Token 後, 依照API文件格式, 獲取用戶資料
            verify_response = await client.post(
                "https://api.line.me/oauth2/v2.1/verify",
                data={
                    "id_token": id_token,
                    "client_id": os.getenv("LINE_CHANNEL_ID"),
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            verify_response.raise_for_status()
            verify_data = verify_response.json()
            logger.info(f"Verify Response: {verify_data}")

            #得到 Token 後, 依照API文件格式, 獲取用戶資料
            profile_response = await client.get(
                "https://api.line.me/v2/profile",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            profile_response.raise_for_status()
            profile_data = profile_response.json()
            logger.info(f"Profile Data: {profile_data}")

            # 将用户资料和 access_token 存储在会话中
            request.session["user"] = verify_data
            request.session["access_token"] = access_token
            request.session["profile"] = profile_data

            return RedirectResponse(url="/")

    except Exception as e:
        logger.error(f"Error requesting token: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={"error": "Failed to obtain token", "details": str(e)},
        )


# # ================================================
# from routers import login
# from utils import verify

# app = FastAPI()
# app.include_router(login.router)

# logger = logging.getLogger(__name__)

# router = APIRouter(
#     prefix="/login",
#     tags=["login"],
#     responses={404: {"description": "LINE Login not found"}},
# )

# # 设置基本的日志配置
# logging.basicConfig(level=logging.INFO)

# @router.post("/")
# async def read_users(code: str, state: str):
#     client_id = os.getenv('LINE_LOGIN_CLIENT_ID')
#     secret = os.getenv('LINE_LOGIN_SECRET')
#     r_uri = os.getenv('LINE_LOGIN_URI')
#     response = requests.post(
#         "https://api.line.me/oauth2/v2.1/token",
#         data={
#             "grant_type": "authorization_code",
#             "code": code,
#             "redirect_uri": r_uri,
#             "client_id": client_id,
#             "client_secret": secret,
#         }, headers={"Content-Type": "application/x-www-form-urlencoded"}
#     )
#     payload = response.json()
#     token = payload.get("id_token")

#     if token is None:
#         logger.info('Token payload is empty: ' + str(payload))
#         return JSONResponse(status_code=400, content={'result': payload.get('error_description', 'Unknown error')})

#     try:
#         verify_result = verify.decode_id_token(token, client_id, secret)
#         logger.info('LINE login result: ' + str(verify_result))

#         # 保存用户信息到 JSON
#         users_data = login.load_users()
#         users_data["users"].append({
#             'uid': verify_result.get('sub'),
#             'name': verify_result.get('name'),
#             'picture': verify_result.get('picture')
#         })
#         login.save_users(users_data)

#         return {
#             'uid': verify_result.get('sub'),
#             'name': verify_result.get('name'),
#             'picture': verify_result.get('picture')
#         }
#     except Exception as e:
#         logger.warning('Login warning: ' + str(e))
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Could not validate credentials",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
# @router.get("/uri")
# def get_line_login_link():
#     r_uri = os.getenv("LINE_LOGIN_URI")
#     client = os.getenv("LINE_LOGIN_CLIENT_ID")
#     state = "1"
#     uri = f"https://access.line.me/oauth2/v2.1/authorize?response_type=code&client_id={client}&redirect_uri={r_uri}&scope=profile%20openid%20email&state={state}"
#     logger.info('Login url is: ' + uri)
#     return {'url': uri}


if __name__ == "__main__":
    uvicorn.run("TestlineLogin:app", reload=True, port=8080)
