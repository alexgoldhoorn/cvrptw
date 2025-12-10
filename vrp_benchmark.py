import argparse
import os
import shutil
import time
import uuid

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from haversine import Unit, haversine

from cvrptw.solver import run_solve_from_file
from cvrptw.vrp_parameters import ModelType, VRPParameters

DELIVERY_COLS = ["delivery_lat", "delivery_lon"]


def filter_orders(df: pd.DataFrame):
    df_filtered = df.dropna()
    df_filtered = df_filtered.loc[
        df.activation_time_local.dt.date == df.delivery_time_local.dt.date
    ]
    return df_filtered


def create_time_bins(bin_duration=600, start_time=0, end_time=3600 * 24):
    bins = [(i, i + bin_duration - 1) for i in range(start_time, end_time, bin_duration)]
    return pd.IntervalIndex.from_tuples(bins)


def add_bins(df: pd.DataFrame, field, bin_duration=600):
    bins = pd.cut(df[field], bins=create_time_bins(bin_duration))
    df_merged = df.merge(bins, left_index=True, right_index=True, suffixes=("", "_bin"))
    df_merged[f"{field}_bin_mid"] = df_merged[f"{field}_bin"].apply(lambda x: x.mid).astype(float)
    return df_merged


def add_distance(df: pd.DataFrame):
    df["distance"] = df.apply(
        lambda x: haversine(
            (x.pickup_lat, x.pickup_lon), (x.delivery_lat, x.delivery_lon), Unit.METERS
        ),
        axis=1,
    )
    return df


def read_file(file_name, bin_duration=600, do_filter=True, add_meta=True):
    df = pd.read_csv(
        file_name,
        parse_dates=[
            "activation_time_local",
            "pickup_time_local",
            "delivery_time_local",
        ],
    )
    if do_filter:
        df = filter_orders(df)
    if add_meta:
        df = add_bins(df, "pickup_time_s", bin_duration)
        df = add_bins(df, "delivery_time_s", bin_duration)
        df = add_distance(df)
    return df


def show_counts_per_bin(df, field, description):
    counts_per_bin = df.groupby(["store_address_id", field])["order_id"].count()
    counts_per_bin_df = counts_per_bin.reset_index().rename(columns={"order_id": "n"})
    counts_per_bin_df["hour"] = counts_per_bin_df[field] / 3600.0
    sns.lineplot(
        data=counts_per_bin_df,
        x="hour",
        y="n",
        hue="store_address_id",
        palette=["r", "g", "b", "k"],
    )
    plt.ylabel(f"number of {description}")
    plt.show()


def distance_plot(df):
    sns.displot(
        data=df,
        x="distance",
        hue="store_address_id",
        kind="kde",
        palette=["r", "g", "b", "k"],
    )
    plt.xlabel("distance (m)")
    plt.show()


def save_data(df: pd.DataFrame, name):
    df.to_csv(name, index=False)


def filter_data1(df: pd.DataFrame):
    """From 1 store."""
    return df[
        lambda x: (x.delivery_time_s >= 81000)
        & (x.delivery_time_s < 81600)
        & (x.store_address_id == 191768)
    ].copy()


def filter_data2(df: pd.DataFrame):
    """Wider time frame for 1 store."""
    return df[
        lambda x: (x.delivery_time_s >= 80000)
        & (x.delivery_time_s < 85000)
        & (x.store_address_id == 191768)
    ].copy()


def filter_data3(df: pd.DataFrame):
    """Filter more, use other store addresses and set their location to 1 of them
    (i.e. artificially create more orders)"""
    filtered_df = df[lambda x: (x.delivery_time_s >= 80000) & (x.delivery_time_s < 85000)].copy()
    print(filtered_df.groupby("store_address_id")["order_id"].count())
    store_addresses = filtered_df[
        ["store_address_id", "pickup_lat", "pickup_lon"]
    ].drop_duplicates()
    print("First store:", store_addresses.iloc[0])
    # set pickup info to same store
    filtered_df[["store_address_id", "pickup_lat", "pickup_lon"]] = store_addresses.iloc[0]
    # recalc distance
    filtered_df = add_distance(filtered_df)
    filtered_df.distance.describe()
    print("Size:", filtered_df.shape)
    distance_plot(filtered_df)
    filtered_df = filtered_df[lambda x: x.distance <= 5000]
    print("After filtering <5km:")
    distance_plot(filtered_df)
    print("Size:", filtered_df.shape)
    # make time windows much more flexible
    filtered_df["pickup_time_window_end_s"] = filtered_df["time_window_end_s"]
    filtered_df["time_window_start_s"] = filtered_df["pickup_time_window_start_s"]
    return filtered_df


def randomized_data(n: int, df: pd.DataFrame):
    r_df = df.sample(n=n, replace=(n > df.shape[0]))
    # add random noise to delivery loc
    for loc_col in DELIVERY_COLS:
        std = df[loc_col].std()
        r_df[loc_col] += np.random.normal(0, std, size=n)

    if np.any(df[DELIVERY_COLS] > 180) or np.any(df[["delivery_lat", "delivery_lon"]] < -180):
        for loc_col in DELIVERY_COLS:
            df_fil = df[lambda x: (x[loc_col] < -180) | (x[loc_col] > 180)]
            if not df_fil.empty:
                print(df_fil)
    assert not np.any(df[DELIVERY_COLS] > 180) or np.any(
        df[DELIVERY_COLS] < -180
    ), "some locations are out of bound"

    # add time window s
    for tw_col in [
        "pickup_time_window_start_s",
        "pickup_time_window_start_s",
        "time_window_start_s",
        "time_window_end_s",
    ]:
        r_df[tw_col] += np.random.normal(0, 30, size=n)

    r_df = add_distance(r_df)
    assert r_df.shape[0] == n, f"{n} lines expected in the random DF but retrieved {r_df.shape[0]}"

    return r_df


