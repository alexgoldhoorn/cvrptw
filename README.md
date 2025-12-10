# Capacitated Vehicle Routing Problem with Time Windows (CVRPTW)

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![uv](https://img.shields.io/badge/uv-Package%20Manager-blue)](https://github.com/astral-sh/uv)

A Python implementation of the **Capacitated Vehicle Routing Problem with Time Windows (CVRPTW)** solver, designed for optimizing delivery route planning. This project demonstrates how to use Google OR-Tools to solve real-world vehicle routing problems with various constraints.

## 🎯 Overview

This solver optimizes route planning for multiple delivery orders from a single depot, where orders must be delivered within specified time windows. The system minimizes overall delivery time and the number of vehicles required, while respecting constraints on:

- 🚚 **Vehicle capacity** (weight and item count)
- ⏰ **Delivery time windows**
- 📍 **Maximum travel distance and time**
- 🎯 **Pickup time windows** (for live routing scenarios)

Built with [Google OR-Tools](https://developers.google.com/optimization), this solver supports multiple optimization strategies and vehicle types.

## ✨ Features

### Multiple Solver Modes
- **Scheduled Mode**: Time windows only at delivery locations
- **Live Mode**: Time windows at both pickup and delivery locations
- **Distance Optimization**: Minimize total travel distance
- **Time Optimization**: Minimize total travel time
- **Quick Mode**: Fast approximate solutions

### Capabilities
- Multi-vehicle routing optimization
- Interactive route visualization with Plotly
- MapBox integration for geographic visualization
- Comprehensive benchmarking tools
- Solution validation and verification
- Support for different vehicle types (bicycle, motorbike, car)

## 🚀 Quick Start

### Installation

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync
```

Or use the existing virtual environment:
```bash
source .venv/bin/activate
pip install -e .
```

### Basic Usage

Solve a vehicle routing problem with time windows:

```bash
python -m cvrptw -i tests/demo_orders.csv -o output -m live -mx 10
```

This will:
- Read order data from the CSV file
- Solve using the "live" mode (with pickup and delivery time windows)
- Run for a maximum of 10 seconds
- Generate output JSON and visualization

### Example Output

The solver produces detailed route plans including:
- Optimized vehicle routes
- Time and distance metrics per route
- Delivery sequence with arrival times
- Constraint satisfaction verification
- Interactive visualizations

## 🌍 Real-World Applications

This solver is applicable to various logistics and delivery scenarios:

- **Food Delivery Services**: Optimize multi-restaurant pickup and customer delivery routes
- **E-commerce Last-Mile Delivery**: Plan efficient package delivery routes with time slots
- **Courier Services**: Schedule pickups and deliveries with appointment windows
- **Field Service Operations**: Route technicians to customer locations within appointment times
- **Waste Collection**: Optimize collection routes with time-constrained access points
- **Healthcare Services**: Schedule home healthcare visits with patient availability windows

## 📖 Detailed Usage

### Command Line Interface

Run the solver with various parameters:

```bash
python -m cvrptw -i input.csv -o output -m live -mx 5
```

### Parameters
- `-i`: input file with all the order details;
- `-o`: the output file, stores the VRP as a graph;
- `-m`: model type:
  - `distance`: use distance as cost;
  - `time`: use time as cost;
  - `no_tw`: no time windows constraint at all;
  - `scheduled`: scheduled Multibundling has only a time window on the delivery point;
  - `live`: Live Multibundling is the same as the scheduled version but also has a time window on the picukp location.
- `-mx`: maximum solver time in seconds, will stop the solver.
- `-c`: json config file with the VRP parameters (see [`vrp_parameters`](cvrptw/vrp_parameters.py))

Use the help to get an overview of the options:
```
python -m cvrptw --help
```

### Input
The input CSV file should have the following columns per order:
- `id`: the id of the order,
- `pickup_lat`: pickup latitude,
- `pickup_lon`: pickup longitude,
- `delivery_lat`: delivery latitude,
- `delivery_lon`: delivery longitude,
- `order_number_items`: number of items per order,
- `time_window_start_s`: delivery time window start (s),
- `end_time_window_s`: delivery time window end (s),
- `pickup_time_window_start_s`: pickup time window start (s),
- `pickup_end_time_window_s`: pickup time window end (s).
- `weight`: weight of the total order.

The times should be integers in seconds (relative to the start of the day for example).

### Output
The output of the `ScheduledVRP.solve()` (also `LiveVRP.solve()`) is a dictionary
that is generated in `ScheduledVRP.process_solution_data()` using the OR-tools' results.

It contains the following items:
- _meta_: _number of orders_, _maximum couriers_ and _type of problem_.
- _filter_: how many orders were filtered out due to not passing the constraints.
- _summary_: _total time, distance, cost, load_ and _number of used vehicles_ in the solution.
- _parameters_: parameters used to solve.
- _solver_: _type of solver, duration_, and _status_. The latest indicates if the solver was
able to find a solution.
- _routes_: the solution, which is a list of routes per vehicle:
  - _vehicle_id_
  - _vehicle_capacity_
  - _route_: a list of nodes with all the details (_index, name, location, time window_)
and the metrics (_time, distance_ and _cost_) both from the previous point and accumulated starting
from the depot.

The output can be saved in a json file and shown on the screen.

### Visualization

The solver can generate route visualizations in two modes:

1. **Basic Plotting** (default): Routes plotted on a simple coordinate graph
2. **MapBox Integration** (optional): Routes overlaid on real maps

#### Setting up MapBox (Optional)

For geographic map visualization:

1. Create a free account at [MapBox](https://account.mapbox.com/)
2. Get your access token from your MapBox account dashboard
3. Create a file named `.mapbox_token` in the project root
4. Paste your token into this file

```bash
# Create token file
echo "your_mapbox_token_here" > .mapbox_token
```

**Note**: `.mapbox_token` is gitignored and won't be committed to version control.

When using the maps graph, when going over the nodes it will show detailed information
such as the route, name (order id), location and on the first line several statistics, here legend:
- *T:* time
- *T(acc):* time accumulated (from the depot until that node)
- *D:* distance
- *D(acc):* distance accumulated
- *TW:* time window
- *TW(c):* time window constraint
- *N:* number of items
- *N(acc):* number of items accumulated
- *W:* weight
- *W(acc):* weight accumulated

## Benchmarking
The `vrp_benchmark.py` allows to benchmark the VRP algorithms creating semi-random problems based on an input file
that contains some orders. It then runs the VRP model for different number of orders and with several repetitions.
It outputs the timings with a summary of the results for all runs.

Use the help to get an overview of the options:
```
python vrp_benchmark --help
```

## Code
This section gives a quick overview of the source code.

### `cvrptw`
This contains the main project that does creates the routes based on a list of orders.
- `__main__.py`: main entry point to run the solver from the command line.
- `distance.py`: distance functions.
- `input_data_generator.py`: it creates the input data for the model: _distances_, _travel times_, _costs_, _couriers_, etc.
    The main functions are:
  - `create_data_model_from_csv_file()`: use a csv file with the columns shown in the _input_ section [main function to call].
  - `create_data_model_from_dataframe()`: use a dataframe with the columns shown in the _input_ section
    [called from the previous, selects the previous function to call based on the type].
  - `create_data_model_from_orders()`: create a model for _Scheduled Multibundling_.
  - `create_data_model_pu_del_from_orders()`: create a model for _Live Multibundling_.
- `vrp_model.py`: the abstract `VRPModel` class.
- `scheduled_vrp.py`: the Scheduled VRP model class which implements the model generation and result processing.
- `live_vrp.py`: the Live VRP model class, extends the previous with time windows on the pickup location per order.
- `solver.py`: functions that do all: generating the input data, solving, processing and returning the results.
   The main functions:
  - `run_solve_from_file()`: runs the solver with as input a csv file and the model parameters.
  - `run_solve()`: solves a generated `VRPModel` and returns the result.
  - `graph_routes()`: show the results in a graph.
- `test_data.py`: test data set.
- `utils.py`: some json utility functions.
- `vrp_parameters.py`: contains all the parameters for the model.

### `examples`
This contains a list of (edited) examples of the [OR Tools](https://developers.google.com/optimization/routing) web for VRPs:
- `vrp_ex.py`: a simple [VRP problem](https://developers.google.com/optimization/routing/vrp).
- `vrp_tw_ex.py`: [VRP with time windows problem](https://developers.google.com/optimization/routing/vrptw).
- `vrp_pudel_ex.py`: [VRP pickup-and-delivery problem](https://developers.google.com/optimization/routing/pickup_delivery).
- `vrp_pudel_tw_ex.py`: combines the previous two - VPR with pickup-and-delivery and time windows on both points.
- `vrp_reuse_ex.py`: trying to pass an initial (e.g. previous) solution - i.e. to re-use previous solutions.

### `analysis`
Notebooks to analyse the results and benchmarks.

### Other files
- `order_query_dwh.sql`: query fro the DWH to generate an input for the mutibundling algorithm.

### Code Quality with Pre-commit Hooks

This project uses pre-commit hooks to maintain code quality with Black, isort, and flake8:

```bash
# Install pre-commit hooks
pre-commit install && pre-commit install -t pre-push

# Run manually on all files
pre-commit run --all-files
```

The hooks will automatically format your code with Black and check for issues before each commit.

## Tests
The tests are in [`tests/`](tests/) and the output can be generated with [`run_tests.py`](run_tests.py).

The directory contains test cases in the format:
`{id}_{n_orders}_orders*`.

For each test case there the following files:
- `{id}_{n_orders}_orders_input.csv`: the list of orders and details;
- `{id}_{n_orders}_config_{model_type}.json`: configuration ofr the given model type;
- `{id}_{n_orders}_output_{model_type}.json`: the expected output for the model type.
