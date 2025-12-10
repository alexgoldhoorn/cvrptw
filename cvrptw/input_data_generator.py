import numpy as np
import pandas as pd
from typing import List, Optional, Dict

from .distance import coord_distance, euclidean_distance
from .quick_vrp import QuickVRP
from .vrp_parameters import VRPParameters, ModelType
from .utils import convert_field_to_int


def calculate_distance_matrix(
    locations: List[List[float]], distance_func
) -> List[List[float]]:
    """ "
    Calculate the distance between all points i n the locations list.
    Args:
        locations: a list of all locations (x, y) or (latitude, longitude)
        distance_func: distance function
    Returns:
        distance matrix
    """
    n_items = len(locations)
    dist_mat = np.zeros((n_items, n_items))
    for i in range(n_items):
        for j in range(i, n_items):
            if i == j:
                continue
            # Setting distance to depot 0, since we don't want to go back.
            d = distance_func(locations[i], locations[j])
            if j != 0:
                dist_mat[i, j] = d
            if i != 0:
                dist_mat[j, i] = d

    return dist_mat


def calculate_time_matrix(
    distance_matrix, speed: float, waiting_time_at_delivery: float, pickup_rows=[0]
):
    """
    Calculate the time based on a fixed speed and waiting time at delivery.
    Args:
        distance_matrix:    distance matrix between all points
        speed:              fixed speed to calculate the time
        waiting_time_at_delivery: waiting time at each delivery point
        pickup_rows:        rows which are pickup and thus have no waiting_time_at_delivery
    Returns:
        time matrix
    """
    time_mat = waiting_time_at_delivery + distance_matrix / speed
    # remove waiting_time_at_delivery from pickup to any
    time_mat[:, pickup_rows] -= waiting_time_at_delivery
    # Note: setting time to depot 0, since we don't want to go back
    time_mat[:, 0] = 0
    np.fill_diagonal(time_mat, 0)
    return time_mat


def create_base_data(n_orders: int, n_max_couriers: int, model: str):
    return {
        "meta": {"n_orders": n_orders, "n_max_couriers": n_max_couriers, "type": model},
    }


def filter_time_window_constraints(
    order_time_windows, order_pickup_time_windows, duration, meta_results: Dict
):
    """Filter orders based on time window constraints:
    - either inconsistent time windows (lower bound > upper bound)
    - or infeasible time windows (duration > time window)
    """

    inconsistent_time_windows = (
        order_time_windows[:, 0] > order_pickup_time_windows[:, 1]
    )
    meta_results["inconsistent_time_windows"] = inconsistent_time_windows.sum()

    min_duration_for_time_window = (
        order_time_windows[:, 0] - order_pickup_time_windows[:, 1]
    )
    max_duration_for_time_window = (
        order_time_windows[:, 1] - order_pickup_time_windows[:, 0]
    )
    pass_time_window_constraint = (min_duration_for_time_window <= duration) & (
        duration <= max_duration_for_time_window
    )
    meta_results["time_window_infeasible"] = (~pass_time_window_constraint).sum()

    return ~inconsistent_time_windows & pass_time_window_constraint


def estimate_distance_time_items_and_weight_bundle(
    pickup_location,
    order_locations,
    order_number_items,
    weights,
    parameters: VRPParameters,
    dist_func,
):
    qvrp = QuickVRP(
        pickup_location,
        order_locations,
        dist_func,
        extra_cost_per_visit=0,
        max_calc_time=10,
    )
    solution = qvrp.solve()
    distance = solution["total_cost"]
    duration = distance / parameters.speed
    for route in solution["routes"]:
        # Note: for this case we actually want it to be 1 route, since
        # they were already bundled and will be constrained to be in the same route.
        assert len(route) > 0
        duration += parameters.waiting_time_at_delivery * (len(route) - 1)

    if order_number_items is None:
        number_items = None
    else:
        number_items = order_number_items.sum()

    if weights is None:
        weight = None
    else:
        weight = weights.sum()

    return distance, duration, number_items, weight


