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
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from examples.vrp_ex import create_data_model, print_solution

# [END import]


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
        # if from_index>=num or to_index>=num:
        #    print(f" *dc i=({from_index}, {to_index}) -> node=({from_node}, {to_node}) (n={num})")
        return data["distance_matrix"][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    # [END transit_callback]

    # Add distance constraint
    routing.AddDimension(
        transit_callback_index,
        0,  # no slack
        2500,  # maximum distance per vehicle
        False,  # Don't force start cumul to zero.
        "distance_contraint",
    )

    # Define cost of each arc.
    # [START arc_cost]
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    # [END arc_cost]

    # Setting first solution heuristic.
    # [START parameters]
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    # [END parameters]

    # Solve the problem.
    # [START solve]
    # See https://stackoverflow.com/a/63558915/1771479
    routing.CloseModelWithParameters(search_parameters)
    # Re-use a previous solution and improve on that.
    # Note: this initial solution is slightly changed.
    initial_solution = routing.ReadAssignmentFromRoutes(
        [[12, 13, 15, 11, 3, 4, 1, 7], [5, 8, 6, 2, 10, 16, 14, 9]], True
    )
    solution = routing.SolveFromAssignmentWithParameters(initial_solution, search_parameters)
    # [END solve]

    # Print solution on console.
    # [START print_solution]
    if solution:
        routes = print_solution(data, manager, routing, solution)
        print(routes)
    else:
        print("No solution found !")
    # [END print_solution]


if __name__ == "__main__":
    main()
# [END program]
