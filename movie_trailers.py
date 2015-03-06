'''
Created on Mar 4, 2015

@author: jgonz2
'''

import json
import fresh_tomatoes
import movie_info

# instantiate and return list of Movie objects using data from source
def get_movie_objects_list(movies_data):
    movies=[]
    
    for movie in movies_data["movies"]:
        #pass
        #print(movie)
        movie_obj=movie_info.Movie(movie)
        movies.append(movie_obj)
    
    return movies

#open browser to show available movie trailers
def show_trailers(movies_list):
    fresh_tomatoes.open_movies_page(movies_list)
    

# get movies data from json file
def get_movies_data_from_json_file(file):
    
    with open(file) as movies_file:
        movies_info=movies_file.read()
        movies=json.loads(movies_info)

    return movies


def  main():
    
    movies_file_name="movies.json"    
    movies_data_from_file= get_movies_data_from_json_file(movies_file_name)
    
    show_trailers(get_movie_objects_list(movies_data_from_file))
    
        
if __name__ == '__main__':
    main()