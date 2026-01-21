from datetime import datetime, timezone


def parse_http_hosts(data: list):
    hosts = []
    for proxy_host in data:

        try:
            created_time = datetime.fromisoformat(proxy_host['created_on']).astimezone(timezone.utc)
        except ValueError:
            created_time = None

        host = {
            'id': proxy_host.get('id', None),
            'primary_domain': proxy_host.get('domain_names', [None])[0],
            'sans': proxy_host.get('domain_names', [None])[1:],
            'is_https': False if proxy_host.get('certificate_id', 0) == 0 else True,
            'created_on': created_time
        }

        hosts.append(host)

    return hosts


def parse_certificates(data: list):
    certs = []
    for certificate in data:
        cert = {
            'id': certificate.get('id', None),
            'primary_domain': certificate.get('domain_names', [None])[0],
            'expires': datetime.strptime(certificate.get('expires_on'), '%Y-%m-%dT%H:%M:%S.%fZ')
        }
        certs.append(cert)

    return certs
