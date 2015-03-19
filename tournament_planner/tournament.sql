-- Table definitions for the tournament project.
--
-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.

drop view latest_standing;
drop table matchups;
drop table standing;
drop table players;


CREATE TABLE players (
 player_id serial PRIMARY KEY,
 name text
);

CREATE TABLE standing (
 player_id INT REFERENCES players(player_id),
 totalWins INT,
 totalMatchups INT
);

CREATE TABLE matchups (
 match_id serial PRIMARY KEY,
 winner INT REFERENCES players(player_id),
 loser INT REFERENCES players(player_id),
 results text
);

CREATE VIEW latest_standing AS
SELECT players.player_id, name, totalwins, totalmatchups 
FROM players 
JOIN standing ON players.player_id=standing.player_id
ORDER BY totalwins DESC; 



