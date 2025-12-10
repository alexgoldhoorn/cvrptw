import time
from typing import List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from .distance import coord_distance


def quick_vrp_from_df(df: pd.DataFrame, max_calc_time: Optional[int] = None, verbose: bool = False):
    """
    Solve the VRP based on distances only.
    It assumes the locations are coordinates.
    """
    pickup_location = df[["pickup_lat", "pickup_lon"]].values
    pickup_location_unique = np.unique(pickup_location, axis=0)
    if len(pickup_location_unique) == 1:
        pickup_location = pickup_location_unique[0]
        if verbose:
            print("Single pickup location:", pickup_location)
    elif verbose:
        print("Multiple pickup locations")
    order_locations = df[["delivery_lat", "delivery_lon"]].values
    quick_vrp = QuickVRP(
        start_location=pickup_location,
        visit_locations=order_locations,
        dist_func=coord_distance,
        extra_cost_per_visit=0.0,
        max_calc_time=max_calc_time,
        verbose=verbose,
    )

    solution = quick_vrp.solve()

    if verbose:
        print("Solution:")
        for i, route in enumerate(solution["routes"]):
            print(f" ROUTE {i}:", route)
            print(" locs:", order_locations[route])
            print(df.iloc[route])

        print("Cost:", solution["total_cost"])

    return solution


class QuickVRP:
    """Simple VRP solver using a start location, several order locations.
    Parameters:
        start_location: (lat, lon) of the start location (or list)
        visit_locations: list of (lat, lon) of the order locations
        dist_func: function to calculate the distance between 2 locations
        extra_cost_per_visit: extra cost per visit (e.g. time to deliver)
        max_calc_time: maximum time to calculate the solution (in seconds)
    """

    def __init__(
        self,
        start_location: Union[Tuple[float, float], List[Tuple[float, float]]],
        visit_locations: List[Tuple[float, float]],
        dist_func,
        extra_cost_per_visit: float = 0.0,
        max_calc_time: Optional[int] = None,
        verbose: bool = False,
    ):
        self.start_location = start_location
        self.visit_locations = visit_locations
        self.dist_func = dist_func
        self.extra_cost_per_visit = extra_cost_per_visit
        self.max_calc_time = max_calc_time
        self.verbose = verbose
        self.manager = None
        self.routing = None
        self.start_location_index: Optional[List[int]] = None

        assert not self.is_multi_pickup or len(self.start_location) == len(self.visit_locations), (
            f"start_location and visit_locations should have the same length, "
            f"but got {len(self.start_location)} and {len(self.visit_locations)}"
        )

        if self.is_multi_pickup:
            self.start_location_index = []
            unique_locations = np.unique(self.start_location, axis=0)
            for start_location in self.start_location:
                index = np.where(unique_locations == start_location)[0][0]
                self.start_location_index.append(index)

            print("start loc", self.start_location)
            print("unique", unique_locations)
            print("index", self.start_location_index)
            self.start_location = unique_locations

    @property
    def n_items(self):
        return len(self.visit_locations) + self.n_start_locations

    @property
    def n_start_locations(self):
        return len(self.start_location) if self.is_multi_pickup else 1

    @property
    def n_locations(self):
        return len(self.visit_locations)

    @property
    def num_vehicles(self):
        return len(self.visit_locations)

    @property
    def is_multi_pickup(self):
        if self.start_location_index is not None:
            return True
        # else, maybe not yet initialized
        start_loc_type = type(self.start_location[0])
        return start_loc_type is list or start_loc_type is tuple or start_loc_type is np.ndarray

    def cost_matrix(self):
        cost_mat = np.zeros((self.n_items, self.n_items))
        n_start_locations = self.n_start_locations
        for i in range(self.n_items):
            for j in range(self.n_items):
                if i == j:
                    continue
                if i < n_start_locations:
                    if n_start_locations == 1:
                        cost_mat[i, j] = self.dist_func(
                            self.start_location, self.visit_locations[j - 1]
                        )
                    else:
                        cost_mat[i, j] = self.dist_func(
                            self.start_location[i], self.visit_locations[j - n_start_locations]
                        )
                elif j < n_start_locations:
                    # don't count going back
                    cost_mat[i, j] = 0
                else:
                    cost_mat[i, j] = (
                        self.dist_func(
                            self.visit_locations[i - n_start_locations],
                            self.visit_locations[j - n_start_locations],
                        )
                        + self.extra_cost_per_visit
                    )
        return cost_mat

    def process_solution(self, solution) -> dict:
        if solution is None:
            return {"routes": [], "total_cost": 0}

        routes = []
        total_route_cost = 0
        for vehicle_id in range(self.num_vehicles):
            index = self.routing.Start(vehicle_id)
            route = []
            while not self.routing.IsEnd(index):
                node_index = self.manager.IndexToNode(index)
                if node_index > 0:
                    route.append(node_index - 1)
                previous_index = index
                index = solution.Value(self.routing.NextVar(index))
                route_cost = self.routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
                total_route_cost += route_cost

            node_index = self.manager.IndexToNode(index)
            assert node_index == 0
            # route.append(node_index)
            if len(route) > 0:
                routes.append(route)

        return {"routes": routes, "total_cost": total_route_cost}

    def solve(self) -> dict:
        cost_mat = self.cost_matrix()
        if self.verbose:
            print("Cost matrix:", cost_mat)
        self.manager = pywrapcp.RoutingIndexManager(len(cost_mat), self.num_vehicles, 0)
        self.routing = pywrapcp.RoutingModel(self.manager)

        def cost_callback(from_index, to_index):
            from_node = self.manager.IndexToNode(from_index)
            to_node = self.manager.IndexToNode(to_index)
            return cost_mat[from_node][to_node]

        transit_callback_index = self.routing.RegisterTransitCallback(cost_callback)
        self.routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        if self.is_multi_pickup:
            pass
            # n_start_locations = self.n_start_locations
            # for i in range(self.n_locations):
            #    pickup_index = self.manager.NodeToIndex(self.start_location_index[i])
            #    delivery_index = self.manager.NodeToIndex(i + n_start_locations)
            #    self.routing.AddPickupAndDelivery(pickup_index, delivery_index)
            #    self.routing.solver().Add(
            #        self.routing.VehicleVar(pickup_index)
            #        == self.routing.VehicleVar(delivery_index)
            #    )

        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        if self.max_calc_time is not None:
            search_parameters.time_limit.seconds = self.max_calc_time

        if self.verbose:
            print("Solving...")
            t = time.time()
        solution = self.routing.SolveWithParameters(search_parameters)
        if self.verbose:
            print("Solved in", time.time() - t, "seconds")

        return self.process_solution(solution)
