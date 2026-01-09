from optimiser_engine.domain import Client
from optimiser_engine.engine.service import OptimizerService

import json
import shutil
from pathlib import Path
from datetime import datetime, date, time, timedelta
import re
from typing import Dict, Tuple, Optional, List, Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
import pvlib
from optimiser_engine.engine.models.Exceptions import (
    ContextNotDefined,
    DimensionNotRespected,
    NotEnoughVariables,
    SolverFailed,
    WeatherNotValid,
)

BASE_DIR = Path(__file__).parent
PROFILES_DIR = BASE_DIR / "profils"
JOURNEE_MOYENNE_PATH = BASE_DIR / "Journee_moyenne.csv"
WEATHER_LILLE_PATH = BASE_DIR / "weather_lille.csv"

# Configuration par défaut
DEFAULT_SURFACE = 10.0
DEFAULT_EFFICIENCY = 0.18
DEFAULT_AZIMUTH = 180.0
DEFAULT_TILT = 30.0
DEFAULT_INITIAL_TEMP = 50.0
DEFAULT_HORIZON = 24
DEFAULT_STEP = 15

# Localisation par défaut (Lille) pour pvlib
LATITUDE = 50.62925
LONGITUDE = 3.057256


def ensure_profiles_dir() -> None:
    """S'assure que le dossier racine 'profils' existe."""
    PROFILES_DIR.mkdir(exist_ok=True)


def sanitize_pseudo(pseudo: str) -> str:
    """Nettoie le pseudo pour l'utiliser comme nom de dossier."""
    pseudo = pseudo.strip()
    pseudo = re.sub(r"[^A-Za-z0-9_-]+", "_", pseudo)
    pseudo = pseudo.strip("_")
    return pseudo or "profil_inconnu"


def load_profile_structure(pseudo: str) -> Tuple[Optional[str], Optional[Dict], Optional[pd.DataFrame], Optional[str]]:
    """
    Charge les données d'un profil dossier.
    Retourne: client_yaml_str, config_panels_dict, production_df, error_msg
    """
    profile_path = PROFILES_DIR / pseudo
    
    # Chemins attendus
    yaml_path = profile_path / "client.yaml"
    config_path = profile_path / "config_panels.json"
    prod_path = profile_path / "production.csv"

    if not profile_path.is_dir():
        return None, None, None, f"Le dossier du profil {pseudo} est introuvable."

    # Charger YAML
    try:
        client_yaml = yaml_path.read_text(encoding="utf-8")
    except Exception as e:
        return None, None, None, f"Erreur lecture client.yaml: {e}"

    # Charger Config Panels
    config_panels = {}
    try:
        if config_path.exists():
            config_panels = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        pass  # Ce n'est pas bloquant, on peut avoir des defaults

    # Charger Production CSV
    try:
        if prod_path.exists():
            production_df = pd.read_csv(prod_path)
            # Conversion date
            if "date" in production_df.columns:
                production_df["date"] = pd.to_datetime(production_df["date"])
                production_df = production_df.sort_values("date")
            else:
                 return None, None, None, "Le fichier production.csv n'a pas de colonne 'date'."
        else:
            return None, None, None, "Fichier production.csv manquant."
    except Exception as e:
        return None, None, None, f"Erreur lecture production.csv: {e}"

    return client_yaml, config_panels, production_df, None



