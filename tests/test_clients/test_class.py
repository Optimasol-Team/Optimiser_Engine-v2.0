# Importer les dépendances : CLasse client et ses sous classes : 
from datetime import time 
from optimiser_engine.domain import Setpoint
# Tester les initialisations : 

#############TEST 1 : Tester les consignes_models : ############################################
time1, time2, time3 = time(11,30), time(15,45), time(20,15) 

consigne1 = Setpoint(1,time1,60,45)

print(consigne1)








#Tester les factories : 



