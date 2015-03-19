#!/usr/bin/env python
# 
# tournament.py -- implementation of a Swiss-system tournament
#

import psycopg2
import sys

def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""
    return psycopg2.connect("dbname=tournament")


def delete_from(table_name):
    ''' Execute delete command on table name passed as argument'''
    DELETE = "DELETE from {};".format(table_name)
    
    try:
        database_connection = connect()
        cursor = database_connection.cursor()
        cursor.execute(DELETE)
        database_connection.commit()
    except:
        print("Error.")
    finally:
        database_connection.close()

def deleteMatches():
    '''Remove all the match records from the database.'''
    delete_from("matchups")
    

def deletePlayers():
    """Remove all the player records from the database.""" 
    delete_from("standing")
    delete_from("players")

def countPlayers():
    """Returns the number of players currently registered."""
    
    COUNT_PLAYERS_QUERY = 'SELECT COUNT(*) FROM players;'
    
    result=""
    try:
        database_connection = connect()
        cursor = database_connection.cursor()
        cursor.execute(COUNT_PLAYERS_QUERY)
        result = cursor.fetchone()[0]
       
    except:
        print("Error.")
    finally:
        database_connection.close()
    
    return result


def registerPlayer(name):
    """Adds a player to the tournament database.
  
    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)
  
    Args:
      name: the player's full name (need not be unique).
    """
    INSERT_PLAYER_QUERY = 'INSERT INTO players (name) values(%s) RETURNING player_id;'
    ADD_PLAYER_TO_STANDING = 'INSERT INTO standing (player_id, totalwins, totalmatchups) values(%s,%s,%s);'
    
    player_id=0
    try:
        database_connection = connect()
        cursor = database_connection.cursor()
        cursor.execute(INSERT_PLAYER_QUERY, (name,))
          
        '''get player id  of inserted player '''
        player_id= cursor.fetchone()[0]
        
        '''add player to standing table'''    
        cursor.execute(ADD_PLAYER_TO_STANDING, (player_id,0,0,))
      
        database_connection.commit()
    except:
        print("Error.")
    finally:
        database_connection.close()
    
    #return result


def playerStandings():
    """Returns a list of the players and their win records, sorted by wins.

    The first entry in the list should be the player in first place, or a player
    tied for first place if there is currently a tie.

    Returns:
      A list of tuples, each of which contains (id, name, wins, matches):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        wins: the number of matches the player has won
        matches: the number of matches the player has played
    """
    QUERY_STANDING = 'SELECT * FROM latest_standing'
    
    results=[]
    try:
        database_connection = connect()
        cursor = database_connection.cursor()
        
        '''query standing table using latest_standing view. The view return the standung in descending order of wins '''
        cursor.execute(QUERY_STANDING)
        results = cursor.fetchall()        
    except:
        print("Error")
    finally:
        database_connection.close()
    
    return results


def reportMatch(winner, loser):
    """Records the outcome of a single match between two players.

    Args:
      winner:  the id number of the player who won
      loser:  the id number of the player who lost
    """
    INSERT_MATCH_RESULT = 'INSERT INTO matchups (winner, loser) values(%s,%s)'
    UPDATE_WINNER_STANDING = 'UPDATE standing set totalwins = totalwins + 1, totalmatchups= totalmatchups + 1 where player_id=%s'
    UPDATE_LOSER_STANDING = 'UPDATE standing set totalmatchups = totalmatchups + 1 where player_id=%s'
    
    try:
        database_connection = connect()
        cursor = database_connection.cursor()
        INSERT_RESULT=cursor.mogrify(INSERT_MATCH_RESULT,(winner, loser))
        cursor.execute(INSERT_RESULT)
        
        #after reporting the result update the standing for each player
        cursor.execute(UPDATE_WINNER_STANDING, (winner,))
        cursor.execute(UPDATE_LOSER_STANDING, (loser,))
        database_connection.commit()

    except:
        print("Error.")
    finally:
        database_connection.close()
 
def swissPairings():
    """Returns a list of pairs of players for the next round of a match.
  
    Assuming that there are an even number of players registered, each player
    appears exactly once in the pairings.  Each player is paired with another
    player with an equal or nearly-equal win record, that is, a player adjacent
    to him or her in the standings.
  
    Returns:
      A list of tuples, each of which contains (id1, name1, id2, name2)
        id1: the first player's unique id
        name1: the first player's name
        id2: the second player's unique id
        name2: the second player's name
    """
    
    '''query standing table using latest_standing view. The view return the standung in descending order of wins '''
    QUERY_STANDING = 'SELECT * FROM latest_standing'
    
    pairings=[]
    try:
        database_connection = connect()
        cursor = database_connection.cursor()
        cursor.execute(QUERY_STANDING)
        results = cursor.fetchall()

        pairings = [ (results[i][0],results[i][1],results[i+1][0],results[i+1][1]) for i in range(0,len(results),2) ]

        print pairings
    except:
        print("Error.")
    finally:
        database_connection.close()
    
    return pairings


