from typing import Dict, List

from .vrp_parameters import ModelType, VehicleConstraintParameters, VRPParameters


def add_node_lists_to_route(routes: List[Dict]) -> List[Dict]:
    """Add a simple list of the visited nodes (in the order) by index and name."""
    for route in routes:
        route["node_index_route"] = [n["node_index"] for n in route["route"]]
        route["node_index_names"] = [n["node_name"] for n in route["route"]]
    return route


def flag_vehicle_constraints(routes: List[Dict], vrp_parameters: VRPParameters) -> List[Dict]:
    """For each route set the vehicle type constraint if the constraints are set."""
    if vrp_parameters.vehicle_constraints is None:
        print("No vehicle constraints set.")
        return routes

    for route in routes:
        loads = [n.get("load_accumulated", 0) for n in route["route"]]
        load = max(loads)
        weights = [n.get("weight_accumulated", 0) for n in route["route"]]
        weight = max(weights)
        route["vehicle_flags"] = vrp_parameters.vehicle_constraints.get_vehicles_for_item(
            VehicleConstraintParameters(load, weight)
        )

    return routes


def process_solution_data(solution, vrp_model):
    """Prints solution on console and retrieves processed results.
    {
       "routes":
       [ {
           vehicle_id: 0,
           route: [ {
                       "node_index": 0,
                       "node_name": "depot",
                       "time_start": 0,
                       "time_end": 10,
                       "distance_previous": 0,
                       "distance_accumulated": 0,
                       "time_previous": 0,
                       "time_accumulated": 0
                   },
                   {
                       "node_index": 3,
                       "node_name": "P0",
                       "time_start": 40,
                       "time_end": 40,
                       "distance_previous": 100,
                       "distance_accumulated": 100,
                       "time_previous": 40,
                       "time_accumulated": 40
                   }, ..
           ]
       }, ...
    ],
    "meta": {
       "num_vehicles_used": 2,
    }
    "

    """

    has_time_dimension = vrp_model.model_type != ModelType.distance
    time_dimension = vrp_model.routing.GetDimensionOrDie("Time") if has_time_dimension else None
    total_time = 0
    total_distance = 0
    total_load = 0
    total_cost = 0
    total_weight = 0
    num_vehicles_used = 0
    routes = []

    for vehicle_id in range(vrp_model.data["num_vehicles"]):
        index = vrp_model.routing.Start(vehicle_id)
        next_i = solution.Value(vrp_model.routing.NextVar(index))
        if vrp_model.routing.IsEnd(next_i):
            # vehicle not used
            continue

        num_vehicles_used += 1
        route = []

        start_time = None
        index = vrp_model.routing.Start(vehicle_id)
        route_distance = this_distance = 0
        route_cost = this_cost = 0
        route_load = this_load = 0
        route_weight = this_weight = 0
        route_time = this_time = 0
        previous_node_index = previous_index = -1
        while not vrp_model.routing.IsEnd(index):
            node_index = vrp_model.manager.IndexToNode(index)

            # number of items
            if "number_of_items" in vrp_model.data:
                this_load = vrp_model.data["number_of_items"][node_index]
                route_load += this_load

            # order weight
            if "weights" in vrp_model.data:
                this_weight = vrp_model.data["weights"][node_index]
                route_weight += this_weight

            # time
            if has_time_dimension:
                time_var = time_dimension.CumulVar(index)
                if start_time is None:
                    start_time = solution.Min(time_var)

            if previous_index >= 0:
                # time
                this_time = vrp_model.data["time_matrix"][previous_node_index][node_index]
                route_time += this_time

                # distance
                this_distance = vrp_model.data["distance_matrix"][previous_node_index][node_index]
                route_distance += this_distance

                # cost
                this_cost = vrp_model.routing.GetArcCostForVehicle(
                    previous_index, index, vehicle_id
                )
                route_cost += this_cost

            time_window = (
                vrp_model.data["time_windows"][node_index]
                if "time_windows" in vrp_model.data
                else []
            )

            route.append(
                {
                    "node_index": node_index,
                    "index": index,
                    "node_name": vrp_model.data["node_names"][node_index],
                    "location": vrp_model.data["locations"][node_index],
                    "time_start": solution.Min(time_var) if has_time_dimension else None,
                    "time_end": solution.Max(time_var) if has_time_dimension else None,
                    "time_window": time_window,
                    "time": this_time,
                    "time_accumulated": route_time,
                    "distance": this_distance,
                    "distance_accumulated": route_distance,
                    "cost": this_cost,
                    "cost_accumulated": route_cost,
                    "load": this_load,
                    "load_accumulated": route_load,
                    "weight": this_weight,
                    "weight_accumulated": route_weight,
                }
            )

            previous_index = index
            previous_node_index = node_index
            index = solution.Value(vrp_model.routing.NextVar(index))

        total_time += route_time
        total_distance += route_distance
        total_cost += route_cost
        total_load += route_load
        total_weight += route_weight

        capacities = dict()
        for capacity in ["courier_item_capacities", "courier_weight_capacities"]:
            if capacity in vrp_model.data:
                capacities[capacity] = vrp_model.data[capacity][vehicle_id]

        routes.append(
            {
                "vehicle_id": vehicle_id,
                **capacities,
                "route": route,
            }
        )

    add_node_lists_to_route(routes)
    flag_vehicle_constraints(routes, vrp_model.parameters)

    return {
        "routes": routes,
        "meta": vrp_model.data["meta"],
        "filter": vrp_model.data["filter"],
        "summary": {
            "total_time": total_time,
            "total_distance": total_distance,
            "total_cost": total_cost,
            "total_load": total_load,
            "total_weight": total_weight,
            "num_vehicles_used": num_vehicles_used,
        },
        "parameters": vrp_model.parameters.to_dict(),
    }
