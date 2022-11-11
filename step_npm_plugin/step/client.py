import logging
import pathlib
import subprocess

from step_npm_plugin.step.exceptions import GenericStepError, NotBootstrapped, ProcessError


logger = logging.getLogger('console')


class StepClient:
    """
    An interface to the commandline interface for Smallstep CA.

    Warning: This version of StepClient is considered _unsafe_ due to the use of "shell=True" in subprocess calls.
    The `shell` flag is required for the step-cli client as it uses /dev/tty for file access. There may be a better way
    of doing this so will require revisiting in the future.
    """
    ca_scheme: str = "https"
    ca_domain: str = None
    ca_port: int = 9000
    ca_fingerprint: str = None
    provisioner_pass_file: pathlib.Path = None

    ca_url = None
    _bootstrapped = False

    def __init__(self, ca_scheme: str, ca_domain: str, ca_port: int, ca_fingerprint: str,
                 provisioner_pass_file: pathlib.Path):
        self.ca_scheme = ca_scheme
        self.ca_domain = ca_domain
        self.ca_port = ca_port
        self.ca_fingerprint = ca_fingerprint
        self.provisioner_pass_file = provisioner_pass_file

        self._build_ca_url()

    def _build_ca_url(self):
        self.ca_url = f"{self.ca_scheme}://{self.ca_domain}:{self.ca_port}"

    def bootstrap(self):
        commands = [
            'step', 'ca', 'bootstrap', '--ca-url', self.ca_url, '--fingerprint', self.ca_fingerprint, '--force'
        ]
        process = subprocess.run(" ".join(commands), stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)

        if not process.returncode == 0:
            raise GenericStepError(process.stderr.decode('utf-8'))

        self._bootstrapped = True
        return process

    def get_ca_health(self):
        if not self._bootstrapped:
            raise NotBootstrapped("Client has not yet been bootstrapped.")

        commands = ['step', 'ca', 'health']
        process = subprocess.run(" ".join(commands), stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)

        return process

    def create_certificate(
            self, common_name: str, *sans: str, not_before: str = None, not_after: str = None
    ) -> tuple[pathlib.Path, pathlib.Path]:
        if not self._bootstrapped:
            raise NotBootstrapped("Client has not yet been bootstrapped.")

        commands = ['step', 'ca', 'certificate']

        for san in sans:
            commands.append('--san')
            commands.append(san)

        if not_before:
            commands.append('--not-before')
            commands.append(not_before)

        if not_after:
            commands.append('--not-after')
            commands.append(not_after)

        commands.append('--provisioner-password-file')
        commands.append(self.provisioner_pass_file.absolute().__str__())
        commands.append('--force')

        commands.append(common_name)
        commands.append(common_name + '.crt')
        commands.append(common_name + '.key')

        process = subprocess.run(" ".join(commands), stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)

        logger.debug(f'Process run')

        if process.returncode != 0:
            logger.debug(f'Run failed with error: {process.stderr.decode("utf-8")}')
            raise ProcessError(f'Run failed with error: {process.stderr.decode("utf-8")}')

        return (
            pathlib.Path('./' + common_name + '.crt').absolute(), pathlib.Path('./' + common_name + '.key').absolute()
        )
