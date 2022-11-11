from datetime import datetime


def parse_http_hosts(data: list):
    hosts = []
    for proxy_host in data:
        if proxy_host.get('certificate_id', None) == 0:
            host = {
                'id': proxy_host.get('id', None),
                'primary_domain': proxy_host.get('domain_names', [None])[0],
                'sans': proxy_host.get('domain_names', [None])[1:]
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
