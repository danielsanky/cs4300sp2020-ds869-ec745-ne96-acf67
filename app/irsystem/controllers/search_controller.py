from . import *
from app.irsystem.models.helpers import *
from app.irsystem.models.helpers import NumpyEncoder as NumpyEncoder
import numpy as np
import pandas as pd
import collections 
from collections import Counter 
import random
import nltk
import re
from sklearn.feature_extraction.text import TfidfVectorizer

@irsystem.route('/', methods=['GET'])
def start():
    i = session.get("interests",'')
    g = session.get("genres",[])
    v = session.get("valence",'')
    d = session.get("danceability",'')
    e = session.get("energy",'')
    return render_template('index.html',interests=i, genres=g, valence=v, danceability=d, energy=e)

@irsystem.route('/submit/', methods=['POST', 'GET'])
def recommender():
    interests_query = request.args.get("interests")
    movie_genres = request.args.getlist("all-movies")
    song_genres = request.args.getlist("all-music")

    #SONGS
    #valence
    if request.args.get("valence"):
        valence=request.args.get("valence")
    else:
        valence='DONT CARE'
    #danceability
    if request.args.get("danceability"):
        danceability=request.args.get("danceability")
    else:
        danceability='DONT CARE'
    #energy
    if request.args.get("energy"):
        energy=request.args.get("energy")
    else:
        energy='DONT CARE'

    #factor in optional genres
    if song_genres!=[]:
        mod_music_query=mod_query(song_genres, music_qs)
        song=music_recs(valence, energy, danceability, mod_music_query)
    else: 
        song=music_recs(valence, energy, danceability)

    #get ready to display
    song=[{
            'title': item[1],
            'artist': item[2],
            'url': "https://open.spotify.com/embed/track/"+item[0],
            'genre': item[6], 
            'score': item[7]
            } for item in song]


    #PODCASTS AND MOVIES
    if type(interests_query)==str:
        podcast=podcast_recs(interests_query)
        if podcast[0]: 
             podcast=[{
            'title': item[0],
            'description': item[1],
            'url': item[2],
            'score': item[3]
            } for item in podcast]
        else:
            podcast=[]

        if movie_genres!=[]:
            mod_movie_query=mod_query(movie_genres, movie_qs)
            movie=movie_recs(interests_query,mod_movie_query)
        else:
            movie=movie_recs(interests_query)
    
        if movie[0]: 
            movie=[{
            'title': item[0],
            'year': item[1],
            'url': item[3], 
            'num_revs': item[2],
            'rating': item[4],
            #'genre': item[5],
            'score': item[5]
            } for item in movie]
        else:
            movie=[]
        
    else:
        podcast=[]
        movie=[]

    session["interests"] = interests_query
    session["genres"] = genres
    session["valence"] = valence
    session["danceability"] = danceability
    session["energy"] = energy
    # def movie_url(imdbid):
    #     s = str(imdbid)
    #     return "https://www.imdb.com/title/tt{0}/".format(s.zfill(7))

    # if movie_query!=[]:
    #     movie=recs(genre_to_movie, movie_query)
    #     movie=[{
    #         'title': item[0],
    #         'score': item[1],
    #         'url': movie_url(list(movies.loc[movies["Title"] == item[0]]["imdbId"].to_dict().values())[0]),
    #         'rating': list(movies.loc[movies["Title"] == item[0]]["IMDB Score"].to_dict().values())[0]
    #         } for item in movie]
    # else:
    #     movie=[]

    return render_template('results.html', podcasts=podcast, movies=movie, songs=song)

#load data
resp = pd.read_csv("young-people-survey/responses.csv")
podcasts=pd.read_csv("young-people-survey/df_popular_podcasts.csv")
word_exp=re.compile("[^\x00-\x7F]+")
non_eng_pod=[index for index,value in enumerate(list(podcasts["Name"].to_dict().values())) if len(re.findall(word_exp,value))!=0]
podcasts=podcasts.drop(non_eng_pod).drop_duplicates("Name", keep="first")

movies=pd.read_csv("young-people-survey/movie_metadata.csv")
movies=movies[movies["imdb_score"].astype(float)>float(5.0)]
movies=movies.dropna().drop_duplicates("movie_imdb_link", keep="first")

