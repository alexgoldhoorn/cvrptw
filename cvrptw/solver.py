from .distance_vrp import DistanceVRP
from .graph_routes import graph_routes
from .input_data_generator import create_data_model_from_csv_file
from .live_vrp import LiveVRP
from .notw_vrp import NoTWVRP
from .scheduled_vrp import ScheduledVRP
from .time_vrp import TimeVRP
from .utils import save_as_json, show_dict
from .vrp_model import VRPModel
from .vrp_parameters import ModelType, VRPParameters


def model_factory(data, parameters: VRPParameters):
    """Create a VPR model based on the type."""
    if parameters.model_type == ModelType.distance:
        return DistanceVRP(data, parameters)
    elif parameters.model_type == ModelType.time:
        return TimeVRP(data, parameters)
    elif parameters.model_type == ModelType.scheduled:
        return ScheduledVRP(data, parameters)
    elif parameters.model_type == ModelType.live:
        return LiveVRP(data, parameters)
    elif parameters.model_type == ModelType.no_tw:
        return NoTWVRP(data, parameters)
    raise Exception(f"Unknown solver type {parameters.model_type.name}")


def run_solve(model: VRPModel, graph=True, show=True, out_file=None):
    """
    Run the solver.
    Args:
        model:  the VRP model
        graph: create the graph
        show: show the result on screen
        out_file: output file
    """
    if show:
        show_dict(model.data, header="INPUT DATA")

    print(f"Running solver ({model.n_orders} orders; {model.n_nodes} nodes)...")
    result = model.solve()

    if show:
        show_dict(result, header="SOLUTION")
    if graph and "routes" in result:
        graph_routes(model.data, result["routes"], out_file, show)

    return result


def run_solve_from_file(
    file_name: str,
    out_file: str,
    parameters: VRPParameters,
    show=True,
    graph=True,
):
    """
    Run and solve the problem from a file.
    Args:
        file_name: csv file name
        out_file: output file name
        parameters: VRP parameters
        show: show the output on the screen
        graph: create the graph file
    """
    data, df_in = create_data_model_from_csv_file(
        file_name,
        parameters,
        return_df=True,
    )
    model = model_factory(data, parameters)
    result = run_solve(model, out_file=out_file, show=show, graph=graph)
    if out_file is not None:
        out_json_file = out_file if out_file[-5:] == ".json" else out_file + ".json"
        save_as_json(result, out_json_file)
    return result
