from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from .scheduled_vrp import ScheduledVRP
from .vrp_parameters import ModelType, VRPParameters


class LiveVRP(ScheduledVRP):
    """
    Solve the CVRP with time windows on both the pickup and delivery location,
    and capacity limitations.

    It extends the ScheduledVRP by adding time windows on the pickup location.

    It uses as input data: input_data_generator.py: create_data_pu_del_model_from_orders()
    """

    def __init__(self, data, parameters: VRPParameters):
        super().__init__(data, parameters)

    def _create_model(self):
        super()._create_model()

        # Define Transportation Requests.
        for request in self.data["pickups_deliveries"]:
            pickup_index = self.manager.NodeToIndex(request[0])
            delivery_index = self.manager.NodeToIndex(request[1])
            self.routing.AddPickupAndDelivery(pickup_index, delivery_index)
            self.routing.solver().Add(
                self.routing.VehicleVar(pickup_index) == self.routing.VehicleVar(delivery_index)
            )

    def get_search_parameters(self):
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
        )
        return search_parameters

    @property
    def model_type(self) -> ModelType:
        return ModelType.live
