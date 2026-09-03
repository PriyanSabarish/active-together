CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS places (
    place_id text PRIMARY KEY,
    display_name text NOT NULL,
    activity_category text NOT NULL,
    classification_confidence text,
    lga_name text NOT NULL,
    feature_type text,
    feature_subtype text,
    source_dataset text,
    source_record_id text,
    location geography(Point, 4326) NOT NULL
);

CREATE INDEX IF NOT EXISTS place_location_idx ON places USING GIST (location);
CREATE INDEX IF NOT EXISTS place_lga_idx ON places (lga_name);
CREATE INDEX IF NOT EXISTS place_category_idx ON places (activity_category);