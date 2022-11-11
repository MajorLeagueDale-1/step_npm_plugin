from argparse import ArgumentParser


parser = ArgumentParser(
    prog='Smallstep CA NPM Plugin', description="An automation solution for Nginx Proxy Manager (NPM) that monitors "
                                                "for proxy hosts without an SSL certificate and automatically "
                                                "generates one using Smallstep CA's step-cli tool."
)


npm = parser.add_argument_group('Nginx Proxy Manager')
npm.add_argument('-ns', '--npm-scheme', type=str, choices=('http', 'https'))
npm.add_argument('-nh', '--npm-host', type=str)
npm.add_argument('-np', '--npm-port', type=int)
npm.add_argument('-nu', '--npm-user', type=str)
npm.add_argument('-npw', '--npm-pass', type=str)


step = parser.add_argument_group('Smallstep CA')
step.add_argument('-ss', '--step-ca-scheme', type=str, choices=('http', 'https'))
step.add_argument('-sd', '--step-ca-domain', type=str)
step.add_argument('-sp', '--step-ca-port', type=int)
step.add_argument('-sf', '--step-ca-fingerprint', type=str)
step.add_argument('-spw', '--step-ca-provisioner-pass', type=str)

plugin = parser.add_argument_group('Plugin Config')
plugin.add_argument('--schedule', type=str)
plugin.add_argument('--log-level', type=str, choices=('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'))
