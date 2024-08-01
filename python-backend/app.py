import json

import httpx
import requests
import uvicorn
from databricks.sdk import WorkspaceClient
from fastapi import FastAPI, Response, Cookie, Request
from starlette import status
from starlette.responses import JSONResponse, StreamingResponse, RedirectResponse

from constants import CLIENT_ID, REDIRECT_URI, WORKSPACE_URL, REACT_SERVICE_URL, SCOPES, PORT, HOST, CLIENT_SECRET
from models import TokenInfo, AuthorizeUrlResponse, AuthorizePayload, OauthChallengeCfg

app = FastAPI()


# Add CORS middleware
# DO NOT NEED CORS, YOU SHOULD TRY TO RUN THE APPS IN THE SAME DOMAIN
# cross domain cookies are tricky to deal with, require secure and difficult to test
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:5173"],  # Allows all origins
#     allow_credentials=True,
#     allow_methods=["*"],  # Allows all methods
#     allow_headers=["*"],  # Allows all headers
# )


@app.get("/authorize-url")
def authorize(response: Response) -> AuthorizeUrlResponse:
    # this will generate authorization url that will take your browser to another page
    # once you auth to databricks ws it will redirect back to the redirect uri
    # the redirect uri will be your application
    # the redirect will also include a code and state that you can use to verify and get the token
    # this is to ensure that the code is exchanged with the right service with the proper state
    auth_payload = AuthorizePayload.generate()
    authorize_cookie = auth_payload.to_oauth_cfg().json()
    response.set_cookie(key=OauthChallengeCfg.get_cookie_name(), value=authorize_cookie, httponly=True)
    return AuthorizeUrlResponse.from_authorize_payload(auth_payload)


@app.get("/token")
def token(
        code: str,
        state: str,
        # token_request: TokenRequest,
        oauth_challenge_cfg: str = Cookie(None)
):
    # oauth challenge config cookie
    oauth_cfg = OauthChallengeCfg.from_cookie(oauth_challenge_cfg)
    oauth_code_verifier = oauth_cfg.code_verifier
    oauth_state = oauth_cfg.state
    if state != oauth_state:
        invalid_state = JSONResponse(status_code=401, content={"error": "Invalid state"})
        invalid_state.delete_cookie(OauthChallengeCfg.get_cookie_name())
        return invalid_state
    print("Oauth CFG cookie", oauth_cfg)
    redirect_uri = REDIRECT_URI
    code_verifier = oauth_code_verifier
    authorization_code = code

    url = f"{WORKSPACE_URL}/oidc/v1/token"

    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'scope': SCOPES,
        'redirect_uri': redirect_uri,
        'code_verifier': code_verifier,
        'code': authorization_code
    }

    data = requests.post(url, headers={'Content-Type': 'application/x-www-form-urlencoded'}, data=data)
    access = data.json()
    try:
        token_info = TokenInfo(**access)
        resp = RedirectResponse(url="/", status_code=status.HTTP_308_PERMANENT_REDIRECT, )
        resp.set_cookie(key="session", value=token_info.to_encrypted_string(), httponly=True)
        resp.delete_cookie(OauthChallengeCfg.get_cookie_name())
        return resp
        # return access
    except Exception as e:
        pass
    invalid_token = JSONResponse(status_code=401, content={"error": "Invalid token"})
    invalid_token.delete_cookie(OauthChallengeCfg.get_cookie_name())
    return invalid_token


# THIS IS TOTALLY OPTIONAL AND NOT REQUIRED IF THE USER DOES NOTHING FOR 1 HR THEN JUST MAKE THEM GO THROUGH LOGIN FLOW AGAIN
@app.post("/validate-session")
def refresh(response: Response, session: str = Cookie(None)):
    if session is None:
        return JSONResponse(status_code=401, content={"error": "Invalid session"})

    token_info = TokenInfo.from_encrypted_string(session)
    if token_info.is_token_about_to_expire():
        print("Token is about to expire, attempting refresh")
        token_info.attempt_refresh()

    if token_info.access_token is None:
        response.delete_cookie("session")
        return JSONResponse(status_code=401, content={"error": "Invalid session"})

    response.set_cookie(key="session", value=token_info.to_encrypted_string(), httponly=True)
    return


@app.get("/test")
async def test_token(session: str = Cookie(None)):
    if session is None:
        return JSONResponse(status_code=401, content={"error": "Invalid session"})
    token_info = TokenInfo.from_encrypted_string(session)
    w = WorkspaceClient(token=token_info.access_token, host=WORKSPACE_URL)
    return w.current_user.me().as_dict()


# make sure this route is last as its a catch all route to push to the node server rendering react app
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH", "TRACE"])
async def proxy(request: Request, path: str):
    client = httpx.AsyncClient(base_url=REACT_SERVICE_URL)

    url = httpx.URL(path=path, query=request.url.query.encode("utf-8"))

    req = client.build_request(
        request.method,
        url,
        headers=request.headers.raw,
        content=await request.body()
    )

    response = await client.send(req, stream=True)

    return StreamingResponse(
        response.aiter_raw(),
        status_code=response.status_code,
        headers=response.headers
    )


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
