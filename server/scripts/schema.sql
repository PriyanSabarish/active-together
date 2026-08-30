CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS place (
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

CREATE INDEX IF NOT EXISTS place_location_idx ON place USING GIST (location);
CREATE INDEX IF NOT EXISTS place_lga_idx ON place (lga_name);
CREATE INDEX IF NOT EXISTS place_category_idx ON place (activity_category);