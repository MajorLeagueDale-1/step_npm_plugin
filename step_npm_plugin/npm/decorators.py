import logging
from requests.exceptions import ReadTimeout, ConnectTimeout

from .exceptions import GenericNPMError, NotLoggedIn, CommunicationError


RETRIES = 3
logger = logging.getLogger('console')


def retry_handler(f):
    def wrapper(*args, **kwargs):
        counter = 0
        data = {}

        while counter < RETRIES:
            try:
                data = f(*args, **kwargs)
            except NotLoggedIn:
                counter += 1
                logger.debug('Token expired, attempting to log back in.')
                args[0].login()
            except (GenericNPMError, CommunicationError, ReadTimeout, ConnectTimeout):
                counter += 1
                logger.debug(f"Failed to access NPM after {counter} tries...")
            else:
                break

        if counter >= RETRIES:
            raise GenericNPMError(f"Failed to communicate with NPM on URI {args[1]}.")

        return data

    return wrapper
