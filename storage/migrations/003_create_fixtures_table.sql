-- Migration: Create fixtures table for Premier League matches
-- Date: 2024-01-15
-- Create fixtures table
CREATE TABLE IF NOT EXISTS fixtures (
    id SERIAL PRIMARY KEY,
    fpl_id INTEGER UNIQUE NOT NULL,
    event INTEGER NOT NULL,
    -- Gameweek number
    team_h_id INTEGER NOT NULL REFERENCES teams(id),
    team_a_id INTEGER NOT NULL REFERENCES teams(id),
    team_h_score INTEGER,
    team_a_score INTEGER,
    finished BOOLEAN DEFAULT FALSE,
    kickoff_time TIMESTAMP NOT NULL,
    difficulty INTEGER,
    team_h_difficulty INTEGER,
    team_a_difficulty INTEGER,
    started BOOLEAN DEFAULT FALSE,
    finished_provisional BOOLEAN DEFAULT FALSE,
    minutes INTEGER DEFAULT 0,
    provisional_start_time BOOLEAN DEFAULT FALSE,
    pulse_id INTEGER,
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);
-- Create indexes
CREATE INDEX IF NOT EXISTS idx_fixtures_fpl_id ON fixtures(fpl_id);
CREATE INDEX IF NOT EXISTS idx_fixtures_event ON fixtures(event);
CREATE INDEX IF NOT EXISTS idx_fixtures_team_h_id ON fixtures(team_h_id);
CREATE INDEX IF NOT EXISTS idx_fixtures_team_a_id ON fixtures(team_a_id);
CREATE INDEX IF NOT EXISTS idx_fixtures_kickoff_time ON fixtures(kickoff_time);
CREATE INDEX IF NOT EXISTS idx_fixtures_finished ON fixtures(finished);
-- Create trigger to update updated_at timestamp
CREATE TRIGGER update_fixtures_updated_at BEFORE
UPDATE ON fixtures FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();