from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from .notw_vrp import NoTWVRP
from .vrp_parameters import ModelType, VRPParameters


class ScheduledVRP(NoTWVRP):
    """
    Solve the CVRP with time windows, and capacity limitations.
    It uses as input data: input_data_generator.py: create_data_model_from_orders()
    """

    def __init__(self, data, parameters: VRPParameters):
        super().__init__(data, parameters)

    def _create_model(self):
        super()._create_model()

        time_dimension = self.routing.GetDimensionOrDie("Time")
        # Instantiate route start and end times to produce feasible times.
        for i in range(self.data["num_vehicles"]):
            self.routing.AddVariableMinimizedByFinalizer(
                time_dimension.CumulVar(self.routing.Start(i))
            )
            self.routing.AddVariableMinimizedByFinalizer(
                time_dimension.CumulVar(self.routing.End(i))
            )

        # Add time window constraints for each location except depot.
        for location_idx, time_window in enumerate(self.data["time_windows"]):
            if location_idx == self.data["depot"]:
                continue
            index = self.manager.NodeToIndex(location_idx)
            time_dimension.CumulVar(index).SetRange(int(time_window[0]), int(time_window[1]))

    def get_search_parameters(self):
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        return search_parameters

    @property
    def model_type(self) -> ModelType:
        return ModelType.scheduled
