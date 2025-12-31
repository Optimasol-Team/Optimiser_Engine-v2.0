"""Domain feature flags and optimisation mode declarations.

Author: @anaselb
"""

from enum import Enum


class OptimizationMode(Enum):
    """
    Supported optimisation objectives for controlling heater operation.

    Members
    -------
    AUTOCONS
        (autoconsommation) Optimise for self-consumption.
    COST
        (coût) Optimise for energy cost.
    """
    AUTOCONS = "AutoCons"
    COST = "cost"


class Features :
    """
    Encapsulates optional behaviours toggled for a given client configuration.

    Attributes
    ----------
    gradation : bool
        (gradation activée) Whether partial power gradation is available.
    mode : OptimizationMode
        (mode d'optimisation) Selected optimisation objective.
    """
    def __init__(self, gradation : bool, mode: OptimizationMode) :
        """
        Initialize feature flags for a client.

        Parameters
        ----------
        gradation : bool
            (gradation activée) Indicates if the heater can modulate power.
        mode : OptimizationMode
            (mode d'optimisation) Optimisation objective for the solver.

        Returns
        -------
        None
            (aucun retour) The constructor sets attributes without returning.
        """
        self.gradation = gradation #True or False selon si l'utilisateur a / veut le mode gradation
        self.mode = mode

    @property 
    def gradation(self) :
        """
        Flag indicating whether power gradation is enabled.

        Returns
        -------
        bool
            (gradation activée) True when gradation is available.
        """
        return self._gradation 
    @gradation.setter 
    def gradation(self, valeur) :
        """
        Set the gradation capability flag with strict type validation.

        Parameters
        ----------
        valeur : bool
            (gradation activée) Desired gradation availability.

        Returns
        -------
        None
            (aucun retour) The setter updates the gradation flag.

        Raises
        ------
        TypeError
            (type invalide) If the provided value is not boolean.
        """
        if not isinstance(valeur, bool) :
            raise TypeError("gradation doit être un booléen selon si le mode gradation est souhaité ou non") 
        self._gradation = valeur 
    
    @property
    def mode(self):
        """
        Current optimisation mode for the client.

        Returns
        -------
        OptimizationMode
            (mode d'optimisation) Selected objective enum value.
        """
        return self._mode
    
    @mode.setter
    def mode(self, valeur):
        """
        Assign the optimisation mode, ensuring it matches the expected enum.

        Parameters
        ----------
        valeur : OptimizationMode
            (mode d'optimisation) New optimisation target.

        Returns
        -------
        None
            (aucun retour) The setter stores the provided mode.

        Raises
        ------
        TypeError
            (type invalide) If the value is not an OptimizationMode member.
        """
        # Vérification ultra-robuste : ça DOIT être un membre de l'Enum
        if not isinstance(valeur, OptimizationMode):
            raise TypeError("Le mode doit être un objet OptimizationMode (ex: OptimizationMode.COST)")
        self._mode = valeur


    
    def __repr__(self) :
        """
        Return a human-readable description of the features.

        Returns
        -------
        str
            (représentation textuelle) Formatted summary.
        """
        if self.gradation :
            sum_grad = "- Gradation : ON\n" 
        else :
            sum_grad = "- Gradation : OFF\n"
        if self.mode == OptimizationMode.COST :
            sum_mode = "- Quantity optimized : Cost (€)" 
        else :
            sum_mode = "- Quantity optimized : Autoconsumption"
        
        return sum_grad + sum_mode 