from flask import Flask, render_template
import requests, time, os, json

app = Flask(__name__)

#Erstatter til enklere forklaring
bus_names = {
    "RUT:Line:2071": "71b",
    "RUT:Line:71": "71a",
    "RUT:Line:77": "77"
}

def fetch_buses():
    # Fetch data from Entur's GraphQL API
    api_url = 'https://api.entur.io/realtime/v1/vehicles/graphql'
    headers = {
        'ET-Client-Name': '<YOUR_CLIENT_NAME>',
        'ET-Client-ID': '<YOUR_CLIENT_ID>',
        'Content-Type': 'application/json'
    }
    buses = []
    for line in ["RUT:Line:2071", "RUT:Line:71", "RUT:Line:77"]:
        query = f"""
        {{
          vehicles(codespaceId: "RUT", lineRef: "{line}") {{
            line {{
              lineRef
            }}
            lastUpdated
            location {{
              latitude
              longitude
            }}
          }}
        }}
        """
        data = {'query': query}
        r = requests.post(api_url, json=data, headers=headers)
        response_json = r.json()

        # Extract bus data from API response
        if response_json['data']['vehicles']:  # Only add buses if there are any
          for vehicle in response_json['data']['vehicles']:
              bus_number = vehicle['line']['lineRef']
              last_updated = vehicle['lastUpdated']
              lat = vehicle['location']['latitude']
              lon = vehicle['location']['longitude']
              buses.append({
                  'bus_number': bus_names[bus_number],  # Use bus_names dictionary to translate bus number
                  'last_updated': last_updated,
                  'lat': lat,
                  'lon': lon
              })

    # Save data to cache file
    os.remove('cache.json') # For å lage ny timestamp
    with open('cache.json', 'w') as f:
        json.dump(buses, f)

    return buses

def get_buses_from_cache():
    # Check if cache file exists and is less than 30 seconds old
    try:
        with open('cache.json', 'r') as f:
            cache_timestamp = time.gmtime(os.path.getmtime('cache.json'))
            age = time.time() - time.mktime(time.localtime(os.path.getmtime('cache.json')))
            print("timestamp:",cache_timestamp)
            print("age:",age)
            if age < 30:  # Cache is less than 30 seconds old
                print("CACHE")
                return json.load(f)
            else:
              print("Not cache 1")
              return fetch_buses()
    except FileNotFoundError:
        print("Not cache 2")
        return fetch_buses()
        pass  # Cache file does not exist, so just continue with the GraphQL request

@app.route('/')
def index():
    # Try to get buses from cache, otherwise fetch them from the API
    buses = get_buses_from_cache() or fetch_buses()
    print(buses)
    # Render template with bus data
    return render_template('index.html', buses=buses)

if __name__ == '__main__':
    app.run(debug=True)
