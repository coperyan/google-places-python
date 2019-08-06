# python-google-places

Example of using the Google Places API using Python

## How to use

1. Add your own credentials
2. Edit export paths for master/detail CSVs
3. Edit list of accepted place types
4. Edit list of search keywords
5. Edit search radius
6. Edit search coordinates (lat/lng)

## How it works

1. Iterates over each geocode & search keyword
2. Performs a search for nearby "places"
3. Filters out duplicates, results that don't fit accepted place "types" (specified by user)
4. Exports places and their details to CSVs in specified paths

## Documentation

1. Place Search: https://developers.google.com/places/web-service/search
2. Place Details: https://developers.google.com/places/web-service/details
3. Place IDs (for examples): https://developers.google.com/places/web-service/place-id
4. Place Types: https://developers.google.com/places/web-service/supported_types
