# Authentication

## Overview

<!-- See https://www.youtube.com/watch?v=d7OxfJZOIhQ

The service uses Google OAuth2 for authentication. The authentication flow is
implemented using the `Google-api-python-client` library. -->

The authentication flow will use Google OAuth2 flow.

An endpoint will be created at `auth/login` to present the user with a link to authenticate with Google.

The user will be redirected to the Google OAuth2 consent screen, where they can grant permission to the application to access their Google account (email and profile information).

Once the user grants permission, they will be redirected back to the url they came from with an **authorization token** in the query string.

The screen will then make a `POST` request to our `auth/login` endpoint with the authorization token in the body of the request.

The service will take the authorization token and use it to acquire the user's profile information from google, including their email address and name, as well as an access token.

If a user does not exist matching the email address, a username will be automatically generated from the user's email address and the password will be set to a strong random password. A `User` object will be created in the database with the user's profile information and the generated username and password.

If a user already exists with the email address, the existing user will be retreived from the database and the access token will be updated with the new access token from Google.

The `POST` request to `auth/login` will return an access token and the user's profile information in the response body.

The access token will be used to authenticate the user in subsequent requests to the service.

We will have two separate Google OAuth2 credentials for the service:

- One for the development environment. This will allow requests from `localhost:8000` and `localhost:3000`.

- One for the production environment. This will allow requests from `https://www.example-service.com` and `https://example-client.com`.