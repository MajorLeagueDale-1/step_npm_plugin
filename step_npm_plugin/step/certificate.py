import logging
import pathlib

from cryptography import x509
from cryptography.x509 import Certificate
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key, Encoding, PrivateFormat, NoEncryption
)
from cryptography.hazmat.primitives.asymmetric.types import PRIVATE_KEY_TYPES


logger = logging.getLogger('console')


class StepCertificate:
    certificate = None
    intermediate = None
    private_key = None

    def __init__(
            self, certificate: Certificate, certificate_key: PRIVATE_KEY_TYPES or None,
            intermediates: list[Certificate] = None,
    ):
        self.certificate = certificate
        self.intermediates = intermediates
        self.private_key = certificate_key

    @classmethod
    def from_file(cls, certificate: pathlib.Path, certificate_key: pathlib.Path):
        with open(certificate, 'rb') as f:
            cert = []
            cert_list = []

            for line in f.readlines():
                cert.append(line)
                if line.startswith(b'-----END CERTIFICATE-----'):
                    cert_list.append(b''.join(cert))
                    cert.clear()

        web_cert = x509.load_pem_x509_certificate(cert_list.pop(0))
        intermediates = []

        if len(cert_list) > 0:
            logger.debug('Certificate contains an intermediate chain - importing...')
            for cert in cert_list:
                intermediates.append(x509.load_pem_x509_certificate(cert))

        with open(certificate_key, 'rb') as f:
            private_key = load_pem_private_key(f.read(), None)

        logger.debug(f'Created certificate instance from {certificate} and {certificate_key} files.')

        return cls(web_cert, private_key, intermediates=intermediates)

    @property
    def is_pair(self):
        return True if self.certificate and self.private_key else False

    @property
    def certificate_bytes(self):
        return self.certificate.public_bytes(Encoding.PEM)

    @property
    def intermediate_bytes(self):
        return b'\n'.join([intermediate.public_bytes(Encoding.PEM) for intermediate in self.intermediates])

    @property
    def private_key_bytes(self):
        return self.private_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())

    def __repr__(self):
        return f"<StepCertificate {self.certificate.__repr__()}, {self.private_key.__repr__()}>"

    def __str__(self):
        return f"Certificate: {self.certificate.subject.rfc4514_string()}, Key: {self.private_key.__str__()}"
