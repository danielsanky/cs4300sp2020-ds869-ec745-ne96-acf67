from . import *
from app.irsystem.models.helpers import *
from app.irsystem.models.helpers import NumpyEncoder as NumpyEncoder
import numpy as np
import pandas as pd
import collections
import random
import nltk
import re
from sklearn.feature_extraction.text import TfidfVectorizer

@irsystem.route('/', methods=['GET'])
def start():
    return render_template('index.html')


@irsystem.route('/back/', methods=['POST'])
def back():
    return render_template('index.html')

@irsystem.route('/submit/', methods=['POST', 'GET'])
def recommender():

    podcast_query = request.args.get("interests")
    movie_query = request.args.getlist("all-movies")
    music_query = request.args.getlist("all-music")
    #form_data = request.args.to_dict()

    if music_query!=[]:
        mod_music_query=mod_query(music_query, music_qs)
        song=recs(genre_to_music, mod_music_query)
        song=[{
            'title': item[0][1],
            'url': "https://open.spotify.com/embed/track/"+item[0][0],
            'artist': item[0][3],
            'genre': item[0][2]
            } for item in song]
    else:
        song=[]

    if podcast_query!=[]:
        podcast=podcast_recs(podcast_query)
        podcast=[{
            'title': item[0],
            'description': item[1],
            'url': item[2],
            'score': item[3]
            } for item in podcast]
    else:
        podcast=[]

    def movie_url(imdbid):
        s = str(imdbid)
        return "https://www.imdb.com/title/tt{0}/".format(s.zfill(7))

    if movie_query!=[]:
        movie=recs(genre_to_movie, movie_query)
        movie=[{
            'title': item[0],
            'score': item[1],
            'url': movie_url(list(movies.loc[movies["Title"] == item[0]]["imdbId"].to_dict().values())[0]),
            'rating': list(movies.loc[movies["Title"] == item[0]]["IMDB Score"].to_dict().values())[0]
            } for item in movie]
    else:
        movie=[]

    return render_template('results.html', podcasts=podcast, movies=movie, songs=song)

#load data
resp = pd.read_csv("young-people-survey/responses.csv")
podcasts=pd.read_csv("young-people-survey/df_popular_podcasts.csv")
word_exp=re.compile("[^\x00-\x7F]+")
non_eng_pod=[index for index,value in enumerate(list(podcasts["Name"].to_dict().values())) if len(re.findall(word_exp,value))!=0]
podcasts=podcasts.drop(non_eng_pod).drop_duplicates("Name", keep="first")

titles=pd.read_csv("young-people-survey/netflix_titles.csv")
movies=titles[titles["type"]=="Movie"]
shows=titles[titles["type"]=="TV Show"]


music=pd.read_csv("young-people-survey/SpotifyFeatures.csv")
music=music.drop_duplicates("track_id")
music=music[music["popularity"].astype(float)>float(50)]

