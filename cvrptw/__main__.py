import argparse
import sys

import pandas as pd

from .graph_routes import graph_locations
from .input_data_generator import create_random_data_model_test
from .quick_vrp import quick_vrp_from_df
from .scheduled_vrp import ScheduledVRP
from .solver import ModelType, graph_routes, run_solve_from_file
from .test_data import get_test_data
from .vrp_parameters import VRPParameters


def try_random(parameters: VRPParameters, n: int, param: int, show_output: bool):
    """Create and solve a random model."""
    data = create_random_data_model_test(
        n_orders=n,
        n_couriers=n,
        parameters=parameters,
        max_dist=4000,
        max_demand=1,
        xparam=param,
    )
    if show_output:
        for k, v in data.items():
            print(f"** {k} **")
            print(v)

    print(f"Running solver ({n} orders)...")
    model = ScheduledVRP(data, parameters)
    res, routes = model.solve()
    if show_output:
        print(res)
        graph_routes(data, routes)

    print("**ROUTES**")
    print(routes)
    print("***")
    return res, routes


def try_all(
    parameters: VRPParameters,
    start_n: int,
    max_n: int,
    out_csv_file: str,
    param: int,
    show_output=False,
):
    """Run random models"""
    df = None
    for n in range(start_n, max_n + 1, 10):
        res, routes = try_random(parameters, n, param, show_output)
        if df is None:
            df = pd.DataFrame.from_records([res])
        else:
            df = df.append(res, ignore_index=True)
        df.to_csv(out_csv_file)


def try_test(parameters: VRPParameters):
    """Solve the test data."""
    data = get_test_data()
    model = ScheduledVRP(data, parameters)
    res, routes = model.solve()
    print(res)
    graph_routes(data, routes)


def get_args():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "-i",
        "--input",
        default=None,
        help="Input csv file, or random example if not set.",
    )
    arg_parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output csv file.",
    )
    arg_parser.add_argument(
        "-n",
        default=10,
        type=int,
        help="Number of orders to test.",
    )
    arg_parser.add_argument(
        "-n-max",
        default=None,
        type=int,
        help="Maximum number of orders to test (iterating from n to n_max).",
    )
    arg_parser.add_argument(
        "-nw",
        "--no-window",
        default=False,
        action="store_true",
        help="Do not use time windows.",
    )
    arg_parser.add_argument(
        "--test",
        default=False,
        action="store_true",
        help="Test",
    )
    arg_parser.add_argument(
        "--model",
        "-m",
        default=None,
        type=str,
        choices=[m.name for m in ModelType],
        help="Model type",
    )
    arg_parser.add_argument(
        "--max-calc-time",
        "-mx",
        default=None,
        type=int,
        help="Maximum calculation time (seconds).",
    )
    arg_parser.add_argument(
        "---courier-cost",
        "-cc",
        default=None,
        type=int,
        help="Courier cost (s) added to every route, the cost of adding an extra courier.",
    )
    arg_parser.add_argument(
        "--track-solver-progress",
        "-tsp",
        default=None,
        action="store_true",
        help="Track the solver cost progress.",
    )
    arg_parser.add_argument(
        "--config",
        "-c",
        default=None,
        type=str,
        help="Json configuration files containing the VRP Parameters.",
    )
    arg_parser.add_argument(
        "--only-show-location-graph",
        "-osl",
        default=False,
        action="store_true",
        help="Only shows the location graphs.",
    )
    return arg_parser.parse_args()


def main():
    args = get_args()
    if args.only_show_location_graph:
        if not args.input:
            print("Error: an input csv file is required to show them on a graph.")
        else:
            df = pd.read_csv(args.input)
            graph_locations(df, args.output, True)
        sys.exit(0)

    if args.config:
        vrp_parameters = VRPParameters.create_from_file(args.config)
        if args.model:
            vrp_parameters.model_type = ModelType[args.model]
    else:
        if args.model is None:
            print("Model type required if no config file is passed.")
            sys.exit(-1)
        model_type = ModelType[args.model]
        vrp_parameters = VRPParameters(model_type)
    if args.max_calc_time:
        vrp_parameters.max_calc_time = args.max_calc_time
    if args.courier_cost:
        vrp_parameters.courier_cost = args.courier_cost
    if args.track_solver_progress:
        vrp_parameters.track_solver_progress = args.track_solver_progress

    print("VRP parameters:")
    print(vrp_parameters.to_str())

    if vrp_parameters.model_type == ModelType.quick:
        df = pd.read_csv(args.input)
        res = quick_vrp_from_df(df, vrp_parameters.max_calc_time, verbose=True)
        print("Results:")
        print(res)
    elif args.input:
        print(f"Input file: {args.input}")
        run_solve_from_file(args.input, args.output, vrp_parameters)
    elif args.test:
        print("TEST")
        try_test(vrp_parameters)
    else:
        start_n = n = args.n
        if args.n_max:
            n = args.n_max
            assert n >= start_n
        param = int(not args.no_window)
        if args.output:
            out_csv = args.output
        else:
            out_csv = "out.csv"

        print(f"Trying from {start_n} up to {n} orders")
        print(f"Output: {out_csv}")
        try_all(vrp_parameters, start_n, n, out_csv, param, True)


if __name__ == "__main__":
    main()
