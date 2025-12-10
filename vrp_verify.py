import sys
import json
from typing import List


def in_time_window(t: int, t_window: List[int]) -> bool:
    if len(t_window) == 0:
        return True
    return t_window[0] <= t <= t_window[1]


def verify_node(node: dict, vehicle_id: int, parameters: dict) -> bool:
    node_str = (
        f" vehicle {vehicle_id} node {node['node_name']} "
        f"(idx={node['index']}, nd_idx={node['node_index']})"
    )
    ok = True

    if not in_time_window(node["time_start"], node["time_window"]):
        ok = False
        print(f" {node_str} has time_start out of time window")
    if not in_time_window(node["time_end"], node["time_window"]):
        ok = False
        print(f" {node_str} has time_end out of time window")

    if node["time_accumulated"] > parameters["max_time_duration"]:
        ok = False
        print(f" {node_str} time_accumulated out of max_time_duration")
    if node["time_start"] > parameters["max_time_duration"]:
        ok = False
        print(f" {node_str} time_start out of max_time_duration")
    if node["time_end"] > parameters["max_time_duration"]:
        ok = False
        print(f" {node_str} time_end out of max_time_duration")

    if node["time_accumulated"] > parameters["max_delivery_time"]:
        ok = False
        print(f" {node_str} time_accumulated out of max_delivery_time")
    if node["distance_accumulated"] > parameters["max_delivery_distance"]:
        ok = False
        print(f" {node_str} time_accumulated out of max_delivery_distance")
    if node["load_accumulated"] > parameters["courier_item_capacity"]:
        ok = False
        print(f" {node_str} load_accumulated out of courier_item_capacity")
    if node["weight_accumulated"] > parameters["courier_weight_capacity"]:
        ok = False
        print(f" {node_str} weight_accumulated out of courier_weight_capacity")

    return ok


def verify_route(route: dict, parameters: dict) -> bool:
    id = route["vehicle_id"]
    ok = True
    for node in route["route"]:
        node_ok = verify_node(node, id, parameters)
        ok = node_ok and ok

    return ok


def verify(data: dict) -> bool:
    ok = True
    if data["solver"]["status_code"] != 1:
        print(f"! Solver status is not success: {data['solver']['status']}")
        ok = False

    for route in data["routes"]:
        route_ok = verify_route(route, data["parameters"])
        ok = route_ok and ok

    return ok


def verify_file(json_file: str) -> bool:
    with open(json_file, "r") as f:
        json_data = json.load(f)
    return verify(json_data)


def main():
    if len(sys.argv) < 2:
        print("Parameter required: solutions json file")
        return

    json_file = sys.argv[1]
    print(f"Verifying file {json_file}...")
    result = verify_file(json_file)

    if result:
        print("Results comply with the constraints.")
    else:
        print("Some results do NOT comply with the constraints!")


if __name__ == "__main__":
    main()