music=pd.read_csv("young-people-survey/SpotifyFeatures.csv")
music=music.drop_duplicates("track_id")

music_qs=list(Counter(list(music["genre"].to_dict().values())).keys())
movie_qs=['Horror', 'Biography', 'War', 'Western', 'Comedy', 'Sport', 'History', 'Musical', 'Family', 'Action', 'Animation', 'Adventure', 'Sci-Fi','Fantasy', 'Trhiller', 'Romance', 'Drama', 'Crime', 'Mystery', 'Documentary' ]
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

def cosine_sim(corpus):
    vectorizer=TfidfVectorizer(stop_words="english", min_df=1)
    tfidf = vectorizer.fit_transform(corpus)
    similarity = tfidf * tfidf.T
    return similarity.toarray()

def get_max_val_podcast(np_array): 
    index_max_val=np.argmax(np_array)
    output=(podcasts.iloc[index_max_val][:]["Name"], podcasts.iloc[index_max_val][:]["Description"], podcasts.iloc[index_max_val][:]["Podcast URL"], np_array[index_max_val])
    if np_array[index_max_val]==0:
        return 
    else: 
        np_array[index_max_val]=0
    return output

def get_max_val_movie(np_array):
    index_max_val=np.argmax(np_array)
    output=(movies.iloc[index_max_val][:]["movie_title"], movies.iloc[index_max_val][:]["title_year"], movies.iloc[index_max_val][:]["num_voted_users"], movies.iloc[index_max_val][:]["movie_imdb_link"], movies.iloc[index_max_val][:]["imdb_score"],np_array[index_max_val])
    if np_array[index_max_val]==0:
        return 
    else: 
        np_array[index_max_val]=0
    return output

def podcast_recs(query):
    descriptions=list(podcasts['Description'])
    corpus=[query]+descriptions
    matrix=cosine_sim(corpus)
    matrix_slice=matrix[:][0][1:]
    result=[]
    for x in range(5):
        result.append(get_max_val_podcast(matrix_slice))
    while None in result:
        result.remove(None)
    return result

def movie_recs(query):
    plot_keywords=list(movies['plot_keywords'])
    for i in range(len(plot_keywords)):
        plot_keywords[i]=plot_keywords[i].replace('|', " ")
    corpus=[query]+plot_keywords
    matrix=cosine_sim(corpus)
    matrix_slice=matrix[:][0][1:]
    result=[]
    for x in range(5):
        movie=get_max_val_movie(matrix_slice)
        result.append(movie)
    while None in result:
        result.remove(None)
    return result

def music_recs(val_pref, energy_pref, dance_pref, genres=None):
    # 1. Filter by genres (None means no filtering)
    if genres is None:
        music_filtered = music
    else:
        music_filtered = music[music.apply(lambda x: x['genre'] in genres, axis=1)]
    # 2. Compute relevance scores
    # Subscore functions
    subscore_fn = {
        'HIGH': lambda x: x,
        'MID': lambda x: 4 * x * (1 - x),
        'LOW': lambda x: 1 - x,
        'DONT CARE': lambda x: 0.5
    }
    # Subscores
    val_subscore = music_filtered['valence'].apply(subscore_fn[val_pref])
    energy_subscore = music_filtered['energy'].apply(subscore_fn[energy_pref])
    dance_subscore = music_filtered['danceability'].apply(subscore_fn[dance_pref])
    # Weights
    w_val, w_energy, w_dance = 1, 1, 1
    # Total score
    score = (w_val * val_subscore + w_energy * energy_subscore + w_dan ce * dance_subscore) \
        / (w_val + w_energy + w_dance)
    results = pd.DataFrame({
        'track_id': music_filtered['track_id'],
        'title': music_filtered['track_name'],
        'artist': music_filtered['artist_name'],
        'valence': music_filtered['valence'],
        'energy': music_filtered['energy'],
        'danceability': music_filtered['danceability'],
        'genre': music_filtered['genre'],
        'score': score
    })
    # 3. Shuffle
    results = results.sample(frac=1).reset_index(drop=True)
    # 4. Sort descending by score
    results.sort_values('score', ascending=False, inplace=True)
    results=[tuple(r) for r in results.to_numpy()]
    return results[:5]
