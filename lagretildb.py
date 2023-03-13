import os
import sqlite3
 
def save_to_database(data: list):
    # Use default file path if STORE_LOCATION is not set
    store_location = os.environ.get("STORE_LOCATION")
    if store_location:
        db_file = os.path.join(store_location, "database.db")
    else:
        db_file = "database.db"

    conn = sqlite3.connect(db_file)
    c = conn.cursor()

    # Create table if it doesn't exist
    c.execute('''CREATE TABLE IF NOT EXISTS data (bus_number text, last_updated text, lat real, lon real, direction text, vehicleId text)''')

    # Insert data into table
    for item in data:
        c.execute("INSERT INTO data (bus_number, last_updated, lat, lon, direction, vehicleId) VALUES (?, ?, ?, ?, ?, ?)", (item['bus_number'], item['last_updated'], item['lat'], item['lon'], item['direction'], item['vehicleId']))

    # Commit changes and close connection
    conn.commit()
    conn.close()
