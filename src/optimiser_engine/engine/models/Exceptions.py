"""Custom exceptions used throughout the optimisation engine models.

Author: @anaselb
"""


class DimensionNotRespected(Exception) :
    """
    Raised when an array or vector does not meet the expected dimensionality.
    """
    pass
class NotEnoughVariables(Exception) :
    """
    Raised when required variables are missing to complete an operation.
    """
    pass 
class PermissionDeniedError(Exception):
    """
    Raised when attempting an action that is not permitted in the current state.
    """
    pass 
class ContextNotDefined(Exception) :
    """
    Raised when operations require a context that has not been provided.
    """
    pass

class WeatherNotValid(Exception) :
    """
    Raised when external weather or production data fails validation.
    """
    pass 

class SolverFailed(Exception) :
    """
    Raised when the optimisation solver cannot produce a valid trajectory.
    """
    pass