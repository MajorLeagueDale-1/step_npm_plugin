import logging
import requests

from step_npm_plugin.core.data_types import SecureString
from step_npm_plugin.step.certificate import StepCertificate

from .decorators import retry_handler
from .exceptions import GenericNPMError, FailedToLogin, NotLoggedIn, CommunicationError


logger = logging.getLogger('console')


class NginxProxyManagerClient:
    host: str = None
    port: int = None
    scheme: str = None
    uri: str = None
    session: requests.Session = None

    __auth: tuple = None

    def __init__(self, host: str, port: int, auth: tuple[str, SecureString], scheme: str = "http"):
        self.host = host
        self.port = port
        self.scheme = scheme    # NPM defaults to HTTP

        self.__auth = auth

        self.session = requests.Session()
        self.__build_uri()

    def __build_uri(self):
        self.uri = f"{self.scheme}://{self.host}:{self.port}"

    @staticmethod
    def _response_parse(r: requests.Response):
        if r.status_code in (200, 201):
            data = r.json()
        elif r.status_code in (401, 403):
            logger.debug('Token has timed out. Need to login and retry.')
            raise NotLoggedIn("Token timed out.")
        else:
            data = {}

        return data

    @retry_handler
    def _get(self, uri: str, **kwargs):
        logger.debug(f"GET issued to: {uri}")
        r = self.session.get(uri, timeout=5, **kwargs)
        return self._response_parse(r)

    @retry_handler
    def _post(self, uri: str, data: dict = None, **kwargs):
        logger.debug(f'POST issued to: {uri}')
        r = self.session.post(uri, json=data, timeout=5, **kwargs)
        return self._response_parse(r)

    def _put(self, uri: str, data: dict = None, **kwargs):
        logger.debug(f'PUT issued to: {uri}')
        r = self.session.put(uri, json=data, timeout=5, **kwargs)
        return self._response_parse(r)

    def login(self) -> None:
        token_uri = f"{self.uri}/api/tokens"

        post = {
            "identity": self.__auth[0],
            "secret": self.__auth[1].to_string()
        }

        logger.debug(f'Login to proxy initiated to {token_uri}')

        r = self.session.post(token_uri, json=post)

        if r.status_code in (200, 201):
            logger.debug('Login success, received token from NPM.')
            self.session.headers.update({"Authorization": f"Bearer {r.json()['token']}"})
        elif r.status_code == 401 or r.status_code == 403:
            # Wrong login credentials {"error":{"message": "..."}}
            logger.critical("Incorrect login credentials provided for NPM.")
            raise FailedToLogin("Incorrect credentials provided to log in to NPM.")
        else:
            # Random error. Report it. {"error":{"message": "..."}}
            logger.warning("Communication error occurred, will retry later.")
            logger.debug(f"{r}")
            raise GenericNPMError(f"Unknown error occurred communicating with NPM. Received: {r.json()}")

    def get_proxy_hosts(self) -> list:
        url = f"{self.uri}/api/nginx/proxy-hosts"
        data = self._get(url)

        return data

    def get_certificates(self) -> list:
        url = f"{self.uri}/api/nginx/certificates"
        data = self._get(url)

        return data

    def create_certificate(self, step_cert: StepCertificate, common_name: str) -> int:
        """
        Create a new certificate in Nginx Proxy Manager.

        Nginx Proxy Managers API goes through a two-step process to create a certificate. Firstly, POST
        /api/nginx/certificates with {"nice_name": <common_name>, "provider": "other"}. The response will give a new
        certificate ID: {"id": <int>, ...} with status 201. Using this ID, you upload the certificates using
        multipart/form-data to /api/nginx/certificates/<id>/upload with the keys
        {"certificate": "...", "certificate_key": "..."}. Due to a bug in NPM, uploading an intermediate cert in the
        `intermediate_certificate` field does not attach to the certificate and must be concatenated in to the main
        certificate.

        :param StepCertificate step_cert: Smallstep CA generated certificate and key pair.
        :param str common_name: Common name for the certificate being added to NPM.
        :return: New Certificate ID
        """
        create_url = f"{self.uri}/api/nginx/certificates"
        new_cert_id = self._post(create_url, {"nice_name": common_name, "provider": "other"})['id']

        logger.debug(f'New Certificate with created with ID: {new_cert_id}')

        upload_url = f"{create_url}/{new_cert_id}/upload"
        cert_upload = self._post(
            upload_url, files={
                'certificate': step_cert.certificate_bytes + step_cert.intermediate_bytes,
                'certificate_key': step_cert.private_key_bytes
            }
        )

        logger.info(f'Certificate {new_cert_id} uploaded successfully.')

        return new_cert_id

    def update_proxy_host_certificate(self, proxy_host_id: int, certificate_id: int) -> None:
        """
        Updates a proxy host with a certificate to use.

        To apply a new certificate, we get the current state of the proxy host and then apply the certificate with
        the additional configurations using certificate_id, hsts_enabled and ssl_forced.

        :param int proxy_host_id: ID of the Proxy Host to be updated
        :param int certificate_id: ID of the certificate to be applied to the proxy host
        :return:
        """
        proxy_host_url = f"{self.uri}/api/nginx/proxy-hosts/{proxy_host_id}"
        proxy_host = self._get(proxy_host_url)

        if proxy_host.get('certificate_id', None) != 0:
            logger.info(f'Recheck of proxy host {proxy_host.get("domain_names", [None])[0]} already has a '
                        f'certificate assigned. Skipping host...')
            return

        proxy_host_update = self._put(proxy_host_url, {
            'certificate_id': certificate_id,
            'hsts_enabled': True,
            'ssl_forced': True
        })

        logger.info(f'Configuration updated successfully!')

        return
