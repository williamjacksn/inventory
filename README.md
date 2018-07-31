# Inventory

**Inventory** is a very simple web app for managing inventory. Its main use case is for resale operations.

*   *Items* are the things you are tracking
*   Items can be grouped into *categories*
*   *Orders* are used to increase your item inventory levels
*   *Sales* are used to decrease your item inventory levels
*   *Samples* are used to decrease your saleable inventory without actually making a sale

## Setup

### 1. Google Sign-In

**Inventory** uses Google Sign-In for authentication. You will need to use the
[Google Cloud Console](https://console.cloud.google.com/apis/credentials) to generate an OAuth 2.0 client ID and secret.
Save these values in the environment variables `GOOGLE_LOGIN_CLIENT_ID` and `GOOGLE_LOGIN_CLIENT_SECRET`.

If you plan to serve the application over HTTPS, set the environment variable `GOOGLE_LOGIN_REDIRECT_SCHEME` to `https`.
Otherwise, set it to `http`.

### 2. Database

**Inventory** needs a PostgreSQL database and permission to create tables. The environment variable `DSN` should contain
the connection string for the database, for example:

*   `DSN=postgresql://username:password@hostname:port/databasename`.

### 3. Install

**Inventory** requires at least Python 3.6. You can install from PyPI:

    pip install inventory==2.0.1

Installation will add the `inventory` command to your path.

### 4. Environment variables

Here are all the environment variables **Inventory** needs to run, including those already mentioned.

*   `DSN` (PostgreSQL connection string)
*   `GOOGLE_LOGIN_CLIENT_ID`
*   `GOOGLE_LOGIN_CLIENT_SECRET`
*   `GOOGLE_LOGIN_REDIRECT_SCHEME` (either `http` or `https`)
*   `SECRET_KEY` (a random string used for secure cookies)

By default, **Inventory** will listen on port 8080. Listen on a different port by setting the `PORT` environment
variable to the port number you want to listen on, for example:

*   `PORT=8088`

If you want to listen on a Unix socket instead of a TCP port, set the environment variable `UNIX_SOCKET` to
the path of the socket, for example:

*   `UNIX_SOCKET=/var/run/inventory.socket`

If `UNIX_SOCKET` and `PORT` are both set, `UNIX_SOCKET` will take priority.

**Inventory** uses Python's logging module to send logs to `stdout`. You can customize the log format and level with the
`LOG_FORMAT` and `LOG_LEVEL` environment variables. Defaults are:

*   `LOG_FORMAT="%(levelname)s [%(name)s] %(message)s"`
*   `LOG_LEVEL=DEBUG`

### 5. Launch

With environment variables set as explained, Launch the web app with the command `inventory`.
