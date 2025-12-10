import os.path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px


def use_px_mapbox():
    return os.path.exists(".mapbox_token")


def graph_routes(data: dict, routes: list, out_file=None, show=True):
    """
    Plot the found routes in a graph and save the image.
    Args:
        data:   input model (dictionary created by input_data_generator)
        routes: list of routes (generated solution)
        out_file: output file (optional)
        show: show the graph on screen (otherwise save only)
    """
    if not show and out_file is None:
        print("Not showing a graph (show=False and no output file)")
        return

    if use_px_mapbox():
        graph_routes_px(data, routes, out_file, show)
    else:
        graph_routes_pyplot(data, routes, out_file, show)


def routes_to_dataframe(routes: list) -> pd.DataFrame:
    data_rows = []
    for vehicle in routes:
        route = vehicle["route"]
        for i, node in enumerate(route):
            if i > 0 and (node["location"] == route[0]["location"]).all():
                continue

            time_window = node["time_window"]
            if len(time_window) == 0 or node["time_start"] is None:
                tw_str = ""
            else:
                tw_str = f""",TW:{node['time_start']}-{node['time_end']},
TW(c):{time_window[0]}-{time_window[1]}"""
            capacity = ""
            if "load" in node and node["load_accumulated"] > 0:
                capacity += f" N:{node['load']} N(acc):{node['load_accumulated']}"
            if "weight" in node and node["weight_accumulated"] > 0:
                capacity += f" W:{node['weight']} W(acc):{node['weight_accumulated']}"

            row = {
                "route": vehicle["vehicle_id"],
                "lat": node["location"][0],
                "lon": node["location"][1],
                "name": node["node_name"],
                "description": f"""T:{node['time']}
T(acc):{node['time_accumulated']}
D:{node['distance']}
D(acc):{node['distance_accumulated']}{tw_str}{capacity}""",
            }

            data_rows.append(row)
    return pd.DataFrame(data_rows)


def px_set_mapbox_access_token():
    """Set the Mapbox access token, required to use maps."""
    px.set_mapbox_access_token(open(".mapbox_token").read())


def graph_routes_px(data: dict, routes: list, out_file=None, show=True):
    """
    Plot the found routes in a graph on a map and save the image.
    Args:
        data:   input model (dictionary created by input_data_generator)
        routes: list of routes (generated solution)
        out_file: output file (optional)
        show: show the graph on screen (otherwise save only)
    """
    if "locations" not in data:
        print("No locations in the data")
        return

    px_set_mapbox_access_token()
    df = routes_to_dataframe(routes)
    fig = px.line_mapbox(
        df,
        lat="lat",
        lon="lon",
        color="route",
        text="name",
        hover_name="description",
        zoom=12,
    )

    if out_file:
        fig.write_image(out_file + ".png")
    if show:
        fig.show()


def graph_routes_pyplot(data: dict, routes: list, out_file=None, show=True):
    """
    Plot the found routes in a graph and save the image.
    Args:
        data:   input model (dictionary created by input_data_generator)
        routes: list of routes (generated solution)
        out_file: output file (optional)
        show: show the graph on screen (otherwise save only)
    """
    if "locations" not in data:
        print("No locations in the data")
        return

    locs = np.array(data["locations"])
    plt.scatter(locs[:, 0], locs[:, 1])
    plt.xlabel("latitude")
    plt.ylabel("longitude")

    for vehicle in routes:
        route = vehicle["route"]
        locations = [n["location"] for n in route]
        x = [loc[0] for loc in locations]
        y = [loc[1] for loc in locations]

        if (locations[0] == locations[-1]).all():
            x = x[:-1]
            y = y[:-1]

        plt.plot(x, y)

    plt.scatter(locs[0, 0], locs[0, 1], color="r")

    if locs.shape[0] < 15:
        i = 0
        for row in locs:
            if i == 0:
                i += 1
                continue
            plt.text(row[0], row[1], str(i))
            i += 1

    if out_file:
        plt.savefig(out_file + ".png")
    if show:
        plt.show()


def extract_locations_from_orders_df(input_df: pd.DataFrame) -> pd.DataFrame:
    """Return a DataFrame with only the locations and the names."""
    pickup_df = input_df[["pickup_lat", "pickup_lon"]].drop_duplicates()
    assert pickup_df.shape[0] == 1

    pickup_df = pickup_df.rename(
        columns={"pickup_lat": "lat", "pickup_lon": "lon"}
    ).assign(name="pickup", type="pickup")
    delivery_df = (
        input_df[["delivery_lat", "delivery_lon", "order_id"]]
        .rename(
            columns={"delivery_lat": "lat", "delivery_lon": "lon", "order_id": "name"}
        )
        .assign(type="delivery")
    )
    return pd.concat([pickup_df, delivery_df], ignore_index=True)


def graph_locations(input_df: pd.DataFrame, out_file=None, show=True):
    """
    Plot the locations on a graph.
    Args:
        input_df:   data frame with the order details
        out_file: output file (optional)
        show: show the graph on screen (otherwise save only)
    """
    if not show and out_file is None:
        print("Not showing a graph (show=False and no output file)")
        return

    df = extract_locations_from_orders_df(input_df)

    if use_px_mapbox():
        graph_locations_px(df, out_file, show)
    else:
        graph_locations_pyplot(df, out_file, show)


def graph_locations_px(df: pd.DataFrame, out_file=None, show=True):
    """
    Plot the locations on a map and save the image.
    Args:
        df:   data with locations
        out_file: output file (optional)
        show: show the graph on screen (otherwise save only)
    """
    px_set_mapbox_access_token()
    fig = px.scatter_mapbox(
        df,
        lat="lat",
        lon="lon",
        text="name",
        color="type",
        zoom=12,
    )

    if out_file:
        fig.write_image(out_file + ".png")
    if show:
        fig.show()


def graph_locations_pyplot(df: pd.DataFrame, out_file=None, show=True):
    """
    Plot the locations on a graph and save the image.
    Args:
        df:  data with locations
        out_file: output file (optional)
        show: show the graph on screen (otherwise save only)
    """
    plt.scatter(
        df.loc[df.type == "delivery", "lat"],
        df.loc[df.type == "delivery", "lon"],
        color="blue",
        label="delivery",
    )
    plt.scatter(
        df.loc[df.type == "pickup", "lat"],
        df.loc[df.type == "pickup", "lon"],
        color="red",
        label="pickup",
    )
    plt.xlabel("latitude")
    plt.ylabel("longitude")

    if out_file:
        plt.savefig(out_file + ".png")
    if show:
        plt.show()
