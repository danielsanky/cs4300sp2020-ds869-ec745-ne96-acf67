from . import *  
from app.irsystem.models.helpers import *
from app.irsystem.models.helpers import NumpyEncoder as NumpyEncoder
import numpy as np 
import pandas as pd 
import collections
import random 

@irsystem.route('/', methods=['GET'])
def start():
    return render_template('index.html')


@irsystem.route('/back/', methods=['POST'])
def back():
    return render_template('index.html')

@irsystem.route('/submit/', methods=['POST', 'GET'])
def recommender():
    
    podcast_query = request.args.getlist("all-interests")
    movie_query = request.args.getlist("all-movies")
    music_query = request.args.getlist("all-music")
    form_data = request.args.to_dict()

    if music_query!=[]:
        song=recs(genre_to_music, music_query, form_data)
    else:
        song=["We can't recommend you a song, since you didn't select any genres!"]

    if podcast_query!=[]:
        podcast=recs(final_dict, podcast_query, form_data)
    else:
        podcast=["We can't recommend you a podcast, since we don't know your interests!"]
        
    if movie_query!=[]:
        movie=recs(genre_to_movie, movie_query, form_data)
    else: 
        movie=["We can't recommend you a movie, since we don't know what genres you like!"]

    return render_template('results.html', podcast=podcast, movie=movie, song=song, test=form_data)

#load data
resp = pd.read_csv("young-people-survey/responses.csv")
podcasts=pd.read_csv("young-people-survey/df_popular_podcasts.csv")
movies=pd.read_csv("young-people-survey/MovieGenre.csv")
music=pd.read_csv("young-people-survey/SpotifyFeatures.csv")
genre_IDs=[['1311', 'News & Politics'], ['26', 'Podcasts'], ['1479', 'Social Sciences'], ['1315', 'Science & Medicine'], ['1324', 'Society & Culture'], ['1302', 'Personal Journals'], ['1469', 'Language Courses'], ['1304', 'Education'], ['1320', 'Places & Travel'], ['1416', 'Higher Education'], ['1465', 'Professional'], ['1316', 'Sports & Recreation'], ['1303', 'Comedy'], ['1305', 'Kids & Family'], ['1439', 'Christianity'], ['1314', 'Religion & Spirituality'], ['1444', 'Spirituality'], ['1309', 'TV & Film'], ['1462', 'History'], ['1310', 'Music'], ['1478', 'Medicine'], ['1321', 'Business'], ['1412', 'Investing'], ['1420', 'Self-Help'], ['1307', 'Health'], ['1481', 'Alternative Health'], ['1417', 'Fitness & Nutrition'], ['1467', 'Amateur'], ['1480', 'Software How-To'], ['1318', 'Technology'], ['1448', 'Tech News'], ['1456', 'Outdoor'], ['1477', 'Natural Sciences'], ['1301', 'Arts'], ['1454', 'Automotive'], ['1323', 'Games & Hobbies'], ['1438', 'Buddhism'], ['1443', 'Philosophy'], ['1401', 'Literature'], ['1402', 'Design'], ['1410', 'Careers'], ['1470', 'Training'], ['1413', 'Management & Marketing'], ['1306', 'Food'], ['1406', 'Visual Arts'], ['1446', 'Gadgets'], ['1468', 'Educational Technology'], ['1405', 'Performing Arts'], ['1460', 'Hobbies'], ['1471', 'Business News'], ['1404', 'Video Games'], ['1450', 'Podcasting'], ['1473', 'National'], ['1325', 'Government & Organizations'], ['1461', 'Other Games'], ['1466', 'College & High School'], ['1459', 'Fashion & Beauty'], ['1476', 'Non-Profit'], ['1415', 'K-12'], ['1455', 'Aviation'], ['1464', 'Other'], ['1421', 'Sexuality'], ['1472', 'Shopping'], ['1475', 'Local'], ['1441', 'Judaism'], ['1440', 'Islam'], ['1474', 'Regional'], ['1463', 'Hinduism']]


# Better organize the id vs name of genre
dict_pod={int(id[0]):id[1] for id in genre_IDs }

# {Genre ID:NAMES OF PODCAST} 
genre_to_podcast={key:[] for key in dict_pod }
for item in podcasts.index:
    array=podcasts["Genre IDs"][item][1:-1].split(',')
    array=[int(array[i].replace('\'', '').strip('\'')) for i in range(len(array))]
    for j in range(len(array)):
        genre_to_podcast[array[j]].append(podcasts["Name"][item])
#final_dict={key.lower():value for key,value in final_dict}
final_dict={list(dict_pod.values())[p]:list(genre_to_podcast.values())[p] for p in range(len(genre_to_podcast.keys()))}
final_dict = dict((k.lower(), v) for k, v in final_dict.items()) 

#MAKE MOVIE DICTIONARY
genre_to_movie={}
for i in range(len(movies)):
    line=str(movies["Genre"][i])
    for genre in line.split("|"):
        genre=genre.lower()
        if genre in genre_to_movie:
            genre_to_movie[genre].append(movies["Title"][i])
        else: 
            genre_to_movie[genre]=[movies["Title"][i]]

#MAKE MUSIC DICTIONARY
genre_to_music={}
for i in range(len(music)):
    genre=music['genre'][i]
    genre=genre.lower()
    if genre in genre_to_music:
            genre_to_music[genre].append(music['track_name'][i]+" by "+music['artist_name'][i])
    else:
            genre_to_music[genre]=[music['track_name'][i]+ " by "+music['artist_name'][i]]


#MAKE CORRELATION MATRIX
music_resp=resp.iloc[:, :19]
movie_resp=resp.iloc[:, 19:31]
hobbies_resp=resp.iloc[:, 31:63]
personality_resp=resp.iloc[:, [79, 80, 105, 106, 109, 110, 113, 129, 132]]
demographics_resp=resp.iloc[:, [140, 144, 146, 147]]

final_mat=pd.concat([music_resp, movie_resp, hobbies_resp, personality_resp, demographics_resp], axis=1)
final_mat=final_mat.rename(columns={"New environment": "adapt", "Socializing": "meeting-people", "Waiting":"patient", "Number of friends": "friends", "Workaholism": "study", "Thinking ahead": "perspectives", "Charity": "charity", "Interests or hobbies": "differ-hobbies"})

corr_mat=pd.DataFrame.corr(final_mat)
corr_mat.columns = map(str.lower, corr_mat.columns)
corr_mat.index = map(str.lower, corr_mat.index)


def recs(genre_dict, genre_query, corr_query):
    """Returns a list of podcasts based on interests user clicked in form
    Params: {query: list of genre names, genre_dict: dictionary that maps genre to titles}
    Returns: list of titles and scores
    """
    #query is an array of genre_names
    #corr_query is a dictionary of radio button responses like {'all-music': 'R&B', 'all-movies': 'Horror', 'all-interests': 'Social Sciences', 'gender': 'female', 'education': 'no'}
    corr_query.pop('all-interests', None)
    corr_query.pop('all-movies', None)
    corr_query.pop('all-music', None)

    genre_query=[genre.lower() for genre in genre_query]
    
    counter={}
    for key in corr_query:
        val=float(corr_query[key]) 
        for cat in genre_query: 
            corr=float(corr_mat[key][cat])
            weighted=corr*val
            for film in genre_dict[cat]:
                if film in counter:
                    counter[film]+=weighted
                else: 
                    counter[film]=weighted

    results = list(counter.items())
    random.shuffle(results)
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:5]



