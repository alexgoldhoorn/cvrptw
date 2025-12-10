"""Simple Pickup Delivery Problem (PDP).

AG: trying to add time windows using the time window example as a reference.
"""
import numpy as np

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp


def create_data_model():
    """Stores the data for the problem."""
    data = {}
    data["distance_matrix"] = [
        [
            0,
            548,
            776,
            696,
            582,
            274,
            502,
            194,
            308,
            194,
            536,
            502,
            388,
            354,
            468,
            776,
            662,
        ],
        [
            548,
            0,
            684,
            308,
            194,
            502,
            730,
            354,
            696,
            742,
            1084,
            594,
            480,
            674,
            1016,
            868,
            1210,
        ],
        [
            776,
            684,
            0,
            992,
            878,
            502,
            274,
            810,
            468,
            742,
            400,
            1278,
            1164,
            1130,
            788,
            1552,
            754,
        ],
        [
            696,
            308,
            992,
            0,
            114,
            650,
            878,
            502,
            844,
            890,
            1232,
            514,
            628,
            822,
            1164,
            560,
            1358,
        ],
        [
            582,
            194,
            878,
            114,
            0,
            536,
            764,
            388,
            730,
            776,
            1118,
            400,
            514,
            708,
            1050,
            674,
            1244,
        ],
        [
            274,
            502,
            502,
            650,
            536,
            0,
            228,
            308,
            194,
            240,
            582,
            776,
            662,
            628,
            514,
            1050,
            708,
        ],
        [
            502,
            730,
            274,
            878,
            764,
            228,
            0,
            536,
            194,
            468,
            354,
            1004,
            890,
            856,
            514,
            1278,
            480,
        ],
        [
            194,
            354,
            810,
            502,
            388,
            308,
            536,
            0,
            342,
            388,
            730,
            468,
            354,
            320,
            662,
            742,
            856,
        ],
        [
            308,
            696,
            468,
            844,
            730,
            194,
            194,
            342,
            0,
            274,
            388,
            810,
            696,
            662,
            320,
            1084,
            514,
        ],
        [
            194,
            742,
            742,
            890,
            776,
            240,
            468,
            388,
            274,
            0,
            342,
            536,
            422,
            388,
            274,
            810,
            468,
        ],
        [
            536,
            1084,
            400,
            1232,
            1118,
            582,
            354,
            730,
            388,
            342,
            0,
            878,
            764,
            730,
            388,
            1152,
            354,
        ],
        [
            502,
            594,
            1278,
            514,
            400,
            776,
            1004,
            468,
            810,
            536,
            878,
            0,
            114,
            308,
            650,
            274,
            844,
        ],
        [
            388,
            480,
            1164,
            628,
            514,
            662,
            890,
            354,
            696,
            422,
            764,
            114,
            0,
            194,
            536,
            388,
            730,
        ],
        [
            354,
            674,
            1130,
            822,
            708,
            628,
            856,
            320,
            662,
            388,
            730,
            308,
            194,
            0,
            342,
            422,
            536,
        ],
        [
            468,
            1016,
            788,
            1164,
            1050,
            514,
            514,
            662,
            320,
            274,
            388,
            650,
            536,
            342,
            0,
            764,
            194,
        ],
        [
            776,
            868,
            1552,
            560,
            674,
            1050,
            1278,
            742,
            1084,
            810,
            1152,
            274,
            388,
            422,
            764,
            0,
            798,
        ],
        [
            662,
            1210,
            754,
            1358,
            1244,
            708,
            480,
            856,
            514,
            468,
            354,
            844,
            730,
            536,
            194,
            798,
            0,
        ],
    ]
    data["pickups_deliveries"] = [
        [1, 6],
        [2, 10],
        [4, 3],
        [5, 9],
        [7, 8],
        [15, 11],
        [13, 12],
        [16, 14],
    ]
    data["num_vehicles"] = 4
    data["vehicle_capacities"] = [3] * data["num_vehicles"]
    data["depot"] = 0

    # -- add time windows
    data["speed"] = 5  # m/s
    data["time_matrix"] = (np.array(data["distance_matrix"]) / data["speed"]).astype(
        np.int64
    )
    data["time_windows"] = [
        (0, 100000),  # depot
        (1000, 200000),  # 1
        (0, 200000),  # 2
        (0, 200000),  # 3
        (0, 200000),  # 4
        (0, 200000),  # 5
        (0, 200000),  # 6
        (0, 200000),  # 7
        (0, 200000),  # 8
        (0, 200000),  # 9
        (0, 200000),  # 10
        (0, 200000),  # 11
        (0, 200000),  # 12
        (0, 200000),  # 13
        (0, 200000),  # 14
        (0, 200000),  # 15
        (0, 200000),  # 16
    ]
    data["demands"] = [0] + [0, 1] * len(data["pickups_deliveries"])

    return data


