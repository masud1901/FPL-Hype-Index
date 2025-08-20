-- Migration: Create teams table and populate with Premier League teams
-- Date: 2024-01-15
-- Create teams table
CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    fpl_id INTEGER UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    short_name VARCHAR(10) NOT NULL,
    code INTEGER NOT NULL,
    -- Team strength and performance
    strength INTEGER DEFAULT 0,
    strength_overall_home INTEGER DEFAULT 0,
    strength_overall_away INTEGER DEFAULT 0,
    strength_attack_home INTEGER DEFAULT 0,
    strength_attack_away INTEGER DEFAULT 0,
    strength_defence_home INTEGER DEFAULT 0,
    strength_defence_away INTEGER DEFAULT 0,
    -- Current season stats
    played INTEGER DEFAULT 0,
    win INTEGER DEFAULT 0,
    loss INTEGER DEFAULT 0,
    draw INTEGER DEFAULT 0,
    points INTEGER DEFAULT 0,
    position INTEGER DEFAULT 0,
    -- Goals
    goals_for INTEGER DEFAULT 0,
    goals_against INTEGER DEFAULT 0,
    goal_difference INTEGER DEFAULT 0,
    -- Advanced metrics
    xg_for FLOAT DEFAULT 0.0,
    xg_against FLOAT DEFAULT 0.0,
    xg_difference FLOAT DEFAULT 0.0,
    -- Form and momentum
    form VARCHAR(10) DEFAULT '',
    unbeaten INTEGER DEFAULT 0,
    winless INTEGER DEFAULT 0,
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Create indexes
CREATE INDEX IF NOT EXISTS idx_teams_fpl_id ON teams(fpl_id);
CREATE INDEX IF NOT EXISTS idx_teams_name ON teams(name);
CREATE INDEX IF NOT EXISTS idx_teams_short_name ON teams(short_name);
CREATE INDEX IF NOT EXISTS idx_teams_position ON teams(position);
-- Add team_id column to players table if it doesn't exist
DO $$ BEGIN IF NOT EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_name = 'players'
        AND column_name = 'team_id'
) THEN
ALTER TABLE players
ADD COLUMN team_id INTEGER REFERENCES teams(id);
CREATE INDEX IF NOT EXISTS idx_players_team_id ON players(team_id);
END IF;
END $$;
-- Insert current Premier League teams (2024/25 season)
INSERT INTO teams (
        fpl_id,
        name,
        short_name,
        code,
        strength,
        position,
        created_at,
        updated_at
    )
VALUES (
        1,
        'Arsenal',
        'ARS',
        3,
        4,
        0,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    ),
    (
        2,
        'Aston Villa',
        'AVL',
        7,
        3,
        0,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    ),
    (
        3,
        'Bournemouth',
        'BOU',
        91,
        2,
        0,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    ),
    (
        4,
        'Brentford',
        'BRE',
        94,
        3,
        0,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    ),
    (
        5,
        'Brighton',
        'BHA',
        36,
        3,
        0,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    ),
    (
        6,
        'Burnley',
        'BUR',
        90,
        2,
        0,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    ),
    (
        7,
        'Chelsea',
        'CHE',
        8,
        4,
        0,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    ),
    (
        8,
        'Crystal Palace',
        'CRY',
        31,
        3,
        0,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    ),
    (
        9,
        'Everton',
        'EVE',
        11,
        3,
        0,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    ),
    (
        10,
        'Fulham',
        'FUL',
        54,
        3,
        0,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    ),
    (
        11,
        'Liverpool',
        'LIV',
        14,
        4,
        0,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    ),
    (
        12,
        'Luton',
        'LUT',
        102,
        2,
        0,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    ),
    (
        13,
        'Manchester City',
        'MCI',
        43,
        5,
        0,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    ),
    (
        14,
        'Manchester United',
        'MUN',
        1,
        4,
        0,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    ),
    (
        15,
        'Newcastle',
        'NEW',
        4,
        4,
        0,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    ),
    (
        16,
        'Nottingham Forest',
        'NFO',
        17,
        3,
        0,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    ),
    (
        17,
        'Sheffield United',
        'SHU',
        49,
        2,
        0,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    ),
    (
        18,
        'Tottenham',
        'TOT',
        6,
        4,
        0,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    ),
    (
        19,
        'West Ham',
        'WHU',
        21,
        3,
        0,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    ),
    (
        20,
        'Wolves',
        'WOL',
        39,
        3,
        0,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    ) ON CONFLICT (fpl_id) DO
UPDATE
SET name = EXCLUDED.name,
    short_name = EXCLUDED.short_name,
    code = EXCLUDED.code,
    strength = EXCLUDED.strength,
    updated_at = CURRENT_TIMESTAMP;
-- Update players table to link with teams
UPDATE players
SET team_id = teams.id
FROM teams
WHERE players.team = teams.name;
-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column() RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = CURRENT_TIMESTAMP;
RETURN NEW;
END;
$$ language 'plpgsql';
CREATE TRIGGER update_teams_updated_at BEFORE
UPDATE ON teams FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();