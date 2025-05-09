import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from flask import Flask, request, jsonify
import pandas as pd


# Seting up flask app
app = Flask(__name__)

# My spotify credentials from the Developer Dashboard// Spotify API
SPOTIPY_CLIENT_ID = '9a99af1c909c44dda2cf1413b254bf90'
SPOTIPY_CLIENT_SECRET = '278da29281654aaab559911cf61b42c7'

# Using Spotify Credentials to authorize/log in
auth_manager = SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET)
sp = spotipy.Spotify(auth_manager=auth_manager)

# Function that retrieves albums from inputted artist
def get_artist_albums(artist_name):
    results = sp.search(q=f'artist:{artist_name}', type='artist', limit=1)
    if not results['artists']['items']:
        return f"No artist found named {artist_name}."

    artist_id = results['artists']['items'][0]['id']
    albums = sp.artist_albums(artist_id, album_type='album')
    album_names = list({album['name'] for album in albums['items']})
    return f"Albums by {artist_name}: " + ", ".join(album_names[:10])


# Function that retrieves top tracks by inputted artist
def get_top_tracks_by_artist(artist_name):
    results = sp.search(q=f'artist:{artist_name}', type='artist', limit=1)
    if not results['artists']['items']:
        return f"No artist found named {artist_name}."

    artist_id = results['artists']['items'][0]['id']
    top_tracks = sp.artist_top_tracks(artist_id, country='US')
    track_names = [track['name'] for track in top_tracks['tracks']]
    return f"Top tracks by {artist_name}: " + ", ".join(track_names[:10])


# Function to get track info from inputted song
def get_track_info(user_input):
    try:
        lowered = user_input.lower()
        # Clean common prefixes, enables chatbot to be more effecient
        cleaned = (
            lowered.replace("track info", "")
                   .replace("info about", "")
                   .replace("about the track", "")
                   .replace("for", "")
                   .replace("about", "")
                   .strip()
        )

        # Try to split by 'by' to extract artist (optional)
        if " by " in cleaned:
            parts = cleaned.split(" by ")
            track_query = parts[0].strip()
            artist_hint = parts[1].strip()
            search_query = f"{track_query} artist:{artist_hint}"
        else:
            track_query = cleaned
            search_query = track_query

        results = sp.search(q=search_query, type='track', limit=5)

        if not results['tracks']['items']:
            return f"No track found matching '{track_query}'."

        for track in results['tracks']['items']:
            if track_query.lower() in track['name'].lower():
                name = track['name']
                artist = track['artists'][0]['name']
                album = track['album']['name']
                release_date = track['album']['release_date']
                url = track['external_urls']['spotify']
                return (
                    f"Track: {name}\nArtist: {artist}\nAlbum: {album}\n"
                    f"Release Date: {release_date}\nListen: {url}"
                )

        # Fallback: show top result even if not a perfect match
        track = results['tracks']['items'][0]
        name = track['name']
        artist = track['artists'][0]['name']
        album = track['album']['name']
        release_date = track['album']['release_date']
        url = track['external_urls']['spotify']
        return (
            f"Closest match for '{track_query}':\nTrack: {name}\nArtist: {artist}\nAlbum: {album}\n"
            f"Release Date: {release_date}\nListen: {url}"
        )

    except Exception as e:
        return f"Error retrieving track info: {e}"


# Function to get artist popularity score from CSV (Run etl.py to retrieve CSV file)
def get_popularity_from_csv(artist_name):
    try:
        # Load CSV data
        df = pd.read_csv('artist_popularity_scores_sorted.csv')

        # Clean up any leading/trailing spaces and standardize case for comparison
        artist_name = artist_name.strip().title()  # Ensure uniform formatting
        df['Artist'] = df['Artist'].str.strip().str.title()  # Ensures all artists' names are cleaned

        # Check if artist is in the DataFrame
        artist_data = df[df['Artist'] == artist_name]

        if not artist_data.empty:
            popularity_score = artist_data['Popularity Score'].values[0]
            return f"{artist_name} has a popularity score of {popularity_score}."
        else:
            return f"Sorry, I couldn't find the popularity score for {artist_name}. Please check the spelling or try a different artist."
    except Exception as e:
        return f"Error retrieving popularity score: {e}"
def get_artist_genres(artist_name):
    results = sp.search(q=f'artist:{artist_name}', type='artist', limit=1)
    if not results['artists']['items']:
        return f"No artist found named {artist_name}."

    genres = results['artists']['items'][0]['genres']
    return f"{artist_name} is associated with genres: " + ", ".join(genres or ["N/A"])

# Function to handle user input and return responses
def get_response(user_input):
    user_input = user_input.lower().strip().rstrip("?.,!")

    # Greeting
    if "hello" in user_input or "hi" in user_input:
        return "Hey, what kind of Spotify-related questions do you have for me?"

    # Popularity Score
    if "popularity" in user_input:
        keywords = ["popularity score for", "popularity of", "how popular is"]
        for keyword in keywords:
            if keyword in user_input:
                artist = user_input.split(keyword)[-1].strip().title()
                return get_popularity_from_csv(artist)

    # Top Tracks
    if "top tracks" in user_input or "top songs" in user_input:
        keywords = ["top tracks by", "top songs by", "top songs from", "top tracks from"]
        for keyword in keywords:
            if keyword in user_input:
                artist = user_input.split(keyword)[-1].strip().title()
                return get_top_tracks_by_artist(artist)

    # Albums
    if "albums by" in user_input or "albums from" in user_input:
        keywords = ["albums by", "albums from"]
        for keyword in keywords:
            if keyword in user_input:
                artist = user_input.split(keyword)[-1].strip().title()
                return get_artist_albums(artist)

    # Genres
    if "genre" in user_input:
        keywords = ["genres of", "what genre is", "what genre does", "genre of"]
        for keyword in keywords:
            if keyword in user_input:
                artist = user_input.split(keyword)[-1].strip().title()
                return get_artist_genres(artist)

    # Track Info
    if "track" in user_input and ("info" in user_input or "about" in user_input):
        keywords = ["track info about", "about the track", "info about", "track info", "track"]
        for keyword in keywords:
            if keyword in user_input:
                track = user_input.split(keyword)[-1].strip().title()
                return get_track_info(track)

    return "I didn't understand that. Try asking about albums, top tracks, genres, or popularity."


# Flask routes

@app.route('/')
def home():
    return 'Welcome to the Spotify Chatbot Assistant!'

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message')
    print(f"Received user input: {user_input}")  # Debugging line
    response = get_response(user_input)
    print(f"Generated response: {response}")  # Debugging line
    return jsonify({'response': response})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)



