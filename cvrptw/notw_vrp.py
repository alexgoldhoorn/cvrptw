from .time_vrp import TimeVRP
from .vrp_parameters import ModelType, VRPParameters


class NoTWVRP(TimeVRP):
    """
    Solve the CVRP (without time windows), with capacity limitations.
    It uses as input data: input_data_generator.py: create_data_model_from_orders()
    """

    def __init__(self, data, parameters: VRPParameters):
        super().__init__(data, parameters)
        self._transit_callback_index_cost = None

    @property
    def transit_callback_index_cost(self):
        return self._transit_callback_index_cost

    def _create_model(self):
        super()._create_model()

        cost_callback = self.create_callback("cost_matrix")
        self._transit_callback_index_cost = self.routing.RegisterTransitCallback(cost_callback)

        # Add number of items constraint.
        if "courier_item_capacities" in self.data:
            items_callback = self.create_callback_1d("number_of_items")
            items_callback_index = self.routing.RegisterUnaryTransitCallback(items_callback)
            self.routing.AddDimensionWithVehicleCapacity(
                items_callback_index,
                0,  # null capacity slack
                self.data["courier_item_capacities"],  # vehicle maximum capacities
                True,  # start cumul to zero
                "ItemCapacity",
            )
        else:
            print("Warning: no number of item constraints")

        # Add weight constraint.
        if "courier_weight_capacities" in self.data:
            weight_callback = self.create_callback_1d("weights")
            weight_callback_index = self.routing.RegisterUnaryTransitCallback(weight_callback)
            self.routing.AddDimensionWithVehicleCapacity(
                weight_callback_index,
                0,  # null capacity slack
                self.data["courier_weight_capacities"],  # vehicle maximum capacities
                True,  # start cumul to zero
                "WeightCapacity",
            )
        else:
            print("Warning: no weight constraints")

        if "on_the_way_bundles" in self.data:
            for bundle in self.data["on_the_way_bundles"]:
                order1_index = self.manager.NodeToIndex(bundle[0])
                for i in range(1, len(bundle)):
                    order2_index = self.manager.NodeToIndex(bundle[i])
                    self.routing.solver().Add(
                        self.routing.VehicleVar(order1_index)
                        == self.routing.VehicleVar(order2_index)
                    )

    @property
    def model_type(self) -> ModelType:
        return ModelType.no_tw