def bundle_lists(existing_bundle_ids, index_delta: int = 0):
    df = pd.DataFrame({"existing_bundle_ids": existing_bundle_ids}).reset_index()
    if index_delta > 0:
        df["index"] += index_delta
    return (
        df.groupby("existing_bundle_ids").agg({"index": list})["index"].values.tolist()
    )


def filter_existing_bundle_constraints(
    order_locations,
    pickup_location,
    parameters: VRPParameters,
    dist_func,
    meta_results: Dict,
    existing_bundle_ids: List[int],
    order_number_items,
    weights,
):
    assert len(order_locations) == len(existing_bundle_ids), (
        f"the number of order locations {len(order_locations)} should be equal to the number of"
        f" existing bundle ids {len(existing_bundle_ids)}"
    )
    meta_results["infeasible_existing_bundle"] = 0
    pass_bundle_constraints = np.ones(len(order_locations), dtype=bool)
    bundles = bundle_lists(existing_bundle_ids)
    for bundle in bundles:
        order_of_bundles = order_locations[bundle]
        order_number_items_of_bundles = (
            None if order_number_items is None else order_number_items[bundle]
        )
        weights_of_bundles = None if weights is None else weights[bundle]
        (
            distance,
            duration,
            number_items,
            weight,
        ) = estimate_distance_time_items_and_weight_bundle(
            pickup_location,
            order_of_bundles,
            order_number_items_of_bundles,
            weights_of_bundles,
            parameters,
            dist_func,
        )
        if (
            distance > parameters.max_delivery_distance
            or duration > parameters.max_delivery_time
            or number_items is not None
            and number_items >= parameters.courier_item_capacity
            or weight is not None
            and weight >= parameters.courier_weight_capacity
        ):
            meta_results["infeasible_existing_bundle"] += 1
            for order in bundle:
                pass_bundle_constraints[order] = False

    return pass_bundle_constraints


def filter_orders(
    order_locations,
    order_time_windows,
    order_number_items,
    weights,
    pickup_location,
    order_pickup_time_windows,
    parameters: VRPParameters,
    dist_func,
    order_ids,
    existing_bundle_ids: Optional[List[int]],
):
    """
    Check if each order complies with the minimum constraint, i.e. such that assigning
    it to 1 route it passes the constraints.
    """
    meta_results = dict()

    if parameters.multi_pickup:
        assert len(pickup_location) == len(order_locations), (
            f"the number of pickup locations {len(pickup_location)} should be equal to the number of"
            f" order locations {len(order_locations)}"
        )
        distance = np.array([dist_func(pickup_location[i], order_locations[i]) for i in range(len(order_locations))])
    else:
        distance = np.array([dist_func(pickup_location, o) for o in order_locations])
    pass_distance_constraint = distance <= parameters.max_delivery_distance
    meta_results["distance_infeasible"] = (~pass_distance_constraint).sum()

    duration = parameters.waiting_time_at_delivery + distance / parameters.speed
    pass_duration_constraint = duration <= parameters.max_delivery_time
    meta_results["time_infeasible"] = (~pass_duration_constraint).sum()

    pass_item_capacity = order_number_items <= parameters.courier_item_capacity
    meta_results["item_capacity_infeasible"] = (~pass_item_capacity).sum()

    if weights is None:
        pass_weight_capacity = pass_item_capacity
    else:
        pass_weight_capacity = weights <= parameters.courier_weight_capacity
        meta_results["weight_capacity_infeasible"] = (~pass_weight_capacity).sum()

    pass_constraints = (
        pass_distance_constraint
        & pass_duration_constraint
        & pass_item_capacity
        & pass_weight_capacity
    )

    if order_time_windows is not None and order_pickup_time_windows is not None:
        pass_time_window_constraint = filter_time_window_constraints(
            order_time_windows, order_pickup_time_windows, duration, meta_results
        )
        pass_constraints = pass_constraints & pass_time_window_constraint

    if existing_bundle_ids is not None:
        pass_for_bundle_constraints = filter_existing_bundle_constraints(
            order_locations,
            pickup_location,
            parameters,
            dist_func,
            meta_results,
            existing_bundle_ids,
            order_number_items,
            weights,
        )
        pass_constraints = pass_constraints & pass_for_bundle_constraints

    meta_results["n_filtered"] = (~pass_constraints).sum()
    if order_ids is not None and meta_results["n_filtered"] > 0:
        print("Filtered out orders:", order_ids[~pass_constraints])

    return (
        order_locations[pass_constraints],
        None if order_time_windows is None else order_time_windows[pass_constraints],
        order_number_items[pass_constraints],
        None if weights is None else weights[pass_constraints],
        None
        if order_pickup_time_windows is None
        else order_pickup_time_windows[pass_constraints],
        meta_results,
        None if order_ids is None else order_ids[pass_constraints],
        existing_bundle_ids[pass_constraints],
    )


