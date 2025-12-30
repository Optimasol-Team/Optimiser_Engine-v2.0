from ...exceptions import OptimizerError

class DimensionNotRespected(OptimizerError) :
    pass
class NotEnoughVariables(OptimizerError) :
    pass 
class PermissionDeniedError(OptimizerError):
    pass 
class ContextNotDefined(OptimizerError) :
    pass



