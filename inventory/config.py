import os


class Config:
    admin_email: str
    dsn: str
    openid_client_id: str
    openid_client_secret: str
    log_format: str
    log_level: str
    openid_discovery_document: str
    port: int
    scheme: str
    secret_key: str

    def __init__(self):
        self.admin_email = os.getenv('ADMIN_EMAIL')
        self.dsn = os.getenv('DSN')
        self.openid_client_id = os.getenv('OPENID_CLIENT_ID')
        self.openid_client_secret = os.getenv('OPENID_CLIENT_SECRET')
        self.log_format = os.getenv('LOG_FORMAT', '%(levelname)s [%(name)s] %(message)s')
        self.log_level = os.getenv('LOG_LEVEL', 'DEBUG')
        self.openid_discovery_document = os.getenv('OPENID_DISCOVERY_DOCUMENT')
        self.port = int(os.getenv('PORT', '8080'))
        self.scheme = os.getenv('SCHEME', 'http')
        self.secret_key = os.getenv('SECRET_KEY')