def run_vrp(df: pd.DataFrame, parameters: VRPParameters, save_input_when_fail):
    name = "_temp_input_" + str(uuid.uuid4()) + "_" + parameters.model_type.name
    temp_input_csv_file = name + ".csv"
    save_data(df, temp_input_csv_file)
    assert not df.empty
    output_file = name + "_out"

    results = run_solve_from_file(
        temp_input_csv_file,
        output_file,
        parameters,
        show=False,
        graph=False,
    )

    if save_input_when_fail and results["solver"]["status_code"] != 1:
        error_csv_file = "_" + results["solver"]["status"] + "_" + temp_input_csv_file
        print(
            f"Failed to find a solution {results['solver']['status']}, "
            f"saving as {error_csv_file}"
        )
        shutil.copy(temp_input_csv_file, error_csv_file)

    os.remove(temp_input_csv_file)

    return results


def run_vrp_w_random_data(
    df_base: pd.DataFrame,
    parameters: VRPParameters,
    n: int,
    save_input_when_fail,
):
    df_rand = randomized_data(n, df_base)
    return run_vrp(df_rand, parameters, save_input_when_fail)


def run_diff_nums(
    df_base: pd.DataFrame,
    parameters: VRPParameters,
    order_nums,
    n_repeats,
    save_input_when_fail,
):
    meta_res_list = []
    for n in order_nums:
        for i in range(n_repeats):
            this_meta = {"n_orders": n, "iteration": i}
            try:
                result = run_vrp_w_random_data(
                    df_base,
                    parameters,
                    n,
                    save_input_when_fail,
                )
                meta_res = {
                    **result["solver"],
                    **result.get("meta", {}),
                    **result.get("summary", {}),
                    **result.get("filter", {}),
                }
            except Exception as e:
                print("Exception:", e)
                msg = e.message if hasattr(e, "message") else str(e)
                meta_res = {"status_code": -1, "status": "exception", "exception": msg}

            meta_res_list.append({**this_meta, **meta_res})
            pd.DataFrame(meta_res_list).to_csv("_out_meta_tmp.csv")

    return meta_res_list


def print_results(df_meta: pd.DataFrame):
    pd.set_option("display.max_columns", 50)
    COLS_TO_SHOW = [
        "n_orders",
        "iteration",
        "duration",
        "status_code",
        "n_max_courier",
        "total_time",
        "total_distance",
        "total_cost",
        "total_load",
        "num_vehicles_used",
        "n_filtered",
    ]
    cols = [col for col in COLS_TO_SHOW if col in df_meta.columns]

    if df_meta.shape[0] > 5:
        print(df_meta[cols].describe())
    else:
        print(df_meta[cols])


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "-i",
        "--input",
        default=None,
        required=True,
        help="Input csv file, or random example if not set.",
    )
    arg_parser.add_argument(
        "-o",
        "--output",
        default="out.csv",
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
        default=20,
        type=int,
        help="Maximum number of orders to test (iterating from n to n_max).",
    )
    arg_parser.add_argument(
        "--repeat",
        "-r",
        default=1,
        type=int,
        help="Number of repeats per number of orders",
    )
    arg_parser.add_argument(
        "--model",
        "-m",
        default=ModelType.live.name,
        type=str,
        choices=[m.name for m in ModelType],
        help="Model type",
    )
    arg_parser.add_argument(
        "--max-calc-time",
        "-mx",
        default=10,
        type=int,
        help="Maximum calculation time (seconds).",
    )
    arg_parser.add_argument(
        "-fl",
        "--filter",
        default=False,
        action="store_true",
        help="Filter the data and create the time windows.",
    )
    arg_parser.add_argument(
        "-sf",
        "--save-failed",
        default=False,
        action="store_true",
        help="Save input when failed to solve.",
    )
    args = arg_parser.parse_args()

    print("CVRPTW")
    print("=" * 10)
    print("Input: ", args.input)
    print("Output: ", args.output)
    print(f"n: {args.n} .. {args.n_max}; repeats: {args.repeat}")
    print(f"Max calc time: {args.max_calc_time} s")
    print("Model: ", args.model)

    if args.n > args.n_max:
        print(f"n {args.n} > n-max {args.n_max} is not valid")
        return

    print(f"Reading {args.input}...")
    input_df = read_file(
        args.input, bin_duration=60 * 30, do_filter=args.filter, add_meta=args.filter
    )
    if args.filter:
        input_df = filter_data2(input_df)

    model_type = ModelType[args.model]
    vrp_parameters = VRPParameters(model_type, max_calc_time=args.max_calc_time)

    print("Running benchmark...")
    start_time = time.time()
    meta_results = run_diff_nums(
        input_df,
        vrp_parameters,
        range(args.n, args.n_max + 1),
        args.repeat,
        args.save_failed,
    )
    duration = time.time() - start_time
    print(f"Benchmark finished, took {duration:.2} s")

    df_meta = pd.DataFrame(meta_results)

    print_results(df_meta)

    print()
    print("Status counts:")
    print(df_meta.groupby("status")["status_code"].count())
    print()

    output_csv = args.output if args.output[:-4] == ".csv" else args.output + ".csv"
    print(f"Writing to {output_csv} ...")
    df_meta.to_csv(output_csv)
    print("DONE")


if __name__ == "__main__":
    main()
