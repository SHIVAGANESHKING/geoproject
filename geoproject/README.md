# Terrain Annotator

**Terrain Annotator** is a professional desktop GIS application designed for the rapid and accurate annotation of digital elevation models (DEMs). It provides a user-friendly interface for classifying various landforms (e.g., hills, valleys, plains, ridges) by drawing polygons directly onto a map. These annotations are crucial for training AI models for geospatial analysis, such as identifying suitable locations for infrastructure projects like helipads in remote areas.

This application is built with PyQt6 and leverages the power of the QGIS core libraries for robust geospatial data handling and visualization.

## Key Features

- **Interactive Map Canvas**: A QGIS-powered map canvas for displaying basemaps and geospatial data layers.
- **DSM/DEM Loading**: Load and display Digital Surface Models (DSMs) and Digital Elevation Models (DEMs) in GeoTIFF format.
- **Polygon Annotation**: Tools for drawing, editing, and selecting polygons to classify terrain features.
- **PostGIS Integration**: Save, load, and manage annotations directly in a PostGIS database for a robust, multi-user workflow.
- **Live Statistics**: Get real-time calculations for area, perimeter, elevation, and slope as you draw.
- **3D Visualization**: View selected terrain areas in a 3D surface plot.
- **Data Export**: Export annotations to common geospatial formats like GeoJSON and Shapefile.

## Architecture Overview

The application follows a modular architecture that separates the user interface, core logic, and data models.

```
┌─────────────────────────────────────────────────────────┐
│                   Main Application Window                │
│  ┌─────────────┐  ┌──────────────────────────────────┐ │
│  │             │  │                                  │ │
│  │  Sidebar    │  │      QGIS Map Canvas            │ │
│  │             │  │   (2D/2.5D Visualization)       │ │
│  │  - Classes  │  │                                  │ │
│  │  - Tools    │  │                                  │ │
│  │  - Stats    │  │                                  │ │
│  │  - Export   │  │                                  │ │
│  │             │  │                                  │ │
│  └─────────────┘  └──────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │     Backend Services          │
            ├───────────────────────────────┤
            │  • PostGIS Connection         │
            │  • GDAL/Rasterio DSM Handler  │
            │  • Geometry Processing        │
            │  • Statistics Calculator      │
            └───────────────────────────────┘
```

## Technology Stack

- **Core Framework**: PyQt6, QGIS Core Libraries
- **Geospatial**: GDAL/OGR, Rasterio, Shapely, Fiona
- **Database**: PostGIS, `psycopg2`, `GeoAlchemy2`
- **3D Visualization**: `PyQtGraph`, `PyVista`
- **Scientific Computing**: NumPy, SciPy

## Project Structure

```
terrain-annotator/
├── main.py                # Application entry point
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── .gitignore             # Git ignore rules
│
├── config/                # Configuration files (DB settings)
├── ui/                    # PyQt6 UI components (windows, widgets)
├── core/                  # Core application logic (DB, DSM processing)
├── tools/                 # QGIS map tools (drawing, editing)
├── models/                # Data models (TerrainClass, Annotation)
├── utils/                 # Utility modules (logging, exporters)
└── tests/                 # Unit and integration tests
```

## Installation and Setup

This is a desktop application with system-level dependencies. Please follow these steps carefully.

### 1. System Dependencies (QGIS and GDAL)

The application requires a working installation of **QGIS (LTR version 3.28+ recommended)** and **GDAL (3.x)**. These cannot be installed via `pip`. The recommended way to install them is using a Conda environment.

**Using Conda (Recommended):**
```bash
# Create a new conda environment
conda create -n terrain-annotator python=3.10

# Activate the environment
conda activate terrain-annotator

# Install QGIS and other geospatial libraries from the conda-forge channel
conda install -c conda-forge qgis gdal rasterio shapely fiona pyqt
```
This will install QGIS and ensure all necessary libraries are available in the environment's path.

### 2. Database Setup (PostGIS)

You need a PostgreSQL server (12+) with the PostGIS extension (3.x) enabled.

1.  Create a database (e.g., `gis_database`).
2.  Enable the PostGIS extension: `CREATE EXTENSION postgis;`
3.  Run the provided SQL scripts to create the `terrain_classes` and `terrain_annotations` tables.

### 3. Environment Variables

The application connects to the PostGIS database using environment variables. Create a `.env` file in the project root or set these variables in your shell:

```
PG_HOST=localhost
PG_PORT=5432
PG_DBNAME=gis_database
PG_USER=your_db_user
PG_PASSWORD=your_db_password
```

### 4. Python Dependencies

Install the remaining Python packages using `pip`:

```bash
# Ensure you are in the correct conda environment
pip install -r requirements.txt
```
*Note: The `requirements.txt` file has the system-level dependencies commented out, as they are handled by Conda.*

## How to Run the Application

With the setup complete, you can run the application from the project root:

```bash
# Activate your conda environment if you haven't already
conda activate terrain-annotator

# Run the main application
python main.py
```

## How to Run Tests

The project includes a suite of unit tests. To run them:

```bash
# Activate your conda environment
conda activate terrain-annotator

# Run pytest from the project root
python -m pytest
```