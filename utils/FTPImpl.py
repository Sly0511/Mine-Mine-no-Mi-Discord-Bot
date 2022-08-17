from ftputil import FTPHost

from utils.configs import FTPConfig


class FTPServer:
    def __init__(self, config: FTPConfig):
        self.config = config

    def connect(self):
        self.ftp = FTPHost(self.config.host, self.config.username, self.config.password)
        return self.ftp
