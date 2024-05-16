import os
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import OAuth2AuthorizationCodeBearer
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from starlette.config import Config

# 加载环境变量
load_dotenv(".local.env")

# FastAPI 应用实例
app = FastAPI()

# 配置中间件
app.add_middleware(SessionMiddleware, secret_key=os.environ.get("SECRET_KEY", "your_random_secret_key"))

# OAuth 设置
config_data = {
    "GOOGLE_CLIENT_ID": os.getenv("GOOGLE_CHANNEL_ID"),
    "GOOGLE_CLIENT_SECRET": os.getenv("GOOGLE_CHANNEL_SECRET"),
}

config = Config(environ=config_data)
oauth = OAuth(config)
oauth.register(
    name='google',
    client_id=config_data['GOOGLE_CLIENT_ID'],
    client_secret=config_data['GOOGLE_CLIENT_SECRET'],
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    refresh_token_url=None,
    client_kwargs={'scope': 'openid profile email'},
)

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl='https://accounts.google.com/o/oauth2/auth',
    tokenUrl='https://accounts.google.com/o/oauth2/token',
)

@app.get("/login")
async def login(request: Request):
    redirect_uri = request.url_for('auth')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth")
async def auth(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user = await oauth.google.parse_id_token(request, token)
    return JSONResponse(user)

@app.get("/protected-route")
async def protected_route(token: str = Depends(oauth2_scheme)):
    return {"token": token}

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, port=8080)