def create_data_model_from_orders(
    order_locations,
    order_time_windows,
    order_number_items,
    weights,
    pickup_location,
    n_couriers: int,
    parameters: VRPParameters,
    dist_func=coord_distance,
    order_ids: Optional[List[int]] = None,
    do_filter: bool = True,
    existing_bundle_ids: Optional[List[int]] = None,
):
    """
    Generates all meta data for the solver.
    """
    assert not parameters.multi_pickup, "multi-pickup only implemented for pickup-delivery model"
    data = create_base_data(
        len(order_locations),
        n_couriers,
        "delivery",
    )

    if do_filter:
        (
            order_locations,
            order_time_windows,
            order_number_items,
            weights,
            _,
            data["filter"],
            order_ids,
            existing_bundle_ids,
        ) = filter_orders(
            order_locations,
            order_time_windows,
            order_number_items,
            weights,
            pickup_location,
            None,
            parameters,
            dist_func,
            order_ids,
            existing_bundle_ids,
        )

    n_items = len(order_locations) + 1  # pickup store
    loc_mat = np.concatenate([[pickup_location], order_locations])
    # note: first is the start (pickup) location.
    data["locations"] = loc_mat

    data["distance_matrix"] = calculate_distance_matrix(loc_mat, dist_func)
    data["time_matrix"] = calculate_time_matrix(
        data["distance_matrix"], parameters.speed, parameters.waiting_time_at_delivery
    )

    # add courier weight to first distance (start to any) for the cost
    cost_mat = data["distance_matrix"].copy()
    cost_mat[0, :] += parameters.courier_cost
    cost_mat[0, 0] = 0
    data["cost_matrix"] = cost_mat

    # these are num items in order
    data["number_of_items"] = np.append([0], order_number_items)
    data["courier_item_capacities"] = [parameters.courier_item_capacity] * n_couriers
    if existing_bundle_ids is not None:
        data["on_the_way_bundles"] = bundle_lists(existing_bundle_ids, index_delta=1)

    if weights is not None:
        data["weights"] = np.append([0], weights)
        data["courier_weight_capacities"] = [
            parameters.courier_weight_capacity
        ] * n_couriers

    # time windows for depot and delivery
    if order_time_windows is not None:
        data["time_windows"] = np.concatenate(
            [[[0, parameters.max_time_duration]], order_time_windows]
        )

    # store original IDs/names of nodes
    if order_ids is None:
        order_ids = range(1, n_items)
    data["node_names"] = ["depot"] + list(map(str, order_ids))

    # convert to int
    for field in [
        "distance_matrix",
        "cost_matrix",
        "time_matrix",
        "time_windows",
        "number_of_items",
        "weights",
        "courier_item_capacities",
    ]:
        if field in data:
            convert_field_to_int(data, field)

    # general info
    data["num_vehicles"] = n_couriers
    data["depot"] = 0

    return data


