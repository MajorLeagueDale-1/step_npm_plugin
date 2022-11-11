

class GenericStepError(Exception):
    """
    Generic Exception for Step CLI related errors
    """
    pass


class NotBootstrapped(GenericStepError):
    """
    Error trying to execute an actions before the client has been bootstrapped.
    """
    pass


class ProcessError(GenericStepError):
    """
    Error with running Step-CLI
    """
    pass
