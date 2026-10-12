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

-- Indoor places (story 9.3, task A53): an unverified list shown for the
-- "Indoor place" setting. Kept apart from places because the categories are
-- not the seven Vicmap activity categories and nothing here is ranked,
-- weathered or turned into a mission.
CREATE TABLE IF NOT EXISTS indoor_places (
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

CREATE INDEX IF NOT EXISTS indoor_place_location_idx ON indoor_places USING GIST (location);
CREATE INDEX IF NOT EXISTS indoor_place_category_idx ON indoor_places (activity_category);


-- Daily request budget for external services, shared by every worker (A41).
CREATE TABLE IF NOT EXISTS api_usage (
    day date NOT NULL,
    service text NOT NULL,
    count integer NOT NULL DEFAULT 0,
    PRIMARY KEY (day, service)
);