def print_solution_dist(data, manager, routing, solution):
    """Prints solution on console."""
    print(f"Objective: {solution.ObjectiveValue()}")
    total_distance = 0
    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        plan_output = "Route for vehicle {}:\n".format(vehicle_id)
        route_distance = 0
        while not routing.IsEnd(index):
            plan_output += " {} -> ".format(manager.IndexToNode(index))
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id
            )
        plan_output += "{}\n".format(manager.IndexToNode(index))
        plan_output += "Distance of the route: {}m\n".format(route_distance)
        print(plan_output)
        total_distance += route_distance
    print("Total Distance of all routes: {}m".format(total_distance))


def print_solution(data, manager, routing, solution):
    """Prints solution on console."""
    print(f"Objective: {solution.ObjectiveValue()}")
    time_dimension = routing.GetDimensionOrDie("Time")
    total_time = 0
    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        plan_output = "Route for vehicle {}:\n".format(vehicle_id)
        route_start_time = None
        while not routing.IsEnd(index):
            time_var = time_dimension.CumulVar(index)
            plan_output += "{0} Time({1},{2}) -> ".format(
                manager.IndexToNode(index),
                solution.Min(time_var),
                solution.Max(time_var),
            )
            if route_start_time is None:
                route_start_time = solution.Min(time_var)
            index = solution.Value(routing.NextVar(index))
        time_var = time_dimension.CumulVar(index)
        plan_output += "{0} Time({1},{2})\n".format(
            manager.IndexToNode(index), solution.Min(time_var), solution.Max(time_var)
        )
        route_time = solution.Min(time_var) - route_start_time
        plan_output += "Time of the route: {} s\n".format(route_time)
        print(plan_output)
        total_time += solution.Min(time_var)
    print("Total time of all routes: {} s".format(total_time))


def main():
    """Entry point of the program."""
    # Instantiate the data problem.
    data = create_data_model()

    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(
        len(data["distance_matrix"]), data["num_vehicles"], data["depot"]
    )

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)

    # Define cost of each arc.
    def time_callback(from_index, to_index):
        """Returns the manhattan distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data["time_matrix"][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(time_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Dimension for pickup/delivery times (/ distances later?)
    dimension_name = "time_pudel"
    routing.AddDimension(
        transit_callback_index,
        0,  # no slack
        60 * 60,  # 3000,  # vehicle maximum travel distance
        True,  # start cumul to zero
        dimension_name,
    )
    pudel_dimension = routing.GetDimensionOrDie(dimension_name)
    pudel_dimension.SetGlobalSpanCostCoefficient(100)

    # Define Transportation Requests.
    for request in data["pickups_deliveries"]:
        pickup_index = manager.NodeToIndex(request[0])
        delivery_index = manager.NodeToIndex(request[1])
        routing.AddPickupAndDelivery(pickup_index, delivery_index)
        routing.solver().Add(
            routing.VehicleVar(pickup_index) == routing.VehicleVar(delivery_index)
        )
        routing.solver().Add(
            pudel_dimension.CumulVar(pickup_index)
            <= pudel_dimension.CumulVar(delivery_index)
        )

    # Add time windows
    time = "Time"
    routing.AddDimension(
        transit_callback_index,
        1 * 60,  # allow waiting time
        60 * 60,  # maximum time per vehicle
        False,  # Don't force start cumul to zero.
        time,
    )
    time_dimension = routing.GetDimensionOrDie(time)
    # Add time window constraints for each location except depot.
    for location_idx, time_window in enumerate(data["time_windows"]):
        if location_idx == data["depot"]:
            continue
        index = manager.NodeToIndex(location_idx)
        time_dimension.CumulVar(index).SetRange(time_window[0], time_window[1])
    # Add time window constraints for each vehicle start node.
    depot_idx = data["depot"]
    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        time_dimension.CumulVar(index).SetRange(
            data["time_windows"][depot_idx][0], data["time_windows"][depot_idx][1]
        )

    # Add route duration constraint.
    routing.AddDimension(
        transit_callback_index,
        60,  # allow waiting time
        460,  # maximum time per vehicle
        False,  # Don't force start cumul to zero.
        "time_constraint",
    )

    # Instantiate route start and end times to produce feasible times.
    for i in range(data["num_vehicles"]):
        routing.AddVariableMinimizedByFinalizer(
            time_dimension.CumulVar(routing.Start(i))
        )
        routing.AddVariableMinimizedByFinalizer(time_dimension.CumulVar(routing.End(i)))

    def demand_callback(index):
        """Returns the manhattan distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        node = manager.IndexToNode(index)
        return data["demands"][node]

    if "vehicle_capacities" in data:
        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # null capacity slack
            data["vehicle_capacities"],  # vehicle maximum capacities
            True,  # start cumul to zero
            "Capacity",
        )
    else:
        print("Warning: no capacity constraint")

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
    )

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)

    # Print solution on console.
    if solution:
        print_solution(data, manager, routing, solution)
        print("--dist--")
        print_solution_dist(data, manager, routing, solution)
    else:
        print("NO solution, status=", routing.status())


if __name__ == "__main__":
    main()
