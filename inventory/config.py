import os


class Config:
    admin_email: str
    dsn: str
    google_login_client_id: str
    google_login_client_secret: str
    log_format: str
    log_level: str
    port: int
    scheme: str
    secret_key: str
    unix_socket: str

    def __init__(self):
        self.admin_email = os.getenv('ADMIN_EMAIL')
        self.dsn = os.getenv('DSN')
        self.google_login_client_id = os.getenv('GOOGLE_LOGIN_CLIENT_ID')
        self.google_login_client_secret = os.getenv('GOOGLE_LOGIN_CLIENT_SECRET')
        self.log_format = os.getenv('LOG_FORMAT', '%(levelname)s [%(name)s] %(message)s')
        self.log_level = os.getenv('LOG_LEVEL', 'DEBUG')
        self.port = int(os.getenv('PORT', '8080'))
        self.scheme = os.getenv('SCHEME', 'http')
        self.secret_key = os.getenv('SECRET_KEY')
        self.unix_socket = os.getenv('UNIX_SOCKET')
