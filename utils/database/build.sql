CREATE TABLE IF NOT EXISTS Players (
    uuid VARCHAR(36) NOT NULL PRIMARY KEY UNIQUE,
    discord_id BIGINT NULL UNIQUE,
    name VARCHAR(16) NOT NULL UNIQUE,
    crew_name VARCHAR(16) DEFAULT NULL,
    last_updated TIMESTAMP NOT NULL,
    FOREIGN KEY (crew_name) REFERENCES Crews (name)
);

CREATE TABLE IF NOT EXISTS Crews (
    name VARCHAR(32) NOT NULL PRIMARY KEY UNIQUE,
    captain_uuid VARCHAR(36) NOT NULL UNIQUE,
    role_id BIGINT NULL,
    FOREIGN KEY (captain_uuid) REFERENCES Players (uuid)
);



    