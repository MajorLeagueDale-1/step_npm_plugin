

class GenericNPMError(Exception):
    """
    Generic error handling NPM communication
    """
    pass


class FailedToLogin(GenericNPMError):
    """
    Fatal error, the credentials used to access NPM are incorrect.
    """
    pass


class NotLoggedIn(GenericNPMError):
    """
    The NPM client is not authenticated and needs to be logged in again. Safe to retry.
    """
    pass


class CommunicationError(GenericNPMError):
    """
    Unable to communicate with the NPM host, or it responded in a way that we cannot handle.
    """
