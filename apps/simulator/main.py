from optimiser_engine.domain import Client 
import pandas as pd
from optimiser_engine.engine.service import TrajectorySystem, OptimizerService 
from datetime import datetime 
#Appeler le factory client : 
import matplotlib.pyplot as plt 
import numpy as np

with open("client_sample.yaml", "r") as f :
    content = f.read() 

client = Client.from_yaml(content) 

service = OptimizerService(24,15) 

df = pd.read_csv("weather.csv", parse_dates=["date"]).set_index("date")



start = datetime(2026,1,1,0)  
traj = service.trajectory_of_client(client, start, 45, df) 
print(f"Le prix optimisé est : {traj.compute_cost()}") 

traj_standard = service.trajectory_of_client_standard(client, start, 45, df, mode_WH = None, setpoint_temperature=60) 
traj_standard.update_X() 
print(f"Prix standard : {traj_standard.compute_cost()}")
N=int(service.horizon*60 /service.step_minutes)
t = np.linspace(0,service.horizon,N)

x = traj_standard.x 

print(f"autoconsommation optimisé : {traj.compute_self_consumption()}") 
print(f"autoconsommation standard : {traj_standard.compute_self_consumption()}") 




plt.plot(t,x) 

plt.show() 