def create_data_pu_del_model_from_orders(
    order_locations,
    order_time_windows,
    order_number_items,
    weights,
    pickup_location,
    n_couriers,
    order_pickup_time_windows,
    parameters: VRPParameters,
    dist_func=coord_distance,
    order_ids: Optional[List[int]] = None,
    do_filter: bool = True,
    existing_bundle_ids: Optional[List[int]] = None,
):
    """
    Generates all meta data for the solver.
    """
    # We have to list all order locations AND the pickup location (which is the same) for all of
    # them, such that we can put a time window on both the pickup and delivery location per order.
    data = create_base_data(
        len(order_locations),
        n_couriers,
        "pickup-delivery",
    )

    if do_filter:
        (
            order_locations,
            order_time_windows,
            order_number_items,
            weights,
            order_pickup_time_windows,
            data["filter"],
            order_ids,
            existing_bundle_ids,
        ) = filter_orders(
            order_locations,
            order_time_windows,
            order_number_items,
            weights,
            pickup_location,
            order_pickup_time_windows,
            parameters,
            dist_func,
            order_ids,
            existing_bundle_ids,
        )

    n_orders = len(order_locations)

    n_items = n_orders * 2 + 1  # pickup store
    # format will be: [depot, pickup_1, pickup_2, ..., pickup_n, delivery_1, .. delivery_n]
    # note: depot = pickup location, also all pickup locations are the same (for now)
    loc_mat = np.concatenate([[pickup_location] * (1 + n_orders), order_locations])
    # note: first is the start (pickup) location.
    data["locations"] = loc_mat

    # pickup and delivery nodes
    # (note: we skip index 0 because it is the 'depot')
    data["pickups_deliveries"] = [(i, i + n_orders) for i in range(1, n_orders + 1)]

    data["distance_matrix"] = calculate_distance_matrix(loc_mat, dist_func)
    data["time_matrix"] = calculate_time_matrix(
        data["distance_matrix"],
        parameters.speed,
        parameters.waiting_time_at_delivery,
        range(1 + n_orders),
    )

    # add courier weight to first distance (start to any) for the cost
    cost_mat = data["time_matrix"].copy()
    cost_mat[0, range(1, 1 + n_orders)] += parameters.courier_cost
    cost_mat[0, 0] = 0
    data["cost_matrix"] = cost_mat

    # set the time windows for the depot, pickup of the orders and delivery of the orders
    data["time_windows"] = np.concatenate(
        [
            [[0, parameters.max_time_duration]],
            order_pickup_time_windows,
            order_time_windows,
        ]
    )

    # these are num items in order
    # note: we set 0 for the depot
    # for the pickup location we set the load per order, and -1*load for the delivery,
    #  note that we could also keep the load at 0 for the delivery.
    data["number_of_items"] = np.append(
        [0], np.append(order_number_items, [0] * n_orders)
    )
    data["courier_item_capacities"] = [parameters.courier_item_capacity] * n_couriers
    if existing_bundle_ids is not None:
        data["on_the_way_bundles"] = bundle_lists(existing_bundle_ids, index_delta=1)

    if weights is not None:
        data["weights"] = np.append([0], np.append(weights, [0] * n_orders))
        data["courier_weight_capacities"] = [
            parameters.courier_weight_capacity
        ] * n_couriers

    # store original IDs/names of nodes
    if order_ids is None:
        order_ids = range(1, n_items)
    data["node_names"] = (
        ["depot"] + [f"P{i}" for i in order_ids] + [f"D{i}" for i in order_ids]
    )

    # convert to int
    for field in [
        "distance_matrix",
        "cost_matrix",
        "time_matrix",
        "time_windows",
        "pickup_time_windows",
        "number_of_items",
        "weights" "courier_item_capacities",
        "courier_weight_capacities",
    ]:
        if field in data:
            convert_field_to_int(data, field)

    # general info
    data["num_vehicles"] = n_couriers
    data["depot"] = 0
    return data


