# Active Together API

An intelligent, spatial-aware recommendation backend built with **FastAPI**, **PostgreSQL/PostGIS**, and **SQLAlchemy**. The application curates and generates multi-activity time-budgeted itineraries ("combos") by fusing real-time environmental context with high-performance geospatial queries.

---

## Architecture & Tech Stack

* **Framework:** FastAPI (Async support, automatic OpenAPI/Swagger documentation)
* **Database & GIS:** PostgreSQL hosted on Render with **PostGIS** extension (`geography` types, GiST spatial indexing)
* **ORM & Driver:** SQLAlchemy 2.0 with `pg8000`
* **Data Validation:** Pydantic v2
* **External Integration:** Weather context microservice integration

---

## Core Data-Driven Features

1. **Spatial Indexing via PostGIS:** Uses `ST_DWithin` and spatial tree indices (`GiST`) to perform sub-second radius searches ($3$, $5$, or $10\text{ km}$) without full-table scans.
2. **Geodetic Distance Calculations:** Evaluates true physical distance over the earth's curvature rather than flat 2D grid math by casting points to PostGIS `geography` types.
3. **Administrative Geofencing:** Dynamically validates and restricts business logic to designated operational pilot Local Government Areas (`Melbourne`, `Monash`, `Melton`).
4. **Contextual Environmental Fusion:** Blends real-time meteorological metrics into the recommendation pipeline to score or suppress activities based on weather suitability.

---

## API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| **GET** | `/health` | Returns application status, name, and active environment. |
| **GET** | `/data/places` | Queries PostGIS to fetch candidate venues within a specified radius (`lat`, `lon`, `radius_km`). |
| **GET** | `/data/context` | Fetches live weather metrics for a coordinate point. |
| **POST** | `/recommendations` | Validates pilot boundaries, checks weather context, and generates multi-activity combos based on time budgets. |

---