genre_IDs=[['1311', 'News & Politics'], ['26', 'Podcasts'], ['1479', 'Social Sciences'], ['1315', 'Science & Medicine'], ['1324', 'Society & Culture'], ['1302', 'Personal Journals'], ['1469', 'Language Courses'], ['1304', 'Education'], ['1320', 'Places & Travel'], ['1416', 'Higher Education'], ['1465', 'Professional'], ['1316', 'Sports & Recreation'], ['1303', 'Comedy'], ['1305', 'Kids & Family'], ['1439', 'Christianity'], ['1314', 'Religion & Spirituality'], ['1444', 'Spirituality'], ['1309', 'TV & Film'], ['1462', 'History'], ['1310', 'Music'], ['1478', 'Medicine'], ['1321', 'Business'], ['1412', 'Investing'], ['1420', 'Self-Help'], ['1307', 'Health'], ['1481', 'Alternative Health'], ['1417', 'Fitness & Nutrition'], ['1467', 'Amateur'], ['1480', 'Software How-To'], ['1318', 'Technology'], ['1448', 'Tech News'], ['1456', 'Outdoor'], ['1477', 'Natural Sciences'], ['1301', 'Arts'], ['1454', 'Automotive'], ['1323', 'Games & Hobbies'], ['1438', 'Buddhism'], ['1443', 'Philosophy'], ['1401', 'Literature'], ['1402', 'Design'], ['1410', 'Careers'], ['1470', 'Training'], ['1413', 'Management & Marketing'], ['1306', 'Food'], ['1406', 'Visual Arts'], ['1446', 'Gadgets'], ['1468', 'Educational Technology'], ['1405', 'Performing Arts'], ['1460', 'Hobbies'], ['1471', 'Business News'], ['1404', 'Video Games'], ['1450', 'Podcasting'], ['1473', 'National'], ['1325', 'Government & Organizations'], ['1461', 'Other Games'], ['1466', 'College & High School'], ['1459', 'Fashion & Beauty'], ['1476', 'Non-Profit'], ['1415', 'K-12'], ['1455', 'Aviation'], ['1464', 'Other'], ['1421', 'Sexuality'], ['1472', 'Shopping'], ['1475', 'Local'], ['1441', 'Judaism'], ['1440', 'Islam'], ['1474', 'Regional'], ['1463', 'Hinduism']]


music_qs=list(Counter(list(music["genre"].to_dict().values())).keys())
del music_qs[12]


def mod_query(query, poss_q_list):
    n_query=[]
    for item in query:
        if item in poss_q_list and not n_query:
            n_query.append(item)
        elif item in poss_q_list and n_query:  #Avoids duplicates
            pass
        else:
            for token in item.lower().split(' '):
                # Find edit distance of the words (all in lowercase)
                ed_list=sorted([(q_term,nltk.edit_distance(token, q_term.lower(), substitution_cost=2)) for q_term in poss_q_list], key=lambda x:x[1])
                print(ed_list)
                i=0
                # Iterate through ed_list until an item that isn't in n_query is found
                while ed_list[i][0] in n_query and i<len(ed_list):
                    i+=1
                #for the case when it reaches the final item in ed_list, and another confirmation that the word isn't inn_query
                if ed_list[i][0] not in n_query:
                    n_query.append(ed_list[i][0])
    return n_query



# Better organize the id vs name of genre
dict_pod={int(id[0]):id[1] for id in genre_IDs }

# {Genre ID:NAMES OF PODCAST}
genre_to_podcast={key:[] for key in dict_pod }
for item in podcasts.index:
    array=podcasts["Genre IDs"][item][1:-1].split(',')
    array=[int(array[i].replace('\'', '').strip('\'')) for i in range(len(array))]
    for j in range(len(array)):
        genre_to_podcast[array[j]].append((podcasts["Name"][item], podcasts["Description"][item], podcasts["Podcast URL"][item]))
final_dict={list(dict_pod.values())[p]:list(genre_to_podcast.values())[p] for p in range(len(genre_to_podcast.keys()))}
final_dict = dict((k.lower(), v) for k, v in final_dict.items())

#MAKE MOVIE DICTIONARY
genre_to_movie={}
for i in range( len(movies)):
    line=str(movies.iloc[i]["Genre"])
    for genre in line.split("|"):
        genre=genre.lower()
        if genre in genre_to_movie:
            genre_to_movie[genre].append(movies.iloc[i]["Title"])
        else:
            genre_to_movie[genre]=[movies.iloc[i]["Title"]]

#MAKE MUSIC DICTIONARY
genre_to_music={}
for i in range(len(music)):
    genre=music.iloc[i]['genre']
    genre=genre.lower()
    if genre in genre_to_music:
            genre_to_music[genre].append((music.iloc[i]['track_id'], music.iloc[i]['track_name'],  music.iloc[i]['genre'],  music.iloc[i]['artist_name']))
    else:
            genre_to_music[genre]=[(music.iloc[i]['track_id'], music.iloc[i]['track_name'],  music.iloc[i]['genre'],  music.iloc[i]['artist_name'])]


