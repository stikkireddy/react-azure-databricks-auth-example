from typing import Optional

import httpx
import uvicorn
from databricks.sdk import WorkspaceClient
from databricks.sdk.oauth import OAuthClient, SessionCredentials, Consent
from fastapi import FastAPI, Request, Depends
from pydantic import BaseModel
from starlette import status
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse, StreamingResponse, RedirectResponse

from constants import CLIENT_ID, REDIRECT_URI, WORKSPACE_URL, REACT_SERVICE_URL, SCOPES, PORT, HOST, CLIENT_SECRET, \
    COOKIE_MAX_AGE, COOKIE_ENCRYPTION_KEY

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

app.add_middleware(SessionMiddleware,
                   # this is the key to encrypt the cookie
                   # use a static one if you dont want app reboot to invalidate all sessions
                   secret_key=COOKIE_ENCRYPTION_KEY,
                   https_only=True,
                   max_age=COOKIE_MAX_AGE,
                   same_site="strict")

oauth_client = OAuthClient(host=WORKSPACE_URL,
                           client_id=CLIENT_ID,
                           client_secret=CLIENT_SECRET,
                           redirect_url=REDIRECT_URI,
                           # All three scopes needed for model serving on Azure
                           scopes=SCOPES)


class AuthorizeUrlResponse(BaseModel):
    authorize_url: str

    @classmethod
    def from_authorize_payload(cls, consent: Consent):
        return cls(authorize_url=consent.auth_url)


@app.get("/authorize-url")
def authorize(request: Request) -> AuthorizeUrlResponse:
    # this will generate authorization url that will take your browser to another page
    # once you auth to databricks ws it will redirect back to the redirect uri
    # the redirect uri will be your application
    # the redirect will also include a code and state that you can use to verify and get the token
    # this is to ensure that the code is exchanged with the right service with the proper state
    consent = oauth_client.initiate_consent()
    request.session["consent"] = consent.as_dict()
    return AuthorizeUrlResponse.from_authorize_payload(consent)


@app.get("/token")
def token(
        request: Request,
        code: Optional[str] = None,
        state: Optional[str] = None,
        error: Optional[str] = None,
        error_description: Optional[str] = None,
):
    from databricks.sdk.oauth import Consent

    if error is not None:
        # something wrong happened with state or invalid oauth config
        request.session["consent"] = None
        return JSONResponse(status_code=401, content={"error": error, "error_description": error_description})

    consent = Consent.from_dict(oauth_client, request.session.get("consent"))
    try:
        creds = consent.exchange(code, state)
    except Exception as e:
        request.session["consent"] = None
        return RedirectResponse(url="/", status_code=status.HTTP_308_PERMANENT_REDIRECT, )

    request.session["consent"] = None
    access = creds.as_dict()
    try:
        request.session["token"] = access
        return RedirectResponse(url="/", status_code=status.HTTP_308_PERMANENT_REDIRECT, )
    except Exception:
        pass
    request.session["token"] = None
    return JSONResponse(status_code=401, content={"error": "Invalid token"})


# THIS IS TOTALLY OPTIONAL AND NOT REQUIRED IF THE USER DOES NOTHING FOR 1 HR THEN JUST MAKE THEM GO THROUGH LOGIN FLOW AGAIN
@app.post("/validate-session")
def refresh(request: Request):
    session_token = request.session.get("token")
    if session_token is None:
        return JSONResponse(status_code=401, content={"error": "Invalid session"})
    creds = SessionCredentials.from_dict(oauth_client, session_token)
    if creds.token().valid is False:
        return JSONResponse(status_code=401, content={"error": "Invalid session"})
    request.session["token"] = creds.as_dict()


def get_workspace_client(request: Request) -> Optional[WorkspaceClient]:
    session_token = request.session.get("token")
    if session_token is None:
        return None
    creds = SessionCredentials.from_dict(oauth_client, session_token)
    return WorkspaceClient(token=creds.token().access_token, host=WORKSPACE_URL)


@app.get("/test")
async def test_token(w: Optional[WorkspaceClient] = Depends(get_workspace_client)):
    if w is None:
        return JSONResponse(status_code=401, content={"error": "Invalid session"})
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
