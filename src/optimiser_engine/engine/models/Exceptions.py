"""Custom exceptions used throughout the optimisation engine models.

Author: @anaselb
"""
from ...exceptions import OptimizerError

class DimensionNotRespected(OptimizerError) :
    """
    Raised when an array or vector does not meet the expected dimensionality.
    """
    pass
class NotEnoughVariables(OptimizerError) :
    """
    Raised when required variables are missing to complete an operation.
    """
    pass 
class PermissionDeniedError(OptimizerError):
    """
    Raised when attempting an action that is not permitted in the current state.
    """
    pass 
class ContextNotDefined(OptimizerError) :
    """
    Raised when operations require a context that has not been provided.
    """
    pass

class WeatherNotValid(OptimizerError) :
    """
    Raised when external weather or production data fails validation.
    """
    pass 

class SolverFailed(OptimizerError) :
    """
    Raised when the optimisation solver cannot produce a valid trajectory.
    """
    pass
