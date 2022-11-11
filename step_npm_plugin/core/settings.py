import argparse
import os

from step_npm_plugin.core.data_types import SecureString


class AppConfig:
    """
    Application configuration storage and setup.
    """
    SCHEDULE: str = "10s"
    LOG_LEVEL: str = "INFO"

    STEP_CA_SCHEME: str = "https"
    STEP_CA_DOMAIN: str = None
    STEP_CA_PORT: int = 9000
    STEP_CA_FINGERPRINT: SecureString = None
    STEP_CA_PROVISIONER_PASS: SecureString = None

    NPM_SCHEME: str = "http"
    NPM_HOST: str = None
    NPM_PORT: int = 81
    NPM_USER: str = None
    NPM_PASS: SecureString = None

    __REQUIRED_ATTRS: list = [
        'STEP_CA_DOMAIN', 'STEP_CA_FINGERPRINT', 'STEP_CA_PROVISIONER_PASS', 'NPM_HOST', 'NPM_USER', 'NPM_PASS'
    ]

    def __init__(self, args: argparse.ArgumentParser):
        missing_args = []
        for key, value in AppConfig.__dict__.items():
            if key.startswith('_'):
                continue
            var_type = self.__annotations__.get(key.upper(), None)
            if getattr(args, key.lower()):
                setattr(self, key.upper(), var_type(getattr(args, key.lower())))
            elif os.environ.get(key.upper(), None):
                setattr(self, key.upper(), var_type(os.environ.get(key.upper())))
            else:
                setattr(self, key.upper(), getattr(self, key.upper()))

            if key.upper() in self.__REQUIRED_ATTRS and not getattr(self, key.upper()):
                missing_args.append(key.upper())

        if missing_args:
            raise ValueError(f'Missing required configuration in either Env or CLI command: {", ".join(missing_args)}')
