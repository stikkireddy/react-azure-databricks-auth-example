# React App / Python Backend with Databricks User OAuth


## Description

This is a simple React App that uses a Python backend to fetch data from Databricks using OAuth. 
You can do other strategies to force auth but for the app to be rendered you need to be authenticated.
Otherwise, it will force you to login to the authorization url. 

There is a very basic DatabricksAuthProvider React context provider that will handle the authentication and the token refresh.

## Databricks OAuth Custom Client

1. Go to databricks account console
2. Go to Settings -> App Connections
3. Create a new app connection
4. Make sure you have the following scopes selected `all apis`
5. Make sure you use the following redirect uri: `http://localhost:5173/token` or the appropriate one if you customize
6. We will be using authorization code grant flow with a client secret and PKCE with challenge method S256 (Sha256).
7. Make sure you select **generate client secret** since we have CORS requirement and you will need backend and client secret is good to have since the client is confidential.

## Auth workflow

1. React client code will invoke GET /authorize-url
2. The backend will prepare the code challenge, state and code verifier and ship the authorization url
3. The backend will also save this config as a HTTPOnly secure session cookie
4. The React code will redirect to the authorization url (this is a Databricks url)
5. The user will authenticate and authorize the app
6. Databricks will redirect to the redirect_uri with the code and state and this will be the url pointing to backend
7. The backend will receive the code and state with something like this /token?code=XXX&state=YYY
8. The backend will then retrieve the code verifier, state from the HTTPOnly cookie and validate the state
9. If the state is valid, the backend will exchange the code for the token using the client_id, client_secret, code, code_verifier
10. The backend will save the token, refresh token, etc encrypted in a HTTPOnly secure cookie (session) and redirect to the React application path.

**All cookies in the explanation are managed by the starlette SessionMiddleware. All the cookies are stored as a dictionary, encrypted and httpOnly.**

Make sure you use a proxy/etc to make sure that the backend and frontend are in the same domain to avoid CORS issues and cookie issues.
Cross origin cookies are only set with SameSite=None; Secure and the browser will block them if the domain is different. Not a good idea 
if you dont need to do this.

The app additionally has a background setInterval ref to validate the session every N seconds. It makes an api call POST /validate-session which 
ships the cookies over and then the backend converts the cookie to a decoded jwt and sees if it can refresh the token. You can modify this to be in magnitude of minutes.
To configure the React client to validate session every so often you can modify this in the React code. VITE_SESSION_VALIDATION_INTERVAL.

To modify the backend on how many seconds before expire to refresh token you can modify the config in the .env file. 
You can modify this on the Fastapi server: REFRESH_TOKEN_WITHIN_N_SECONDS.

All cookies have expiry of 1 hr other than the oauth_challenge_cfg which is 60 seconds.

## How to run

1. Clone the repo
2. Make sure you have nodejs and npm installed
3. Make sure you have python 3 installed
4. Populate all the .env files in both the react app and the python backend with the appropriate values. Use the template .env.template to know what to fill out.
5. Run `make install` to install the dependencies for both the python project and the react app
6. Run `make run-backend` to start the backend
7. Run `make run-ui` to start the UI

## Production

You can build the React app and serve it with the python backend.
You can also use a reverse proxy to serve the React app and the backend separately. Just ensure same domain.

## Why cookies?

Cookies are a good way to store the session and the token. 
You can use localStorage, but it is not secure and can be accessed by javascript and prone to xss. An alternative 
can be to use service workers which is beyond the scope of this project and can be used to store the token in memory.
Helping setup cross-origin cookies is beyond the scope of this repo and please reach out to Databricks representative 
if you need help with that.

## Disclaimer

This is provided as is, and you should not use this in production without proper security review. 
This is a simple example, and you should add more security features like CSRF protection, etc.