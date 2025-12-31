"""Client domain aggregate assembling planning, constraints, pricing, and assets for optimisation.

Author: @anaselb
"""
from .consignes_models import Planning, Setpoint
from .constraints import Constraints, ConsumptionProfile
from .features_models import Features, OptimizationMode
from .prices_model import Prices
from .water_heater_model import WaterHeater 
from .common import TimeSlot 


import yaml  
import numpy as np
from datetime import datetime, time
from typing import Dict, Any

class Client :
    """
    Represents a fully configured optimisation client with schedules, assets, and tariffs.

    Attributes
    ----------
    planning : Planning
        (planning hebdomadaire) Schedule of temperature setpoints.
    constraints : Constraints
        (contraintes) Operational restrictions and consumption profiles.
    features : Features
        (fonctionnalités) Feature flags including optimisation mode and gradation.
    prices : Prices
        (tarification) Pricing configuration for energy purchase and resale.
    water_heater : WaterHeater
        (chauffe-eau) Physical model of the client's water heater.
    client_id : int
        (identifiant client) Identifier associated with the client record.
    """
    def __init__(self, 
                 planning : Planning, 
                 constraints : Constraints, 
                 features : Features, 
                 prices : Prices, 
                 water_heater : WaterHeater, 
                 client_id = 0) :
        """
        Construct a client aggregate from its component configurations.

        Parameters
        ----------
        planning : Planning
            (planning hebdomadaire) Setpoint schedule for the client.
        constraints : Constraints
            (contraintes) Restrictions and baseline consumption.
        features : Features
            (fonctionnalités) Flags controlling optimisation behaviour.
        prices : Prices
            (tarification) Pricing scheme for energy purchase and resale.
        water_heater : WaterHeater
            (chauffe-eau) Asset model used in optimisation.
        client_id : int, optional
            (identifiant client) Optional identifier for the client, defaults to 0.

        Returns
        -------
        None
            (aucun retour) Initializes attributes for the client instance.
        """
        self.client_id = client_id 
        self.planning = planning  
        self.constraints = constraints 
        self.features = features
        self.prices = prices
        self.water_heater = water_heater 
    
    def __repr__(self) :
        """
        Represent the client by its identifier.

        Returns
        -------
        str
            (représentation textuelle) String including the client_id.
        """
        return f"client : {self.client_id}" 
    
    @staticmethod
    def _parse_time_str(time_str: str) -> time:
        """
        Convert a 'HH:MM' string into a datetime.time object.

        Parameters
        ----------
        time_str : str
            (chaîne horaire) Text representation of a time value.

        Returns
        -------
        datetime.time or None
            (heure) Parsed time, or None when the input is falsy.
        """
        if not time_str:
            return None
        # On force la conversion en string au cas où le parser YAML 
        # interpréterait 12:00 comme un entier (base 60)
        return datetime.strptime(str(time_str), "%H:%M").time()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Client':
        """
        Build a Client instance from a dictionary representation.

        Parameters
        ----------
        data : dict
            (données client) Mapping describing water heater, prices, features, constraints, and planning.

        Returns
        -------
        Client
            (instance client) Newly constructed client object.

        Raises
        ------
        ValueError
            (données invalides) If any required field is invalid or parsing fails.
        """
        try:
            # 1. Instanciation du Chauffe-Eau
            wh_data = data.get("water_heater", {})
            water_heater = WaterHeater(
                volume=wh_data.get("volume", 0),
                power=wh_data.get("power", 0)
            )
            if "insulation_coeff" in wh_data:
                water_heater.insulation_coefficient = wh_data["insulation_coeff"]
            if "temp_cold_water" in wh_data:
                water_heater.cold_water_temperature = wh_data["temp_cold_water"]

            # 2. Instanciation des Prix
            p_data = data.get("prices", {})
            prices = Prices()
            price_mode = p_data.get("mode", "BASE")
            prices.mode = price_mode
            
            if "hp_price" in p_data: prices.hp = p_data["hp_price"]
            if "hc_price" in p_data: prices.hc = p_data["hc_price"]
            if "base_price" in p_data: prices.base = p_data["base_price"]
            if "resell_price" in p_data: prices.resale_price = p_data["resell_price"]

            if price_mode == "HPHC" and "hp_slots" in p_data:
                time_slots = []
                for slot in p_data["hp_slots"]:
                    time_slots.append(TimeSlot(
                        start=cls._parse_time_str(slot["start"]),
                        end=cls._parse_time_str(slot["end"])
                    ))
                prices.hp_slots = time_slots

            # 3. Instanciation des Features
            f_data = data.get("features", {})
            mode_str = f_data.get("mode", "COST")
            # Conversion string -> Enum
            mode_enum = OptimizationMode(mode_str) 
            
            features = Features(
                gradation=f_data.get("gradation", False),
                mode=mode_enum
            )

            # 4. Instanciation des Constraints
            c_data = data.get("constraints", {})
            
            forbidden_slots = []
            for slot in c_data.get("forbidden_slots", []):
                forbidden_slots.append(TimeSlot(
                    start=cls._parse_time_str(slot["start"]),
                    end=cls._parse_time_str(slot["end"])
                ))

            profil_data = c_data.get("consumption_profile")
            if profil_data:
                matrice = np.array(profil_data)
                consumption_profile = ConsumptionProfile(matrix_7x24=matrice)
            else:
                consumption_profile = ConsumptionProfile()

            constraints = Constraints(
                consumption_profile=consumption_profile,
                forbidden_slots=forbidden_slots,
                minimum_temperature=c_data.get("min_temp", 10.0)
            )

            # 5. Instanciation du Planning
            planning = Planning()
            raw_setpoints = data.get("planning", [])
            liste_objets_setpoints = []
            
            for cons in raw_setpoints:
                c = Setpoint(
                    day=cons["day"],
                    time_of_day=cls._parse_time_str(cons["time"]),
                    temperature=cons.get("target_temp", 50.0),
                    volume=cons.get("volume", 0.0)
                )
                liste_objets_setpoints.append(c)
            
            planning.setpoints = liste_objets_setpoints

            # 6. Création finale
            return cls(
                planning=planning,
                constraints=constraints,
                features=features,
                prices=prices,
                water_heater=water_heater,
                client_id=data.get("client_id", 0)
            )

        except Exception as e:
            raise ValueError(f"Erreur configuration Client : {str(e)}")

    @classmethod
    def from_yaml(cls, yaml_str: str) -> 'Client':
        """
        Instantiate a Client from a YAML string payload.

        Parameters
        ----------
        yaml_str : str
            (contenu YAML) YAML-formatted string describing a client.

        Returns
        -------
        Client
            (instance client) Parsed client configuration.
        """
        data = yaml.safe_load(yaml_str)
        return cls.from_dict(data)

    @classmethod
    def from_yaml_file(cls, file_path: str) -> 'Client':
        """
        Instantiate a Client from a YAML file on disk.

        Parameters
        ----------
        file_path : str
            (chemin du fichier) Path to a YAML configuration file.

        Returns
        -------
        Client
            (instance client) Parsed client object based on file contents.
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize the client configuration to a dictionary.

        Returns
        -------
        dict
            (données client) JSON/YAML-friendly representation of the client.
        """
        # A. Water Heater
        wh_data = {
            "volume": self.water_heater.volume,
            "power": self.water_heater.power,
            "insulation_coeff": self.water_heater.insulation_coefficient,
            "temp_cold_water": self.water_heater.cold_water_temperature
        }

        # B. Prices
        p_data = {
            "mode": self.prices.mode,
            "hp_price": self.prices.hp if self.prices.mode == "HPHC" else None,
            "hc_price": self.prices.hc if self.prices.mode == "HPHC" else None,
            "base_price": self.prices.base if self.prices.mode == "BASE" else None,
            "resell_price": self.prices.resale_price
        }
        # Gestion des créneaux HP si mode HPHC
        if self.prices.mode == "HPHC":
            slots = []
            for c in self.prices.hp_slots:
                slots.append({
                    "start": c.start.strftime("%H:%M"), 
                    "end": c.end.strftime("%H:%M")
                })
            p_data["hp_slots"] = slots

        # C. Features
        f_data = {
            "gradation": self.features.gradation,
            # On récupère la valeur brute de l'Enum ("cost" ou "AutoCons")
            "mode": self.features.mode.value 
        }

        # D. Constraints
        c_data = {
            "min_temp": self.constraints.minimum_temperature,
            "forbidden_slots": [
                {"start": c.start.strftime("%H:%M"), "end": c.end.strftime("%H:%M")}
                for c in self.constraints.forbidden_slots
            ]
        }
        # Note : On ne sérialise pas forcément la matrice géante de consommation 
        # pour ne pas polluer l'affichage, sauf si nécessaire.
        # Ici je mets null par défaut pour simplifier.
        c_data["consumption_profile"] = None 

        # E. Planning
        planning_list = []
        for c in self.planning.setpoints:
            planning_list.append({
                "day": c.day,
                "time": c.time.strftime("%H:%M"),
                "target_temp": c.temperature,
                "volume": c.drawn_volume
            })

        return {
            "client_id": self.client_id,
            "water_heater": wh_data,
            "prices": p_data,
            "features": f_data,
            "constraints": c_data,
            "planning": planning_list
        }
    