#MAKE CORRELATION MATRIX
#music_resp=resp.iloc[:, :19]
#movie_resp=resp.iloc[:, 19:31]
#hobbies_resp=resp.iloc[:, 31:63]
#personality_resp=resp.iloc[:, [79, 80, 105, 106, 109, 110, 113, 129, 132]]
#demographics_resp=resp.iloc[:, [140, 144, 146, 147]]

#final_mat=pd.concat([music_resp, movie_resp, hobbies_resp, personality_resp, demographics_resp], axis=1)
#final_mat=final_mat.rename(columns={"New environment": "adapt", "Socializing": "meeting-people", "Waiting":"patient", "Number of friends": "friends", "Workaholism": "study", "Thinking ahead": "perspectives", "Charity": "charity", "Interests or hobbies": "differ-hobbies"})

#corr_mat=pd.DataFrame.corr(final_mat)
#corr_mat.columns = map(str.lower, corr_mat.columns)
#corr_mat.index = map(str.lower, corr_mat.index)


def recs(genre_dict, genre_query):
    """Returns a list of recommendations based on interests user clicked in form
    Params: {query: list of genre names, genre_dict: dictionary that maps genre to titles, corr_dict: maps personality questions to answers given in survey}
    Returns: list of tuples containing titles and scores
    """

    #query is an array of genre_names
    #corr_query is a dictionary of radio button responses like {'all-music': 'R&B', 'all-movies': 'Horror', 'all-interests': 'Social Sciences', 'gender': 'female', 'education': 'no'}
    #if 'all-interests' in corr_query:
    #    corr_query.pop('all-interests', None)
    #if 'all-movies' in corr_query:
    #    corr_query.pop('all-movies', None)
    #if 'all-music' in corr_query:
    #    corr_query.pop('all-music', None)
    #if not corr_query: #check if empty
    #    corr_query={'charity': '3', 'adapt': '3', 'meeting-people': '3', 'patient': '3', 'friends': '3', 'study': '3', 'perspectives': '3', 'differ-hobbies': '3' }

    genre_query=[genre.lower() for genre in genre_query]

    counter={}
    #for key in corr_query:
    #    val=float(corr_query[key])
    #    if val > 3.0:
    #        val = val - 3
    #    elif val == 3.0:
    #        val = 1
    #    elif val < 3.0:
    #        val = val* - 1
    for cat in genre_query:
        #corr=float(corr_mat[key][cat])
        #weighted=corr*val
        for film in genre_dict[cat]:
            if film in counter:
                counter[film]+=1
            else:
                counter[film]=1

    results = list(counter.items())
    random.shuffle(results)
    results.sort(key=lambda x: x[1], reverse=True)
    #highest_score=results[0][1]
    #output=[]
    #for result in results[:5]:
    #    output.append((result[0], result[1]/highest_score))

    return results[:5]


def cosine_sim(corpus):
    vectorizer=TfidfVectorizer(stop_words="english", min_df=1)
    tfidf = vectorizer.fit_transform(corpus)
    similarity = tfidf * tfidf.T
    return similarity.toarray()

def get_max_val(np_array):
    index_max_val=np.argmax(np_array)
    output=(podcasts.iloc[index_max_val][:]["Name"], podcasts.iloc[index_max_val][:]["Description"], podcasts.iloc[index_max_val][:]["Podcast URL"], np_array[index_max_val])
    np_array[index_max_val]=0
    return output

def podcast_recs(query):
    descriptions=list(podcasts['Description'])
    corpus=[query]+descriptions
    matrix=cosine_sim(corpus)
    matrix_slice=matrix[:][0][1:]
    result=[]
    for x in range(5):
        result.append(get_max_val(matrix_slice))
    return result
