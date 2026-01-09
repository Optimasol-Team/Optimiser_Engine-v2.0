"""Solver orchestration for optimisation problems using SciPy backends.

Author: @anaselb
"""
import numpy as np
from scipy.optimize import linprog, milp, LinearConstraint, Bounds


from .models.optimisation_inputs import OptimizationInputs
from .models.trajectory import TrajectorySystem 

from ..domain.features_models import OptimizationMode 

class Solver:
    """
    Handles mathematical optimisation of trajectories using SciPy linprog or MILP routines.
    """ 
    
    def __init__(self, timeout=60):
        """
        Create a solver instance with an optional time limit.

        Parameters
        ----------
        timeout : int
            (délai maximum) Maximum allowed solving time in seconds.

        Returns
        -------
        None
            (aucun retour) Initializes solver settings.
        """
        self.timeout = timeout

    def solve(self, inputs: OptimizationInputs) -> TrajectorySystem:
        """
        Solve the optimisation problem defined by the provided inputs.

        Parameters
        ----------
        inputs : OptimizationInputs
            (données d'optimisation) Structured matrices, bounds, and context for the solver.

        Returns
        -------
        TrajectorySystem
            (trajectoire optimisée) Completed trajectory populated with solver results.

        Raises
        ------
        RuntimeError
            (échec du solveur) If the underlying optimisation routine does not converge.
        """ 
        
        # 1. Extraction des matrices
        A_eq = inputs.A_eq() 
        B_eq = inputs.B_eq() 
        
        # 2. Sélection de l'objectif (Coût ou Autoconsommation)
        mode = inputs.mode 
        if mode == OptimizationMode.COST:
            Objective_vec = inputs.C_cost() 
        elif mode == OptimizationMode.AUTOCONS:
            Objective_vec = inputs.C_autocons()
        
        # 3. Récupération des bornes brutes [(min, max), ...]
        raw_bounds = inputs.get_bounds() 

        # --- CAS 1 : Gradation (Tout est continu) -> LINPROG
        if inputs.system_config.is_gradation:
            res = linprog(c=Objective_vec, 
                          A_eq=A_eq, 
                          b_eq=B_eq, 
                          bounds=raw_bounds, 
                          method='highs',
                          options={'time_limit': self.timeout})
            
            if not res.success:
                raise RuntimeError(f"Échec LINPROG : {res.message}")  #A modifier / améliorer plus tard. 

        # --- CAS 2 : Tout ou Rien (Entier/Mixte) -> MILP ---
        else:
            # a. Intégrité
            integrality = inputs.get_integrality_vector() 
            
            # b. Contraintes d'égalité pour MILP (lb <= Ax <= ub)
            constraints = []
            if A_eq is not None and B_eq is not None:
                constraints.append(LinearConstraint(A_eq, lb=B_eq, ub=B_eq))
            
            # c. Conversion des bornes pour MILP (Pas de None, il faut +/- inf)
            # On dézippe la liste [(min, max), ...]
            lb = [b[0] if b[0] is not None else -np.inf for b in raw_bounds]
            ub = [b[1] if b[1] is not None else np.inf for b in raw_bounds]
            bounds_obj = Bounds(lb, ub)
            
            res = milp(c=Objective_vec, 
                       constraints=constraints,
                       integrality=integrality, 
                       bounds=bounds_obj,
                       options={'time_limit': self.timeout})

            if not res.success:
                raise RuntimeError(f"Échec MILP : {res.message}")
        
        # 4. Construction de la Trajectoire
        # On utilise le constructeur standard ou la factory si disponible
        traj = TrajectorySystem(inputs.system_config, inputs.context, inputs.initial_temperature) 
        
        # ÉTAPE CLÉ 1 : On passe en mode "Solveur en cours" (Droit d'écriture)
        traj.make_solver_traj() 
        
        # Injection du résultat X
        traj.upload_X_vector(res.x) 
        
        # Injection du coût calculé par le solveur (plus précis)
        if mode == OptimizationMode.COST:
            cost = res.fun / (1000*(60/(inputs.context.step_minutes)))
            traj.upload_cost(cost) 
        # Si mode AUTOCONS, tu pourrais vouloir uploader le score d'autoconsommation si prévu
        
        # ÉTAPE CLÉ 2 : On passe en mode "Livré" (Verrouillage final)
        traj.make_solver_delivered_traj() 
        
        return traj

        











