import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import time

# My spotify credentials from the Developer Dashboard// Spotify API
SPOTIPY_CLIENT_ID = ''
SPOTIPY_CLIENT_SECRET = ''
# Using Spotify Credentials to authorize/log in
client_credentials_manager = SpotifyClientCredentials(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET
)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

# List of genres to explore
genres = ['pop', 'hip-hop', 'rock', 'electronic', 'indie']


def get_top_artists_from_genres(genres):
    artist_map = {}

    for genre in genres:
        print(f"Fetching top tracks for genre: {genre}")
        try:
            # Fetching top tracks for a specific genre (paginate to get top 200)
            artist_ids = set()
            for offset in range(0, 200, 50):  # 50 * 4 = 200 tracks
                results = sp.search(q=f'genre:{genre}', type='track', limit=50, market='US', offset=offset)

                for track in results.get('tracks', {}).get('items', []):
                    for artist in track.get('artists', []):
                        artist_id = artist['id']
                        artist_name = artist['name']
                        artist_ids.add((artist_id, artist_name))

            # Add the unique artists to the artist_map
            for artist_id, artist_name in artist_ids:
                artist_map[artist_id] = artist_name

        except spotipy.exceptions.SpotifyException as e:
            print(f"Spotify API error: {e}")
            continue
        except Exception as e:
            print(f"Error fetching genre {genre}: {e}")
            continue

    print(f"Found {len(artist_map)} unique artists.")
    return artist_map


def get_artist_popularity(artist_map):
    artist_popularity = {}

    for artist_id, artist_name in artist_map.items():
        try:
            # Fetching top tracks for the artist
            top_tracks = sp.artist_top_tracks(artist_id, country='US')['tracks']
            total_popularity = sum(track['popularity'] for track in top_tracks)
            artist_popularity[artist_name] = total_popularity
        except spotipy.exceptions.SpotifyException as e:
            print(f"Rate limited or Spotify error for {artist_name}: {e}")
            print("Sleeping for 60 seconds...")
            time.sleep(60)  # Respect rate limit
            continue
        except Exception as e:
            print(f"Error fetching data for {artist_name}: {e}")
            continue

    return artist_popularity


# Run the process
artist_map = get_top_artists_from_genres(genres)
artist_popularity = get_artist_popularity(artist_map)

# Convert results to a DataFrame
df = pd.DataFrame(list(artist_popularity.items()), columns=['Artist', 'Popularity Score'])

# Sort the DataFrame by 'Popularity Score' in descending order
df = df.sort_values(by='Popularity Score', ascending=False)

# Save results to CSV
df.to_csv('artist_popularity_scores_sorted.csv', index=False)
print(f"Saved {len(df)} artists' popularity scores to artist_popularity_scores_sorted.csv")