def calculate_production_pvlib(
    surface: float, efficiency: float, azimuth: float, tilt: float
) -> Tuple[Optional[pd.DataFrame], Optional[Exception]]:
    """
    Calcule la production PV à partir de Journee_moyenne.csv en utilisant pvlib.
    Utilise une date d'été (15 Juin) pour correspondre à la durée d'ensoleillement du fichier moyen.
    """
    if not JOURNEE_MOYENNE_PATH.exists():
        return None, FileNotFoundError("Journee_moyenne.csv introuvable.")

    try:
        df_weather = pd.read_csv(JOURNEE_MOYENNE_PATH)
        
        # Standardisation des colonnes
        if "DateTime" not in df_weather.columns:
             cols = df_weather.columns
             if "date" in cols:
                 df_weather.rename(columns={"date": "DateTime"}, inplace=True)
             else:
                 df_weather.rename(columns={cols[0]: "DateTime"}, inplace=True)

        # 1. Parsing initial des dates (pour extraire l'heure)
        # On suppose que le fichier contient des dates arbitraires mais des heures valides.
        raw_times = pd.to_datetime(df_weather["DateTime"], errors="coerce", utc=True)
        
        # 2. Construction d'une série temporelle fictive sur le 15 Juin (Solstice d'été approx)
        # Ceci permet d'avoir une géométrie solaire cohérente avec des données de forte production (04h30 -> 19h30)
        base_date = date(2022, 6, 15) 
        
        # On recrée les timestamps en gardant l'heure du fichier original mais en forçant la date
        new_times = []
        for t in raw_times:
            if pd.notna(t):
                # t est un Timestamp (aware UTC si utc=True)
                # On convertit en datetime combine
                dt_new = datetime.combine(base_date, t.time())
                # On remet en UTC
                dt_new = dt_new.replace(tzinfo=t.tzinfo)
                new_times.append(dt_new)
            else:
                new_times.append(None)
                
        time_index = pd.DatetimeIndex(new_times)

        # Création Location
        location = pvlib.location.Location(LATITUDE, LONGITUDE, tz="UTC")

        # Position Solaire
        solpos = location.get_solarposition(time_index)

        # Extraction des composantes météo
        # IMPORTANT: Il faut aligner l'index avec celui de solpos (time_index) pour que pvlib fonctionne correctement
        dni = pd.to_numeric(df_weather.get("DNI", 0), errors='coerce').fillna(0)
        ghi = pd.to_numeric(df_weather.get("GHI", 0), errors='coerce').fillna(0)
        dhi = pd.to_numeric(df_weather.get("DHI", 0), errors='coerce').fillna(0)
        
        # Si c'est des Series, on assigne l'index
        if isinstance(dni, pd.Series): dni.index = time_index
        if isinstance(ghi, pd.Series): ghi.index = time_index
        if isinstance(dhi, pd.Series): dhi.index = time_index

        # Calcul POA (Plane of Array)
        # pvlib peut renvoyer des NaNs si le soleil est sous l'horizon, on fillna(0)
        poa_irradiance = pvlib.irradiance.get_total_irradiance(
            surface_tilt=tilt,
            surface_azimuth=azimuth,
            dni=dni,
            ghi=ghi,
            dhi=dhi,
            solar_zenith=solpos["apparent_zenith"],
            solar_azimuth=solpos["azimuth"]
        ).fillna(0)

        poa_global = poa_irradiance["poa_global"]
        
        # Production
        production_watts = poa_global * surface * efficiency
        
        result_df = pd.DataFrame({
            "date": time_index,
            "production": production_watts.clip(lower=0.0)
        })
        
        # Nettoyage final pour CSV (pas de NaNs)
        result_df["production"] = result_df["production"].fillna(0.0)
        
        return result_df, None

    except Exception as e:
        return None, e


def save_new_profile(
    pseudo: str, client_yaml: str, surface: float, efficiency: float, azimuth: float, tilt: float
) -> Tuple[bool, str, Optional[Dict]]:
    """
    Crée le dossier et sauvegarde les 3 fichiers.
    Retourne (Succès, Message, Metadata loaded)
    """
    slug = sanitize_pseudo(pseudo)
    profile_dir = PROFILES_DIR / slug
    
    if profile_dir.exists():
        return False, f"Le profil '{slug}' existe déjà.", None
    
    # 1. Calcul Production
    prod_df, prod_err = calculate_production_pvlib(surface, efficiency, azimuth, tilt)
    if prod_err is not None:
        return False, f"Erreur calcul PV: {prod_err}", None
    
    try:
        profile_dir.mkdir(parents=True)
        
        # 2. Config Panels
        config_data = {
            "surface": surface,
            "efficiency": efficiency,
            "azimuth": azimuth,
            "tilt": tilt
        }
        (profile_dir / "config_panels.json").write_text(json.dumps(config_data, indent=4), encoding="utf-8")
        
        # 3. Client YAML
        (profile_dir / "client.yaml").write_text(client_yaml, encoding="utf-8")
        
        # 4. Production CSV
        if prod_df is not None:
             prod_df.to_csv(profile_dir / "production.csv", index=False)
             
        # On prépare les données pour chargement immédiat
        loaded_data = {
            "pseudo": slug,
            "client_yaml": client_yaml,
            "config": config_data,
            "prod_df": prod_df
        }
        return True, f"Profil '{slug}' créé avec succès.", loaded_data
        
    except Exception as e:
        if profile_dir.exists():
            shutil.rmtree(profile_dir, ignore_errors=True)
        return False, f"Erreur système fichiers: {e}", None


