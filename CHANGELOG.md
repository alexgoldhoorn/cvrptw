# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-12-10

### Added
- Open source release preparation
- MIT License
- Comprehensive README with badges and examples
- Real-world applications section
- Quick start guide
- Contributing guidelines (CONTRIBUTING.md)
- Changelog documentation
- Example test data files
- Assets directory for visualizations

### Changed
- Removed company-specific references and documentation links
- Updated author information to be vendor-neutral
- Improved .gitignore for demo project structure
- Enhanced documentation for public GitHub release

### Documentation
- Added detailed usage examples
- Improved installation instructions
- Added real-world use case scenarios
- Created contributing guidelines
- Added code of conduct principles

## [0.1.0] - Initial Development

### Added
- Core CVRPTW solver implementation
- Multiple solver variants:
  - Scheduled multibundling (delivery time windows)
  - Live multibundling (pickup and delivery time windows)
  - Distance-based optimization
  - Time-based optimization
  - No time window variant
  - Quick solver mode
- Google OR-Tools integration
- Distance and time matrix calculations
- Haversine distance calculations for geographic coordinates
- Vehicle capacity constraints (items and weight)
- Time window constraints
- Visualization capabilities:
  - Matplotlib graphs
  - Plotly interactive visualizations
  - MapBox integration for geographic plotting
- Command-line interface
- Configuration file support (JSON)
- Benchmarking tools
- Solution verification
- Test cases with expected outputs
- Jupyter notebook analysis tools
- Pre-commit hooks for code quality
- Support for different vehicle types (bicycle, motorbike, car)

### Features
- Multi-vehicle routing optimization
- Pickup and delivery problem solving
- Time window constraint handling
- Capacity constraint handling
- Cost-based optimization
- Solution warm-start/reuse capability
- Infeasible order filtering
- Detailed route metrics (time, distance, cost, load)
- Comprehensive logging and debugging output

[0.2.0]: https://github.com/alexgoldhoorn/cvrptw/releases/tag/v0.2.0
[0.1.0]: https://github.com/alexgoldhoorn/cvrptw/releases/tag/v0.1.0
