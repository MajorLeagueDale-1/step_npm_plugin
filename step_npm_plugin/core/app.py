import datetime
import logging
import random
from logging.config import dictConfig
import pathlib
import time

from step_npm_plugin.npm import (
    NginxProxyManagerClient, GenericNPMError, FailedToLogin, NotLoggedIn, CommunicationError, parse_http_hosts,
    parse_certificates
)
from step_npm_plugin.step import StepClient, StepCertificate, GenericStepError, NotBootstrapped
from step_npm_plugin.schedule import Timer

from . import settings


def setup(config: settings.AppConfig):
    # Configure Logging
    dictConfig({
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s %(filename)s:%(lineno)d] %(funcName)s(): %(message)s'
            }
        },
        'handlers': {
            'default': {
                'class': 'logging.StreamHandler',
                'formatter': 'standard',
                'level': config.LOG_LEVEL,
                'stream': 'ext://sys.stdout'
            }
        },
        'loggers': {
            '': {
                'handlers': ['default'],
                'level': 'WARNING',
                'propagate': False
            },
            'console': {
                'level': config.LOG_LEVEL,
                'handlers': ['default'],
                'propagate': False
            }
        }
    })

    logger = logging.getLogger('console')
    logger.debug('Logging initialised.')
    logger.debug(f'Dumping configuration: {config.__dict__}')

    secrets_dir = pathlib.Path('./.secrets/')

    if not secrets_dir.is_dir():
        secrets_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f'Secrets dir created: {secrets_dir.absolute()}')

    provisioner_pass_file = secrets_dir / 'provisioner_pass'

    with provisioner_pass_file.open('w') as pf:
        pf.write(config.STEP_CA_PROVISIONER_PASS.to_string())
    logger.debug(f"Written provisioner pass to: {provisioner_pass_file.absolute()}")

    step_client = StepClient(
        config.STEP_CA_SCHEME, config.STEP_CA_DOMAIN, config.STEP_CA_PORT, config.STEP_CA_FINGERPRINT.to_string(),
        provisioner_pass_file
    )
    step_client.bootstrap()

    logger.info("Step Client bootstrapped.")

    npm_client = NginxProxyManagerClient(
        config.NPM_HOST, config.NPM_PORT, (config.NPM_USER, config.NPM_PASS), config.NPM_SCHEME
    )

    npm_client.login()

    logger.info("NPM Client logged in.")
    logger.info("Setup complete.")

    return step_client, npm_client


def run(config: settings.AppConfig):
    logger = logging.getLogger('console')
    step_client, npm_client = setup(config)

    timer = Timer(sync_clock=False)
    timer.set_schedule(config.SCHEDULE)

    while True:
        try:
            if timer.breached:
                hosts = parse_http_hosts(npm_client.get_proxy_hosts())
                http_hosts = [host for host in hosts if host['is_https'] is False]
                certs = parse_certificates(npm_client.get_certificates())

                mapper = []

                # Phase 1 - Add new certificates
                if len(http_hosts) > 0:
                    domains = [host["primary_domain"] for host in http_hosts]
                    logger.info(f'New hosts found that are currently HTTP Only: {", ".join(domains)}')

                    for host in http_hosts:
                        existing_cert = next(
                            (cert for cert in certs if cert['primary_domain'] == host['primary_domain']), None
                        )

                        if existing_cert:
                            # Cert exists, use it.
                            logger.info(f'Existing certificate for {host["primary_domain"]} already on NPM.')
                            mapper.append({
                                'proxy_host': host['id'],
                                'certificate': existing_cert['id'],
                                'force': False
                            })
                        else:
                            # No existing cert, create a new one...
                            logger.info(f'No existing cert for {host["primary_domain"]}, need to generate one.')
                            crt_key_pair = step_client.create_certificate(host['primary_domain'], *host['sans'])
                            logger.debug(f'Certificate & Key created in the working directory: {crt_key_pair}')

                            step_cert = StepCertificate.from_file(*crt_key_pair)

                            cert_id = npm_client.create_certificate(step_cert, host['primary_domain'])

                            mapper.append({
                                'proxy_host': host['id'],
                                'certificate': cert_id,
                                'force': False
                            })

                # Phase 2 - Renew old ones
                for cert in certs:
                    rand_jitter = random.randrange(1, 10)
                    if (cert['expires'] - datetime.timedelta(minutes=rand_jitter)) < datetime.datetime.now():
                        logger.info(
                            f'Certificate {cert.get("primary_domain", None)} expires at'
                            f' {cert["expires"].strftime("%Y-%m-%d %H:%M:%S")}. Starting renewal.'
                        )

                        existing_host = next(
                            (host for host in hosts if host['primary_domain'] == cert['primary_domain']), None
                        )
                        if existing_host is None:
                            logger.debug(f'No matching host found for {cert["primary_domain"]}.')
                            continue
                        is_letsencrypt = existing_host.get('certificate', {}).get('provider', None) == 'letsencrypt'

                        if existing_host and not is_letsencrypt:
                            crt_key_pair = step_client.create_certificate(
                                existing_host['primary_domain'], *existing_host['sans']
                            )
                            logger.debug(f'Certificate & Key created in the working directory: {crt_key_pair}')

                            step_cert = StepCertificate.from_file(*crt_key_pair)
                            npm_client.delete_certificate(cert['id'])
                            new_cert_id = npm_client.create_certificate(step_cert, existing_host['primary_domain'])

                            mapper.append({
                                'proxy_host': existing_host['id'],
                                'certificate': new_cert_id,
                                'force': True
                            })
                        else:
                            logger.info(f'Cert not assigned to a host, or the host uses a letsencrypt certificate'
                                        f'... skipping.')

                for cert_map in mapper:
                    npm_client.update_proxy_host_certificate(
                        cert_map['proxy_host'], cert_map['certificate'], cert_map['force']
                    )

            time.sleep(1)

        except FailedToLogin as exc:
            # An attempt to re-login has failed. Something may have changed server-side.
            logger.error("An attempt to re login to NPM has failed, did the users credentials change?")
            logger.debug(f"{exc}")
            raise exc