def get_available_profiles() -> List[str]:
    """Liste les sous-dossiers dans profils"""
    if not PROFILES_DIR.exists():
        return []
    return sorted([d.name for d in PROFILES_DIR.iterdir() if d.is_dir()])


def display_exception_block(message: str, error: Exception) -> None:
    st.error(message)
    st.exception(error)
    st.stop()


def render_time_index(start: datetime, step_minutes: int, length: int) -> pd.DatetimeIndex:
    return pd.date_range(start=start, periods=length, freq=f"{int(step_minutes)}T")


def combine_date_and_time(d: date, t: time) -> datetime:
    return datetime.combine(d, t)


def main() -> None:
    st.set_page_config(page_title="Simulateur Optimasol", layout="wide")
    ensure_profiles_dir()
    
    session = st.session_state
    
    keys = [
        "simu_started", "client_obj", "profile_yaml", "df_production", 
        "traj", "start_datetime", "initial_temp", 
        "horizon_hours", "step_minutes", "loaded_pseudo",
        "panel_surface", "panel_eff", "panel_azimuth", "panel_tilt"
    ]
    for k in keys:
        if k not in session:
            session[k] = None
            
    if session["initial_temp"] is None: session["initial_temp"] = DEFAULT_INITIAL_TEMP
    if session["horizon_hours"] is None: session["horizon_hours"] = DEFAULT_HORIZON
    if session["step_minutes"] is None: session["step_minutes"] = DEFAULT_STEP
    
    if session["panel_surface"] is None: session["panel_surface"] = DEFAULT_SURFACE
    if session["panel_eff"] is None: session["panel_eff"] = DEFAULT_EFFICIENCY
    if session["panel_azimuth"] is None: session["panel_azimuth"] = DEFAULT_AZIMUTH
    if session["panel_tilt"] is None: session["panel_tilt"] = DEFAULT_TILT

    st.title("Simulateur du moteur d'optimisation (Version Profils Dossiers)")

    # Message d'accueil / Bouton Start
    if not session["simu_started"]:
        if st.button("Démarrer la simulation", type="primary"):
            session["simu_started"] = True
            st.rerun()
        else:
            st.info("Cliquez sur Démarrer pour commencer.")
            return

    # -------------------------------------------------------------
    # SECTION 1 : GESTION DES PROFILS
    # -------------------------------------------------------------
    st.header("Gestion du Profil Client")
    
    tab_select, tab_create = st.tabs(["Charger un profil existant", "Créer un nouveau profil"])
    
    # --- ONGLE CHARGEMENT ---
    with tab_select:
        existing_profiles = get_available_profiles()
        if not existing_profiles:
            st.warning("Aucun profil trouvé. Veuillez en créer un.")
        else:
            # Astuce pour pré-selectionner le loaded
            try:
                idx = existing_profiles.index(session["loaded_pseudo"]) if session["loaded_pseudo"] in existing_profiles else 0
            except:
                idx = 0
                
            selected_pseudo = st.selectbox("Choisir un profil", [""] + existing_profiles, index=idx+1 if session["loaded_pseudo"] else 0)
            
            # Bouton charger (Uniquement si changement ou force refresh)
            if st.button("Charger ce profil", disabled=not selected_pseudo):
                yaml_str, config_panels, prod_df, err = load_profile_structure(selected_pseudo)
                
                if err:
                    st.error(err)
                else:
                    try:
                        client_obj = Client.from_yaml(yaml_str)
                    except Exception as exe:
                        st.error(f"Erreur parsing YAML client: {exe}")
                        client_obj = None

                    if client_obj:
                        session["traj"] = None
                        session["client_obj"] = client_obj
                        session["profile_yaml"] = yaml_str
                        session["df_production"] = prod_df
                        session["loaded_pseudo"] = selected_pseudo
                        
                        if config_panels:
                            session["panel_surface"] = config_panels.get("surface", DEFAULT_SURFACE)
                            session["panel_eff"] = config_panels.get("efficiency", DEFAULT_EFFICIENCY)
                            session["panel_azimuth"] = config_panels.get("azimuth", DEFAULT_AZIMUTH)
                            session["panel_tilt"] = config_panels.get("tilt", DEFAULT_TILT)
                        
                        st.success(f"Profil '{selected_pseudo}' chargé avec succès !")
    
    # --- ONGLE CREATION ---
    with tab_create:
        st.subheader("Configuration du Client (YAML)")
        
        default_yaml_content = session["profile_yaml"] if session["profile_yaml"] else ""
        yaml_input = st.text_area("YAML Client", value=default_yaml_content, height=300)
        
        st.subheader("Configuration des Panneaux")
        c1, c2 = st.columns(2)
        new_surface = c1.number_input("Surface (m²)", value=float(DEFAULT_SURFACE), min_value=0.0)
        new_eff = c2.number_input("Rendement (0-1)", value=float(DEFAULT_EFFICIENCY), min_value=0.0, max_value=1.0)
        new_azimuth = c1.number_input("Azimuth (°)", value=float(DEFAULT_AZIMUTH))
        new_tilt = c2.number_input("Tilt/Inclinaison (°)", value=float(DEFAULT_TILT))
        
        new_pseudo = st.text_input("Nom du nouveau profil (Pseudo)")
        
        if st.button("Sauvegarder et Calculer Production"):
            if not new_pseudo:
                st.error("Pseudo requis.")
            else:
                try:
                    client_test = Client.from_yaml(yaml_input)
                except Exception as e:
                    st.error(f"Le YAML est invalide : {e}")
                    client_test = None
                
                if client_test:
                    success, msg, loaded_data = save_new_profile(
                        new_pseudo, yaml_input, new_surface, new_eff, new_azimuth, new_tilt
                    )
                    if success:
                        st.success(msg)
                        # Chargement automatique
                        session["traj"] = None
                        session["client_obj"] = client_test
                        session["profile_yaml"] = loaded_data["client_yaml"]
                        session["df_production"] = loaded_data["prod_df"]
                        session["loaded_pseudo"] = loaded_data["pseudo"]
                        # Config
                        cfg = loaded_data["config"]
                        session["panel_surface"] = cfg["surface"]
                        session["panel_eff"] = cfg["efficiency"]
                        session["panel_azimuth"] = cfg["azimuth"]
                        session["panel_tilt"] = cfg["tilt"]
                        
                        st.rerun()
                    else:
                        st.error(msg)

    # Indicateur d'état
    if session["loaded_pseudo"]:
        st.info(f"Profil Actif : {session['loaded_pseudo']}")
        with st.expander("Voir/Modifier la config panneaux chargée (Impact visuel seulement)"):
            st.write(f"Surface: {session['panel_surface']} m² | Rendement: {session['panel_eff']}")
    else:
        st.warning("Aucun profil chargé. Veuillez charger ou créer un profil pour continuer.")
        # ON ARRETE L'EXECUTION ICI POUR NE PAS AFFICHER LE RESTE
        return 
    
    # -------------------------------------------------------------
    # SECTION 2 : CONTEXTE ET SIMULATION
    # -------------------------------------------------------------

    st.header("Contexte & Simulation")

    # Date de début
    # On propose par défaut le début de la prod chargée si dispo, sinon now
    def_date = datetime.now()
    if session["df_production"] is not None and not session["df_production"].empty:
        # On essaie de prendre le premier timestamp du CSV de prod
        try:
            first_ts = session["df_production"]["date"].iloc[0]
            if isinstance(first_ts, pd.Timestamp):
                def_date = first_ts.to_pydatetime()
        except:
            pass
            
    c_d, c_h = st.columns(2)
    s_date = c_d.date_input("Date début", value=def_date.date())
    s_time = c_h.time_input("Heure début", value=def_date.time())
    start_dt = combine_date_and_time(s_date, s_time)
    session["start_datetime"] = start_dt
    
    session["initial_temp"] = st.number_input("Température Initiale (°C)", value=float(session["initial_temp"]))
    
    with st.expander("Paramètres Avancés (Horizon)"):
        session["horizon_hours"] = st.number_input("Horizon (h)", value=int(session["horizon_hours"]))
        session["step_minutes"] = st.number_input("Pas (min)", value=int(session["step_minutes"]))

    if st.button("Lancer la simulation"):
        if session["client_obj"] is None:
            st.error("Objet Client manquant.")
        elif session["df_production"] is None or session["df_production"].empty:
            st.error("Production PV manquante.")
        else:
            # Préparation service
            try:
                service = OptimizerService(
                    horizon_hours=int(session["horizon_hours"]), 
                    step_minutes=int(session["step_minutes"])
                )
                
                prod_check = session["df_production"].set_index("date")
                end_dt = start_dt + timedelta(hours=session["horizon_hours"])
                
                # Check coverage simple (timezone naive vs aware ? attentions aux mix)
                # On convertit tout en tz-naive pour simplifier la comparaison
                p_start = prod_check.index.min().tz_localize(None)
                p_end = prod_check.index.max().tz_localize(None)
                req_start = start_dt.replace(tzinfo=None)
                req_end = end_dt.replace(tzinfo=None)
                
                if req_start < p_start or req_end > p_end:
                    st.warning(
                        f"Attention : La période demandée ({req_start} -> {req_end}) "
                        f"n'est pas totalement couverte par le fichier de production ({p_start} -> {p_end}). "
                        "Risque d'erreur moteur."
                    )
                
                # Injection dans le moteur
                # Ensure production index is datetime
                prod_check.index = pd.to_datetime(prod_check.index)
                
                traj = service.trajectory_of_client(
                    session["client_obj"],
                    session["start_datetime"],
                    float(session["initial_temp"]),
                    prod_check # Pass the dataframe with Date index
                )
                session["traj"] = traj
                st.success("Simulation terminée avec succès !")
                
            except Exception as e:
                display_exception_block("Erreur lors de la simulation", e)

    # -------------------------------------------------------------
    # SECTION 3 : RÉSULTATS
    # -------------------------------------------------------------
    if session.get("traj"):
        show_results(session)


