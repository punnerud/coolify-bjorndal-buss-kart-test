from flask import Flask, render_template, send_file
import requests, time, os, json, sqlite3
from lagretildb import save_to_database
import datetime

app = Flask(__name__)

#Erstatter til enklere forklaring
bus_names = {
    "RUT:Line:2071": {
        "2":"71b Mortensrud",
        "1":"71b Seterbråten"
            },
    "RUT:Line:71": {
    "2":"71a Mortensrud",
    "1":"71a Bjørdal"
            },
    "RUT:Line:77": {
    "1":"77 Hauketo",
    "2":"77 Bjørndal"
            }
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
            direction
            vehicleId
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
              direction = vehicle['direction']
              vehicleId = vehicle['vehicleId']
              
              ##  Sekunder siden: ##
              try:
                # Attempt to parse time with microseconds
                time = datetime.datetime.strptime(last_updated, '%Y-%m-%dT%H:%M:%S.%f%z')
              except ValueError:
                # If parsing fails, try again with no microseconds
                time = datetime.datetime.strptime(last_updated, '%Y-%m-%dT%H:%M:%S%z')

              now = datetime.datetime.now(time.tzinfo)
              elapsed_time = now - time
              secondsSinceUpdate = int(elapsed_time.total_seconds())


              buses.append({
                  'bus_number': bus_names[line][direction],  # Use bus_names dictionary to translate bus number
                  'last_updated': last_updated,
                  'lat': lat,
                  'lon': lon,
                  'direction': direction,
                  'vehicleId': vehicleId,
                  'secondsSinceUpdate' : secondsSinceUpdate,
              })
    #Lagre til database
    save_to_database(buses)
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
            if age < 15:  # Cache is less than 15 seconds old
                return json.load(f)
            else:
              return fetch_buses()
    except FileNotFoundError:
        return fetch_buses()
        pass  # Cache file does not exist, so just continue with the GraphQL request

@app.route('/')
def index():
    # Try to get buses from cache, otherwise fetch them from the API
    try:
        buses = get_buses_from_cache() or fetch_buses()
    except:
        print("Error - Ingen busser")
        buses = {}
        pass
    # Render template with bus data
    return render_template('index.html', buses=buses)

@app.route("/database", methods = ['GET'])
def db_return():
    store_location = os.environ.get("STORE_LOCATION")
    if store_location:
        db_file = os.path.join(store_location, "database.db")
    else:
        db_file = "database.db"
    return send_file(db_file, as_attachment=True)

portnr = os.environ.get("portnumber")
if portnr:
    portnr = portnr
else:
    portnr = 5000
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=portnr, debug=True)
