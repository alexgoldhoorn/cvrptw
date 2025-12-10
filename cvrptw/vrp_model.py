""" A model for the VRP """

import abc
import time

from ortools.constraint_solver import pywrapcp

from .vrp_parameters import VRPParameters, ModelType
from .process_solution import process_solution_data

# status: https://developers.google.com/optimization/routing/routing_options#search-status
SOLVER_STATUS = [
    "0-not solved",
    "1-success",
    "2-no solution found",
    "3-time-out without solution",
    "4-invalid model",
    "exception",
]


def make_routing_monitor(
    routing_model: pywrapcp.RoutingModel, failure_limit: int
) -> callable:
    class RoutingMonitor:
        def __init__(self, model: pywrapcp.RoutingModel):
            inf = 99999999999
            self.model = model
            self._counter = 0
            self._index = 0
            self._best_objective = inf
            self._counter_limit = failure_limit

        def __call__(self):
            objective = self.model.CostVar().Max()
            if objective < self._best_objective:
                improve_str = "+"
            elif objective > self._best_objective:
                improve_str = "-"
            else:
                improve_str = "="

            self._best_objective = min(self._best_objective, objective)

            print(
                f"[{self._index}|c{self._counter}] ({improve_str}) "
                f"value = {objective} [best = {self._best_objective}]"
            )
            if self._best_objective == self.model.CostVar().Max():
                self._counter = 0
            else:
                self._counter += 1
                if self._counter > self._counter_limit:
                    print(" FINISH current search")
                    self.model.solver().FinishCurrentSearch()

            self._index += 1

    return RoutingMonitor(routing_model)


class VRPModel(abc.ABC):
    """The abstract VRP model that generates the OR-tools model."""

    def __init__(self, data, parameters: VRPParameters):
        self.data = data
        self.routing = None
        self.manager = None
        self.data = data
        self.parameters = parameters

    @property
    def n_nodes(self) -> int:
        """Number of nodes in the VPR problem. Can be more than the number of orders."""
        return len(self.data["time_matrix"])

    @property
    def n_orders(self) -> int:
        """The number of orders."""
        return self.data["meta"]["n_orders"]

    def create_routing_manager(self, track_solver_progress=True):
        """Create the routing index manager."""
        assert len(self.data["time_matrix"]) == len(self.data["distance_matrix"])
        assert self.routing is None
        assert self.manager is None

        self.manager = pywrapcp.RoutingIndexManager(
            len(self.data["time_matrix"]), self.data["num_vehicles"], self.data["depot"]
        )

        # Create Routing Model.
        self.routing = pywrapcp.RoutingModel(self.manager)

        # add callback to track the solutions found by the solver
        if self.parameters.track_solver_progress:
            routing_monitor = make_routing_monitor(self.routing, 10)
            self.routing.AddAtSolutionCallback(routing_monitor)

    def create_callback(self, data_field: str):
        """Create a callback function for the solver."""
        assert data_field in self.data
        return lambda from_index, to_index: self.data[data_field][
            self.manager.IndexToNode(from_index)
        ][self.manager.IndexToNode(to_index)]

    def create_callback_1d(self, data_field: str):
        """Create a callback function for the solver with 1 dimension."""
        assert data_field in self.data
        return lambda index: self.data[data_field][self.manager.IndexToNode(index)]

    @property
    @abc.abstractmethod
    def transit_callback_index_cost(self):
        pass

    def create_model(self):
        self.create_routing_manager()
        self._create_model()
        # Define cost of each arc.
        self.routing.SetArcCostEvaluatorOfAllVehicles(self.transit_callback_index_cost)

    @abc.abstractmethod
    def _create_model(self):
        pass

    @abc.abstractmethod
    def get_search_parameters(self):
        pass

    @property
    @abc.abstractmethod
    def model_type(self) -> ModelType:
        pass

    @property
    def model_name(self):
        return self.model_type.name

    def solve(self):
        if len(self.data["distance_matrix"]) <= 1:
            return {
                "solver": {
                    "model": self.model_name,
                    "status": "no data",
                    "error": "no data",
                }
            }
        self.create_model()

        search_parameters = self.get_search_parameters()
        if self.parameters.max_calc_time:
            search_parameters.time_limit.seconds = self.parameters.max_calc_time

        # Solve the problem.
        print("Solving ...")
        t = time.time()
        try:
            solution = self.routing.SolveWithParameters(search_parameters)
            solver_status = self.routing.status()
        except Exception as e:
            print("Error while running solver:", e)
            solution = None
            solver_status = 5

        duration = time.time() - t

        # Print solution on console.
        if solution:
            result = process_solution_data(solution, self)
        else:
            result = {}

        result["solver"] = {
            "model": self.model_name,
            "duration": duration,
            "status_code": solver_status,
            "status": SOLVER_STATUS[solver_status],
        }

        print("---solver stats----")
        print("Status:  ", result["solver"]["status"])
        print(f"Duration: {duration:.2f} s")

        return result
