-- Table definitions for the tournament project.
--
-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.

drop view if exists latest_standing;
drop table if exists standing;
drop table if exists players;


create table players (
 player_id serial primary key,
 name text
);

create table standing (
 player_id int references players(player_id),
 totalwins int,
 totalmatchups int
);

create view latest_standing as
select players.player_id, name, totalwins, totalmatchups 
from players 
join standing on players.player_id=standing.player_id
order by totalwins desc; 



