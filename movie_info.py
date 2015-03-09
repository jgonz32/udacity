'''
Created on Mar 4, 2015

@author: jgonz2
'''
class Movie:
    
    #init the Movie object
    def __init__(self, movie_details=None):
        self.title=movie_details['title']
        self.year=movie_details['year']
        self.poster_image_url=movie_details['poster_image_url']
        self.trailer_youtube_url=movie_details['trailer_youtube_url']
        self.summary=movie_details["summary"]
        self.stars=movie_details["stars"]
        self.rating=movie_details["rating"]
       