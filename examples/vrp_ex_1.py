#!/usr/bin/env python3
# Copyright 2010-2022 Google LLC
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START program]
"""Simple Vehicles Routing Problem (VRP).

   This is a sample using the routing library python wrapper to solve a VRP
   problem.
   A description of the problem can be found here:
   http://en.wikipedia.org/wiki/Vehicle_routing_problem.

   Distances are in meters.
"""

# [START import]
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import numpy as np


# [END import]


# [START data_model]
def create_data_model():
    """Stores the data for the problem."""
    data = {}
    data["distance_matrix"] = np.array(
        [
            [0, 0, 0, 1499, 2295],
            [0, 0, 0, 1499, 2295],
            [0, 0, 0, 1499, 2295],
            [0, 1499, 1499, 0, 852],
            [0, 2295, 2295, 852, 0]]
    )
    data["time_matrix"] = np.array([
        [0, 0, 0, 559, 825],
        [0, 0, 0, 559, 825],
        [0, 0, 0, 559, 825],
        [0, 559, 559, 0, 344],
        [0, 825, 825, 344, 0]
    ]
    )
    # kdata["cost_matrix"] = data["distance_matrix"]
    data["num_vehicles"] = 4
    data["depot"] = 0
    return data
    # [END data_model]


# [START solution_printer]
def print_solution(data, manager, routing, solution):
    """Prints solution on console."""
    print(f"Objective: {solution.ObjectiveValue()}")
    total_distance = 0
    routes = []
    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        plan_output = "Route for vehicle {}:\n".format(vehicle_id)
        route_distance = 0
        route = []
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            route.append(node_index)
            plan_output += " {} ->".format(node_index)
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id
            )

        node_index = manager.IndexToNode(index)
        route.append(node_index)
        plan_output += " {}\n".format(node_index)
        plan_output += "Distance of the route: {}m\n".format(route_distance)
        print(plan_output)
        total_distance += route_distance

        if len(route) > 2:
            routes.append(route)

    print("Total Distance of all routes: {}m".format(total_distance))

    return routes


# [END solution_printer]
def verify_route(route):
    """Verify that the route satisfies the constraint."""
    # The route must start and end at the depot
    print("VERIFY", route)

    return True


class NoABTogetherFilter(pywrapcp.LocalSearchFilter):
    def __init__(self, manager, routing, data):
        # super().__init__(self)
        self.manager = manager
        self.routing = routing
        self.data = data

    def Accept(self, from_index, to_index, delta):
        # Get the current solution and convert it to a list of routes
        solution = self.routing.ReadAssignmentFromRouting(self.manager, self.routing.solver())
        routes = []
        for vehicle_id in range(self.data['num_vehicles']):
            index = self.routing.Start(vehicle_id)
            route = []
            while not self.routing.IsEnd(index):
                node_index = self.manager.IndexToNode(index)
                route.append(node_index)
                index = solution.Value(self.routing.NextVar(index))
            routes.append(route)

        # Check the constraint on each route
        for route in routes:
            if not verify_route(route):
                return False

        # The solution is valid
        return True


def main():
    """Entry point of the program."""
    # Instantiate the data problem.
    # [START data]
    data = create_data_model()
    # [END data]

    # Create the routing index manager.
    num = len(data["distance_matrix"])
    print(" # items:", num)
    print(" # vehicles:", data["num_vehicles"])
    print(" depot index:", data["depot"])
    print()

    # [START index_manager]
    manager = pywrapcp.RoutingIndexManager(
        len(data["distance_matrix"]), data["num_vehicles"], data["depot"]
    )
    # [END index_manager]

    # Create Routing Model.
    # [START routing_model]
    routing = pywrapcp.RoutingModel(manager)

    # [END routing_model]

    # Create and register a transit callback.
    # [START transit_callback]
    def distance_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data["distance_matrix"][from_node][to_node]

    transit_callback_dist_index = routing.RegisterTransitCallback(distance_callback)

    def time_callback(from_index, to_index):
        """Returns the time between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data["time_matrix"][from_node][to_node]

    transit_callback_time_index = routing.RegisterTransitCallback(time_callback)
    # [END transit_callback]

    # Define cost of each arc.
    # [START arc_cost]
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_dist_index)
    # [END arc_cost]

    # [START constraints]
    routing.AddDimension(
        transit_callback_dist_index,
        0,
        2900,
        False,
        "Distance"
    )

    routing.AddDimension(
        transit_callback_time_index,
        60,
        1000,
        False,
        "time_constraint"
    )
    # [END constraints]

    # Setting first solution heuristic.
    # [START parameters]
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    # [END parameters]

    # [START local_search]
    # filter1 = NoABTogetherFilter(manager, routing, data)
    # routing.AddLocalSearchFilter(filter1)
    # [END local_search]

    # Solve the problem.
    # [START solve]
    solution = routing.SolveWithParameters(search_parameters)
    # [END solve]

    # Print solution on console.
    # [START print_solution]
    if solution:
        print_solution(data, manager, routing, solution)
    else:
        print("No solution found !")
    # [END print_solution]


if __name__ == "__main__":
    main()
# [END program]