def show_results(session):
    traj = session["traj"]
    st.markdown("---")
    st.header("Résultats")
    
    # Axe temporel
    try:
        time_axis = render_time_index(session["start_datetime"], int(session["step_minutes"]), traj.context.N)
    except:
        st.error("Erreur construction axe temporel")
        return

    # 1. Décisions
    st.subheader("Décisions de Pilotage (x)")
    x = traj.x
    vect = traj.context.availability_on
    if x is not None:
        fig, ax = plt.subplots(figsize=(10, 3))
        ax.plot(time_axis[:len(x)], np.array(x)*100, label="x (%)")
        
        # Zones interdites
        if vect:
            vect_arr = np.array(vect).flatten()
            for i, allowed in enumerate(vect_arr[:len(x)]):
                if allowed == 0:
                     if i < len(time_axis)-1:
                        ax.axvspan(time_axis[i], time_axis[i+1], color="red", alpha=0.1)
        
        ax.set_ylabel("% Activation")
        ax.legend()
        st.pyplot(fig)

    # 2. Températures
    st.subheader("Températures")
    temps = traj.get_temperatures()
    if temps is not None:
        fig, ax = plt.subplots(figsize=(10, 3))
        # Ajustement longueur
        t_ax = time_axis if len(time_axis) == len(temps) else time_axis[:len(temps)]
        ax.plot(t_ax, temps, label="Température Eau")
        
        # Min Temp Constraint
        try:
             min_t = session["client_obj"].constraints.minimum_temperature
             ax.axhline(min_t, color="red", linestyle="--", label="Min Temp")
        except:
            pass
            
        ax.legend()
        st.pyplot(fig)

    # 3. Flux
    st.subheader("Bilan Énergétique")
    exports = traj.get_exports()
    imports = traj.get_imports()
    solar = traj.context.solar_production
    
    if exports is not None:
        fig, ax = plt.subplots(figsize=(10, 3))
        common_len = min(len(exports), len(time_axis))
        ax.plot(time_axis[:common_len], np.array(exports).flatten()[:common_len], label="Export")
        ax.plot(time_axis[:common_len], np.array(imports).flatten()[:common_len], label="Import")
        if solar is not None:
            ax.plot(time_axis[:common_len], np.array(solar).flatten()[:common_len], label="Solaire", callback=None)
            
        ax.legend()
        st.pyplot(fig)

    # 4. KPI
    st.subheader("KPIs")
    try:
        cost = traj.compute_cost()
        self_cons = traj.compute_self_consumption()
        st.metric("Coût (€)", f"{cost:.2f}")
        st.metric("Autoconsommation", f"{self_cons:.2%}")
    except:
        st.warning("Calcul KPI impossible")

if __name__ == "__main__":
    main()
