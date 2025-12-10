from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from .vrp_model import VRPModel
from .vrp_parameters import ModelType, VRPParameters


class DistanceVRP(VRPModel):
    """
    Solve the VRP based on distances only.
    It uses as input data: input_data_generator.py: create_data_model_from_orders()
    """

    def __init__(self, data, parameters: VRPParameters):
        super().__init__(data, parameters)
        self.transit_callback_index_dist = None

    @property
    def transit_callback_index_cost(self):
        return self.transit_callback_index_dist

    def _create_model(self):
        # Create and register a transit callback for the distance between 2 points
        dist_callback = self.create_callback("distance_matrix")
        self.transit_callback_index_dist = self.routing.RegisterTransitCallback(dist_callback)

        # Add route distance constraint.
        if self.parameters.max_delivery_distance is not None:
            self.routing.AddDimension(
                self.transit_callback_index_dist,
                0,  # no slack
                self.parameters.max_delivery_distance,  # maximum distance per vehicle
                False,  # Don't force start cumul to zero.
                "distance_contraint",
            )

    def get_search_parameters(self):
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.AUTOMATIC
        )
        return search_parameters

    @property
    def model_type(self) -> ModelType:
        return ModelType.distance
