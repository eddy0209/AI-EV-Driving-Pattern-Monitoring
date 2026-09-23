from dataclasses import dataclass
from pathlib import Path
import joblib
import pandas as pd


FEATURE_NAMES = [
    "Battery_Nominal_V",
    "Battery_Capacity_Ah",
    "Battery_Energy_Wh",
    "SOC_pct",
    "SOH_pct",
    "Battery_Temperature_C",
    "Motor_Rated_Power_kW",
    "Motor_Efficiency_pct",
    "Total_Mass_kg",
    "Vehicle_Speed_kmh",
    "Acceleration_mps2",
    "Throttle_pct",
    "Road_Gradient_pct",
    "Regen_Efficiency_pct",
]


@dataclass
class MLPrediction:
    predicted_wh_per_km: float
    raw_prediction_wh_per_km: float
    features: dict


class EVEnergyMLModel:
    def __init__(self, model_path=None):
        if model_path is None:
            model_path = (
                Path(__file__).resolve().parent
                / "ev_energy_consumption_model.joblib"
            )

        self.model_path = Path(model_path)
        self.model = None
        self.loaded = False

        self.load_model()

    def load_model(self):
        """Load the trained Random Forest model."""
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"ML model not found: {self.model_path}"
            )

        self.model = joblib.load(self.model_path)
        self.loaded = True

    @staticmethod
    def build_features(
        battery_nominal_v,
        battery_capacity_ah,
        soc_pct,
        soh_pct,
        battery_temperature_c,
        motor_rated_power_kw,
        motor_efficiency_pct,
        total_mass_kg,
        vehicle_speed_kmh,
        acceleration_mps2,
        throttle_pct,
        road_gradient_pct,
        regen_efficiency_pct,
    ):
        """Build the exact 14-feature input used by the trained model."""

        battery_energy_wh = (
            float(battery_nominal_v)
            * float(battery_capacity_ah)
        )

        features = {
            "Battery_Nominal_V": float(battery_nominal_v),
            "Battery_Capacity_Ah": float(battery_capacity_ah),
            "Battery_Energy_Wh": battery_energy_wh,
            "SOC_pct": float(soc_pct),
            "SOH_pct": float(soh_pct),
            "Battery_Temperature_C": float(battery_temperature_c),
            "Motor_Rated_Power_kW": float(motor_rated_power_kw),
            "Motor_Efficiency_pct": float(motor_efficiency_pct),
            "Total_Mass_kg": float(total_mass_kg),
            "Vehicle_Speed_kmh": float(vehicle_speed_kmh),
            "Acceleration_mps2": float(acceleration_mps2),
            "Throttle_pct": float(throttle_pct),
            "Road_Gradient_pct": float(road_gradient_pct),
            "Regen_Efficiency_pct": float(regen_efficiency_pct),
        }

        return features

    def predict(
        self,
        battery_nominal_v,
        battery_capacity_ah,
        soc_pct,
        soh_pct,
        battery_temperature_c,
        motor_rated_power_kw,
        motor_efficiency_pct,
        total_mass_kg,
        vehicle_speed_kmh,
        acceleration_mps2,
        throttle_pct,
        road_gradient_pct,
        regen_efficiency_pct,
    ):
        """
        Predict current energy consumption in Wh/km.

        Returns an MLPrediction object.
        """

        if not self.loaded or self.model is None:
            raise RuntimeError("ML model is not loaded.")

        features = self.build_features(
            battery_nominal_v=battery_nominal_v,
            battery_capacity_ah=battery_capacity_ah,
            soc_pct=soc_pct,
            soh_pct=soh_pct,
            battery_temperature_c=battery_temperature_c,
            motor_rated_power_kw=motor_rated_power_kw,
            motor_efficiency_pct=motor_efficiency_pct,
            total_mass_kg=total_mass_kg,
            vehicle_speed_kmh=vehicle_speed_kmh,
            acceleration_mps2=acceleration_mps2,
            throttle_pct=throttle_pct,
            road_gradient_pct=road_gradient_pct,
            regen_efficiency_pct=regen_efficiency_pct,
        )

        # DataFrame preserves the exact feature names/order expected by
        # the trained model.
        model_input = pd.DataFrame(
            [features],
            columns=FEATURE_NAMES,
        )

        raw_prediction = float(
            self.model.predict(model_input)[0]
        )

        # Energy consumption cannot be negative.
        predicted_wh_per_km = max(1.0, raw_prediction)

        return MLPrediction(
            predicted_wh_per_km=predicted_wh_per_km,
            raw_prediction_wh_per_km=raw_prediction,
            features=features,
        )


if __name__ == "__main__":
    # Standalone test using the model file placed beside this module.
    print("=== ML MODEL TEST ===")

    model = EVEnergyMLModel()

    result = model.predict(
        battery_nominal_v=48,
        battery_capacity_ah=85,
        soc_pct=70,
        soh_pct=95,
        battery_temperature_c=30,
        motor_rated_power_kw=5,
        motor_efficiency_pct=90,
        total_mass_kg=500,
        vehicle_speed_kmh=40,
        acceleration_mps2=0.5,
        throttle_pct=50,
        road_gradient_pct=0,
        regen_efficiency_pct=70,
    )

    print(
        f"Predicted energy consumption: "
        f"{result.predicted_wh_per_km:.2f} Wh/km"
    )

    print("Features supplied to model:")
    for name, value in result.features.items():
        print(f"  {name}: {value}")