from dataclasses import dataclass
from enum import Enum
import json
from typing import Dict, List, Optional

ModelType = Enum("ModelType", "scheduled live no_tw time distance quick")
Vehicle = Enum("Vehicle", "BICYCLE MOTORBIKE CAR")


class ConfigError(Exception):
    pass


@dataclass
class VehicleConstraintParameters:
    number_of_items: int = 1
    weight: int = 1

    def passes_constraints(self, values: "VehicleConstraintParameters") -> bool:
        return (
            values.number_of_items <= self.number_of_items
            and values.weight <= self.weight
        )


class ConstraintsParameters:
    def __init__(self, constraint_data: Dict[Vehicle, VehicleConstraintParameters]):
        self._constraint_data = constraint_data

    def __getitem__(self, item):
        if type(item) is str:
            return self._constraint_data[Vehicle[item]]
        return self._constraint_data[item]

    def get_vehicles_for_item(
        self, item_values: VehicleConstraintParameters
    ) -> List[str]:
        pass_constraints = []
        for vehicle, constraints in self._constraint_data.items():
            if constraints.passes_constraints(item_values):
                pass_constraints.append(vehicle.name)
        return pass_constraints

    def to_dict(self):
        data_dict = dict()
        for vehicle, constraints in self._constraint_data.items():
            data_dict[vehicle.name] = constraints.__dict__.copy()
        return data_dict

    @classmethod
    def create(cls, data: dict) -> "ConstraintsParameters":
        constraint_dict = dict()
        for vehicle, constraint_data in data.items():
            vehicle_type = Vehicle[vehicle]
            if vehicle_type in constraint_dict:
                raise ConfigError(f"{vehicle} has more items in the constraints")
            constraint_dict[vehicle_type] = VehicleConstraintParameters(
                **constraint_data
            )
        return cls(constraint_dict)


@dataclass
class VRPParameters:
    """All the parameters used in the multibundling problem."""

    model_type: ModelType
    max_time_duration: int = 3600 * 24
    allowed_waiting_time_at_del: int = 60 * 10
    max_delivery_time: int = 60 * 60
    max_delivery_distance: int = 5000
    waiting_time_at_delivery: int = 60
    speed: int = 3
    courier_item_capacity: int = 5
    courier_weight_capacity: int = 5
    courier_cost: int = 5000
    # Meta parameters
    max_calc_time: int = 10
    track_solver_progress: bool = False
    vehicle_constraints: Optional[ConstraintsParameters] = None
    filter_infeasible_orders: bool = True
    multi_pickup: bool = False


    def to_dict(self):
        dict_data = self.__dict__.copy()
        dict_data["model_type"] = self.model_type.name
        if self.vehicle_constraints is not None:
            dict_data["vehicle_constraints"] = self.vehicle_constraints.to_dict()
        return dict_data

    @classmethod
    def create(cls, data_input: dict):
        data = data_input.copy()
        if "model_type" in data:
            data["model_type"] = ModelType[data_input["model_type"]]
        if "vehicle_constraints" in data:
            data["vehicle_constraints"] = ConstraintsParameters.create(
                data["vehicle_constraints"]
            )
        return cls(**data)

    @classmethod
    def create_from_file(cls, file: str):
        with open(file, "r") as f:
            data = json.load(f)

        return VRPParameters.create(data)

    def to_str(self):
        return json.dumps(self.to_dict(), indent=4)
