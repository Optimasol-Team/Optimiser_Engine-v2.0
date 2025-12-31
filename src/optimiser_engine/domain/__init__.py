"""Domain models for configuring optimisation clients, constraints, schedules, tariffs, and assets used by the engine.

Author: @anaselb

This package groups the business entities required to describe a client scenario, including planning setpoints, consumption constraints, feature flags, pricing models, and the water heater asset. It exposes ready-to-use classes to build a complete domain configuration that can be consumed by the optimiser engine.
"""
from .client import Client 
from .constraints import Constraints, ConsumptionProfile 
from .consignes_models import Planning, Setpoint
from .features_models import Features 
from .prices_model import Prices
from .water_heater_model import WaterHeater
from .common import TimeSlot 
