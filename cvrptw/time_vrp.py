from .distance_vrp import DistanceVRP
from .vrp_parameters import ModelType, VRPParameters


class TimeVRP(DistanceVRP):
    """
    Solve the VRP minimizing travel time.
    It uses as input data: input_data_generator.py: create_data_model_from_orders()
    """

    def __init__(self, data, parameters: VRPParameters):
        super().__init__(data, parameters)
        self.transit_callback_index_time = None

    @property
    def transit_callback_index_cost(self):
        return self.transit_callback_index_time

    def _create_model(self):
        super()._create_model()

        # Create and register a transit callback for the time between 2 points
        time_callback = self.create_callback("time_matrix")
        self.transit_callback_index_time = self.routing.RegisterTransitCallback(time_callback)

        # Add Time dimension (used in planning when to do the orders, and to constraint
        #  on time windows).
        self.routing.AddDimension(
            self.transit_callback_index_time,
            self.parameters.allowed_waiting_time_at_del,  # allow waiting time
            self.parameters.max_time_duration,  # time for the day/week/..
            False,  # Don't force start cumul to zero.
            "Time",
        )

        # Add route duration constraint.
        self.routing.AddDimension(
            self.transit_callback_index_time,
            self.parameters.allowed_waiting_time_at_del,  # allow waiting time
            self.parameters.max_delivery_time,  # maximum time per vehicle
            False,  # Don't force start cumul to zero.
            "time_constraint",
        )

    @property
    def model_type(self) -> ModelType:
        return ModelType.time
