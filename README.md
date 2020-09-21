# Inventory

**Inventory** is a very simple web app for managing inventory. Its main use case is for resale operations.

*   *Items* are the things you are tracking
*   Items can be grouped into *categories*
*   *Orders* are used to increase your item inventory levels
*   *Sales* are used to decrease your item inventory levels
*   *Samples* are used to decrease your saleable inventory without actually making a sale

**Inventory** is multi-tenant but single-user. Anyone can sign in to the application, but each person that signs in will
only see their own data. No data is shared between users.

## Setup

### 1. OpenID Connect

**Inventory** uses OpenID Connect for authentication. You will need to use an OpenID provider (like Google) to generate
an OAuth 2.0 client ID and secret. Save these values in the environment variables `OPENID_CLIENT_ID` and
`OPENID_CLIENT_SECRET`.

When setting up the OAuth 2.0 client with your provider, set the redirect URI to
`https://<web-app-domain-name>/authorize`. If you are testing this application locally, you can set the redirect URI to
`http://localhost:8080/authorize`.

You will also need to set the URL of the OpenID discovery document for your OpenID provider in the environment variable
`OPENID_DISCOVERY_DOCUMENT`. Here are some common discovery document locations that have been tested with this
application:

* Sign in with a Google account: https://accounts.google.com/.well-known/openid-configuration
* Sign in with a Microsoft account: https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration

If you plan to serve the application over HTTPS, set the environment variable `SCHEME` to `https`. Otherwise, set it to
`http`. Most OpenID providers require the application to be served over HTTPS. The author recommends you serve this
application behind a reverse proxy that provides SSL termination, such as [Caddy][a], [Nginx][b], or [Traefik][c].

[a]: https://caddyserver.com/
[b]: https://www.nginx.com/
[c]: https://docs.traefik.io/

### 2. Database

**Inventory** needs a PostgreSQL database and permission to create tables. The environment variable `DSN` should contain
the connection string for the database, for example:

*   `DSN=postgresql://username:password@hostname:port/databasename`.

### 3. Environment variables

Here are all the environment variables **Inventory** needs to run, including those already mentioned.

*   `ADMIN_EMAIL`
*   `DSN` (PostgreSQL connection string)
*   `OPENID_CLIENT_ID`
*   `OPENID_CLIENT_SECRET`
*   `OPENID_DISCOVERY_DOCUMENT`
*   `SCHEME` (either `http` or `https`)
*   `SECRET_KEY` (a random string used for secure cookies)

By default, **Inventory** will listen on port 8080. Listen on a different port by setting the `PORT` environment
variable to the port number you want to listen on, for example:

*   `PORT=8088`

**Inventory** uses Python's logging module to send logs to `stdout`. You can customize the log format and level with the
`LOG_FORMAT` and `LOG_LEVEL` environment variables. Defaults are:

*   `LOG_FORMAT="%(levelname)s [%(name)s] %(message)s"`
*   `LOG_LEVEL=INFO`

### 4. Launch

**Inventory** can be launched using Docker:

    docker container run -p 8080:8080 -e DSN=... -e ... docker.pkg.github.com/williamjacksn/inventory/inventory
