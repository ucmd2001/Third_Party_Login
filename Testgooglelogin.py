from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from fastapi.security import OAuth2AuthorizationCodeBearer
import os
import secrets
from dotenv import load_dotenv
import uvicorn

# 加载环境变量
load_dotenv(".local.env")

# FastAPI 应用实例
app = FastAPI()

# 配置中间件
app.add_middleware(SessionMiddleware, secret_key=os.environ.get("SECRET_KEY", "your_random_secret_key"))

# OAuth 设置
oauth = OAuth()

oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CHANNEL_ID"),
    client_secret=os.getenv("GOOGLE_CHANNEL_SECRET"),
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    refresh_token_url=None,
    client_kwargs={'scope': 'openid profile email'},
    jwks_uri='https://www.googleapis.com/oauth2/v3/certs'
)

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl='https://accounts.google.com/o/oauth2/auth',
    tokenUrl='https://accounts.google.com/o/oauth2/token',
)

@app.get("/login")
async def login(request: Request):
    redirect_uri = request.url_for('auth')
    state = secrets.token_urlsafe(16)  # 使用隨機生成的 state 值
    request.session['oauth_state'] = state
    return await oauth.google.authorize_redirect(request, redirect_uri, state=state)

@app.get("/auth")
async def auth(request: Request):
    state_in_session = request.session.get('oauth_state')
    state_in_request = request.query_params.get('state')

    if state_in_session != state_in_request:
        raise ValueError("State mismatch: possible CSRF attack.")

    token = await oauth.google.authorize_access_token(request)
    # print("Token received:", token)
    id_token = token.get('id_token')
    if not id_token:
        raise ValueError("Missing id_token in the token response")
    user = await oauth.google.parse_id_token(token, None)
    request.session['user_info'] = user
    return RedirectResponse(url='/')

@app.get("/")
async def home(request: Request):
    user_info = request.session.get('user_info')
    if user_info:
        return JSONResponse(user_info)
    return JSONResponse({"message": "User not logged in"})

@app.get("/protected-route")
async def protected_route(token: str = Depends(oauth2_scheme)):
    return {"token": token}

if __name__ == "__main__":
    uvicorn.run("Testgooglelogin:app", reload=True, port=8080)