def create_random_data_model_test(
    n_orders: int,
    n_couriers: int,
    parameters: VRPParameters,
    max_dist: int = 4000,
    max_demand: int = 4,
    xparam: int = 0,
):
    """
    Stores and created the random data for the problem of size n_orders
    (note that it includes the start location).
    """
    pickup_loc = np.random.random(2) * max_dist / 2
    order_locs = np.random.random((n_orders, 2)) * max_dist / 2
    order_num_items = np.append(
        [0], np.random.randint(1, max_demand + 1, size=n_orders)
    )

    if xparam == 0:
        order_time_windows = [(0, 24 * 3600) for _ in range(n_orders)]
    else:
        print("Using tighter time windows")
        time_windows = [(s, s + 30 * 60) for s in range(10 * 3600, 22 * 3600, 30 * 60)]
        order_time_windows = [
            time_windows[np.random.randint(len(time_windows))] for _ in range(n_orders)
        ]

    if parameters.model_type == ModelType.live:
        pickup_order_time_windows = [(0, 24 * 3600) for _ in range(n_orders)]
        return create_data_pu_del_model_from_orders(
            order_locs,
            order_time_windows,
            order_num_items,
            pickup_loc,
            n_couriers,
            pickup_order_time_windows,
            parameters,
            dist_func=euclidean_distance,
        )

    return create_data_model_from_orders(
        order_locs,
        order_time_windows,
        order_num_items,
        pickup_loc,
        n_couriers,
        parameters,
        dist_func=euclidean_distance,
    )


def create_data_model_from_csv_file(
    file_name: str,
    parameters: VRPParameters,
    return_df=False,
):
    print(f"Loading {file_name} ...")
    df_in = pd.read_csv(file_name)
    df_in.columns = df_in.columns.str.strip()
    data = create_data_model_from_dataframe(df_in, parameters)
    if return_df:
        return data, df_in
    else:
        return data


def create_data_model_from_dataframe(
    df: pd.DataFrame,
    parameters: VRPParameters,
):
    """
    Stores and created the random data for the problem of size n_orders
    (note that it includes the start location).
    """
    n_couriers = df.shape[0]  # same as number of orders,
    pickup_location = df[["pickup_lat", "pickup_lon"]]
    if not parameters.multi_pickup:
        pickup_location = pickup_location.iloc[0].values
    order_locations = df[["delivery_lat", "delivery_lon"]].values
    order_num_items = df["order_number_items"].values
    weights = df["weight"].values if "weight" in df else None
    order_time_windows = np.int_(
        df[["time_window_start_s", "time_window_end_s"]].values
    )
    # order_num_items = np.append(
    #    [0], np.random.randint(1, max_demand + 1, size=n_orders)
    # )
    order_ids = df["id"] if "id" in df.columns else df["order_id"]

    # TODO: create list of order IDs that are bundled on-the-way
    if "bundle_id" in df.columns:
        bundle_ids = df["bundle_id"].values
    else:
        bundle_ids = None

    if parameters.model_type == ModelType.live:
        order_pickup_time_windows = np.int_(
            df[["pickup_time_window_start_s", "pickup_time_window_end_s"]].values
        )
        return create_data_pu_del_model_from_orders(
            order_locations,
            order_time_windows,
            order_num_items,
            weights,
            pickup_location,
            n_couriers,
            order_pickup_time_windows,
            parameters,
            dist_func=coord_distance,
            order_ids=order_ids,
            do_filter=parameters.filter_infeasible_orders,
            existing_bundle_ids=bundle_ids,
        )
    else:
        return create_data_model_from_orders(
            order_locations,
            order_time_windows,
            order_num_items,
            weights,
            pickup_location,
            n_couriers,
            parameters,
            dist_func=coord_distance,
            order_ids=order_ids,
            do_filter=parameters.filter_infeasible_orders,
            existing_bundle_ids=bundle_ids,
        )
