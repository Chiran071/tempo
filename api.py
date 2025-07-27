import requests

SEARCH_URL = "https://streaming-availability.p.rapidapi.com/shows/search/title"
HEADERS = {
    "x-rapidapi-key": "880408e69bmshb58a2eb9f7401a3p11a46bjsn6e200b49adc5",
    "x-rapidapi-host": "streaming-availability.p.rapidapi.com"
}

def search_movies(title):
    print(f"🔎 Searching for movie: {title}")
    params = {
        "title": title,
        "country": "us",
        "show_type": "movie",
        "output_language": "en"
    }

    try:
        response = requests.get(SEARCH_URL, headers=HEADERS, params=params)
        print(f" Status Code: {response.status_code}")
        print(f" Raw response text: {response.text[:300]}")

        if response.status_code != 200:
            print(" API call failed")
            return []

        data = response.json()

        if not isinstance(data, list):
            print(" Expected list, got:", type(data))
            return []

        movies = []
        for item in data:
            movies.append({
                "id": item.get("id"),
                "title": item.get("title") or item.get("originalTitle"),
                "poster": item.get("imageSet", {}).get("verticalPoster", {}).get("w240", "")
            })

        print(f" Found {len(movies)} movies")
        return movies

    except Exception as e:
        print(" Exception in search_movies:", str(e))
        return []
