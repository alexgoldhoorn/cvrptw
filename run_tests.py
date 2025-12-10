"""
This script can be used to solve the VRP problems for the test cases (in tests/) for
the different configurations. It stores the results in the same directory, using the
filename as the config file name.

Format of file names:
- Input: `{number}_{name}_input.csv`
- Config: `{number}_{name}_config_{config_name}.json`
- Output:  `{number}_{name}_output_{config_name}.json`

Where `number` has 3 digits. And `config_name` is the model type used.
"""

import argparse
import os
import re
from glob import glob

from cvrptw.solver import run_solve_from_file
from cvrptw.vrp_parameters import VRPParameters


def run_vrp(input_data_csv: str, config_file: str, output_file: str, save_graph: bool):
    """Run the VRP solver for a certain input and config and store the result to the output file."""
    print(f"Solving VRP {input_data_csv} with config {config_file} and save to {output_file}...")
    vrp_parameters = VRPParameters.create_from_file(config_file)
    run_solve_from_file(input_data_csv, output_file, vrp_parameters, show=False, graph=save_graph)
    print("=" * 30)
    print()


def run_for_config(input_data_csv: str, config_file: str, output_dir: str, save_graph: bool):
    """Run the VRP for an input and a config and create the output file name based
    on the config file name. Then it runs the VRP solver and stores the output."""
    m = re.match(r".*(\d{3}_.*)_config_(.*)\.json", config_file)
    if m is None:
        print("Unknown config file name format:", config_file)
        return
    output_file = os.path.join(output_dir, f"{m[1]}_output_{m[2]}")
    run_vrp(input_data_csv, config_file, output_file, save_graph)


def run_all_configs(input_data_csv: str, output_dir: str, save_graph: bool):
    """Run the VRP solver for all configuration of a certain input."""
    m = re.match(r".*(\d{3}_.*)_input\.csv", input_data_csv)
    if m is None:
        print("Unknown input file name format:", input_data_csv)
        return
    file_start = m[1]
    for config_file in glob(f"tests/{file_start}_config_*.json"):
        run_for_config(input_data_csv, config_file, output_dir, save_graph)


def run_all(output_dir: str, save_graph: bool):
    """Run the VRP solver for all problems and configs in the tests directory."""
    for input_file in glob("tests/???_*_input.csv"):
        run_all_configs(input_file, output_dir, save_graph)


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "-i",
        "--input",
        default=None,
        help="Input csv file.",
    )
    arg_parser.add_argument(
        "-c",
        "--config",
        default=None,
        help="Config file",
    )
    arg_parser.add_argument(
        "-o",
        "--output",
        default="tests/",
        help="Output dir",
    )
    arg_parser.add_argument(
        "-g",
        "--graph",
        default=False,
        action="store_true",
        help="Save graph to file.",
    )
    args = arg_parser.parse_args()

    if args.input:
        if args.config:
            run_for_config(args.input, args.config, args.output, args.graph)
        else:
            run_all_configs(args.input, args.output, args.graph)
    elif args.config:
        print("Also set the test case when setting the configuration.")
    else:
        run_all(args.output, args.graph)


if __name__ == "__main__":
    main()
