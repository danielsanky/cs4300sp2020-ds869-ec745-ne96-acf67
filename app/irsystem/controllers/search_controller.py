from . import *  
from app.irsystem.models.helpers import *
from app.irsystem.models.helpers import NumpyEncoder as NumpyEncoder
import numpy as np 
import pandas as pd 
import collections

#project_name = "Ilan's Cool Project Template"
#net_id = "Ilan Filonenko: if56"

@irsystem.route('/', methods=['GET'])
def test():
    return render_template('index.html')


@irsystem.route('/submit/', methods=['GET'])
def recommender():
    podcast_query = request.args.getlist("interests")
    movie_query = request.args.getlist("movie-genre")
    if podcast_query!=[]:
        podcast=recs(final_dict, podcast_query)
    else:
        podcast="We can't recommend you a podcast, since we don't know your interests!"
    if movie_query!=[]:
        movie=recs(genre_to_movie, movie_query)
    else: 
        movie="We can't recommend you a movie, since we don't know what genres you like!"

    return render_template('index.html', podcast=podcast, movie="movie")

#load data
cols = pd.read_csv("young-people-survey\columns.csv")
resp = pd.read_csv("young-people-survey\\responses.csv")
podcasts=pd.read_csv("young-people-survey\df_popular_podcasts.csv")
movies=pd.read_csv("young-people-survey\MovieGenre.csv", encoding="ANSI")
genre_IDs=[['1311', 'News & Politics'], ['26', 'Podcasts'], ['1479', 'Social Sciences'], ['1315', 'Science & Medicine'], ['1324', 'Society & Culture'], ['1302', 'Personal Journals'], ['1469', 'Language Courses'], ['1304', 'Education'], ['1320', 'Places & Travel'], ['1416', 'Higher Education'], ['1465', 'Professional'], ['1316', 'Sports & Recreation'], ['1303', 'Comedy'], ['1305', 'Kids & Family'], ['1439', 'Christianity'], ['1314', 'Religion & Spirituality'], ['1444', 'Spirituality'], ['1309', 'TV & Film'], ['1462', 'History'], ['1310', 'Music'], ['1478', 'Medicine'], ['1321', 'Business'], ['1412', 'Investing'], ['1420', 'Self-Help'], ['1307', 'Health'], ['1481', 'Alternative Health'], ['1417', 'Fitness & Nutrition'], ['1467', 'Amateur'], ['1480', 'Software How-To'], ['1318', 'Technology'], ['1448', 'Tech News'], ['1456', 'Outdoor'], ['1477', 'Natural Sciences'], ['1301', 'Arts'], ['1454', 'Automotive'], ['1323', 'Games & Hobbies'], ['1438', 'Buddhism'], ['1443', 'Philosophy'], ['1401', 'Literature'], ['1402', 'Design'], ['1410', 'Careers'], ['1470', 'Training'], ['1413', 'Management & Marketing'], ['1306', 'Food'], ['1406', 'Visual Arts'], ['1446', 'Gadgets'], ['1468', 'Educational Technology'], ['1405', 'Performing Arts'], ['1460', 'Hobbies'], ['1471', 'Business News'], ['1404', 'Video Games'], ['1450', 'Podcasting'], ['1473', 'National'], ['1325', 'Government & Organizations'], ['1461', 'Other Games'], ['1466', 'College & High School'], ['1459', 'Fashion & Beauty'], ['1476', 'Non-Profit'], ['1415', 'K-12'], ['1455', 'Aviation'], ['1464', 'Other'], ['1421', 'Sexuality'], ['1472', 'Shopping'], ['1475', 'Local'], ['1441', 'Judaism'], ['1440', 'Islam'], ['1474', 'Regional'], ['1463', 'Hinduism']]

#dependent vbs
music=cols[:19]
movie_cols=cols[19:31]
hobbies=cols[31:63]

#independent vbs
personality=cols[76:133]
demographics=cols[140:147]

#Prep the podcasts dataset for the function 

#Get rid of columns we won't use
#podcasts=podcasts.drop('Artwork', axis=1)
#podcasts=podcasts.drop('Episode Count', axis=1)
#podcasts=podcasts.drop('Episode Durations', axis=1)
#podcasts=podcasts.drop('iTunes URL', axis=1)
#podcasts=podcasts.drop('Feed URL', axis=1)
podcasts.head()

# Better organize the id vs name of genre
dict_pod={int(id[0]):id[1] for id in genre_IDs }

# {Genre ID:NAMES OF PODCAST} 
genre_to_podcast={key:[] for key in dict_pod }

for item in podcasts.index:
    array=podcasts["Genre IDs"][item][1:-1].split(',')
    array=[int(array[i].replace('\'', '').strip('\'')) for i in range(len(array))]
    for j in range(len(array)):
        genre_to_podcast[array[j]].append(podcasts["Name"][item])

final_dict={list(dict_pod.values())[p]:list(genre_to_podcast.values())[p] for p in range(len(genre_to_podcast.keys()))}

movies=movies[:10000]

genre_to_movie={}
for i in range(len(movies)):
    line=str(movies["Genre"][i])
    for genre in line.split("|"):
        if genre in genre_to_movie:
            genre_to_movie[genre].append(movies["Title"][i])
        else: 
            genre_to_movie[genre]=[movies["Title"][i]]


def recs(genre_dict, query):
    """Returns a list of podcasts based on interests user clicked in form
    Params: {query: list of genre names, genre_dict: dictionary that maps genre to titles}
    Returns: list of titles and scores
    """

    arr=collections.Counter([[] + genre_dict[cat] for cat in query if cat in list(genre_dict.keys())][0])
    if len(arr.keys())>5:
	    return [(key,value) for key,value in arr.items()]
    elif max(arr.values())==1:
        converted_list=sorted(x.items(), key=lambda pair: pair[1], reverse=True)
        return np.random.choice(converted_list,size=5, replace=False)
    else:
        return arr.most_common(5)



#def music_recs():
#    """Returns a list of songs based on genres user clicked in form
    
#    Params: {genres: list or set of genre names}
#    Returns: list of song titles and scores
#    """
#    return 



