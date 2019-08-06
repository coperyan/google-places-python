import json
import requests
import pandas as pd
import urllib3
import sys
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from get_creds import *

master_export_dir = r'C:\Users\Ryan.Cope\Desktop\PlacesMaster.csv'
detail_export_dir = r'C:\Users\Ryan.Cope\Desktop\PlacesDetails.csv'

maps_api_key = get_gmapskey()
#List of accepted place types
accepted_types = [
'supermarket',
'liquor_store',
'bar',
'convenience_store'
]

#List of search strings
search_keywords = [
'beer',
'wine'
]

#Meter radius for each point below`
search_radius = 20000

#Max additional page tokens
max_addl_pages = 2

#Specified coordinates to search
search_coords = {'coords': [
                            {'lat': 38.702607, 'lng': -121.406366},
                            {'lat': 38.478354, 'lng': -121.464212},
                            {'lat': 38.539634, 'lng': -121.141309},
                            {'lat': 38.803796, 'lng': -121.181011}
                            ]
                }

#Putting together additional request headers
request_headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'max-age=0',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'
            }

#Search base url
base_search_url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'

#Place details base url
base_details_url = 'https://maps.googleapis.com/maps/api/place/details/json'

#Place summary DF
place_search_df = pd.DataFrame(columns=[
                                        'place_id',
                                        'place_lat',
                                        'place_lng',
                                        'place_name',
                                        'place_types'
                                        ])

#Place details DF
place_details_df = pd.DataFrame(columns=[
                                        'place_id',
                                        'place_lat',
                                        'place_lng',
                                        'place_name',
                                        'place_address',
                                        'place_city',
                                        'place_state',
                                        'place_zip',
                                        'place_phone',
                                        'place_link',
                                        'place_types',
                                        'place_rating',
                                        'place_ratingct'
                                        ])

#Function to get place search
def get_nearby_search(api_key,lat,lng,keyword,radius=None,rankby=None,type=None,pagetoken=None):
    '''
    Parameters:
        API Key:
            &key=
        Location:
            &location=lat,lng
        Radius:
            Max distance in meters away from lat/long (meters)
            Can't be included if RankBy is specified
            Can't be > 50000 meters
            &radius=
        RankBy:
            Distance or Prominence
            &rankby=
        Keyword:
        Type:
            Reference accepted_types list above
            &type=
    '''
    #Constructing base_url
    search_url = base_search_url
    search_url = '{}?location={},{}'.format(search_url,lat,lng)
    if radius:
        search_url = '{}&radius={}'.format(search_url,radius)
    search_url = '{}&keyword={}'.format(search_url,requests.utils.requote_uri(keyword))
    if rankby:
        search_url = '{}&rankby={}'.format(search_url,rankby)
    search_url = '{}&key={}'.format(search_url,api_key)
    if pagetoken:
        search_url = '{}&pagetoken={}'.format(search_url,pagetoken)

    get_search_json = requests.get(search_url, headers = request_headers, verify = False)
    get_search_json = get_search_json.json()

    time.sleep(2) # allows for generation of new page token

    return get_search_json

def shred_place_search(search_json):
    '''
    Will shred through the search itself
    Return records in a clean format
    '''

    iterct = 0

    place_resultct = len(search_json['results'])

    for x in range(place_resultct):
        iter_json = search_json['results'][x]
        iter_json_typect = len(iter_json['types'])
        place_id = iter_json['place_id']
        if place_id in place_search_df['place_id'].values:
            continue
        place_lat = iter_json['geometry']['location']['lat']
        place_lng = iter_json['geometry']['location']['lng']
        place_name = iter_json['name']
        place_types = ''
        for x in range(iter_json_typect):
            place_types = '{}{};'.format(place_types, iter_json['types'][x])
        iterct += 1


        place_search_df.loc[len(place_search_df)] = [
                                                        place_id,
                                                        place_lat,
                                                        place_lng,
                                                        place_name,
                                                        place_types
                                                    ]

    print('{} new results added to master DF..'.format(iterct))


#Function to get place details
def get_place_details(api_key, placeid):
    '''
    Parameters:
        API Key:
        PlaceID:
    '''
    details_url = base_details_url
    details_url = '{}?placeid={}'.format(details_url,placeid)
    details_url = '{}&key={}'.format(details_url,api_key)
    get_details_json = requests.get(details_url, headers = request_headers, verify = False)
    get_details_json = get_details_json.json()
    return get_details_json

#Function to shred through place details
def shred_place_details(detail_json):
    '''
    Will shred through the customer details
    Grab in clean format
    '''

    place_address = ''
    street_number = ''
    street_address = ''
    place_city = ''
    place_state = ''
    place_zip = ''
    place_types = ''

    detail_json = detail_json['result']
    place_id = detail_json['place_id']
    place_lat = detail_json['geometry']['location']['lat']
    place_lng = detail_json['geometry']['location']['lng']
    place_name = detail_json['name']
    try:
        place_rating = detail_json['rating']
    except:
        place_rating = ''
    try:
        place_ratingct = detail_json['user_ratings_total']
    except:
        place_ratingct = ''
    try:
        place_link = detail_json['website']
    except:
        place_link = ''
    try:
        place_phone = detail_json['formatted_phone_number']
    except:
        place_phone = ''

    add_len = len(detail_json['address_components'])
    for x in range(add_len):
        add_lng = detail_json['address_components'][x]['long_name']
        add_shrt = detail_json['address_components'][x]['short_name']
        add_typ = detail_json['address_components'][x]['types'][0]
        if add_typ == 'street_number':
            street_number = add_lng
        if add_typ == 'route':
            street_address = add_shrt
        if add_typ == 'locality':
            place_city = add_lng
        if add_typ == 'administrative_area_level_1':
            place_state = add_shrt
        if add_typ == 'postal_code':
            place_zip = add_shrt
    place_address = '{} {}'.format(street_number,street_address)

    typ_len = len(detail_json['types'])
    for x in range(typ_len):
        place_types = '{}{};'.format(place_types,detail_json['types'][x])

    place_details_df.loc[len(place_details_df)] = [
                                                    place_id,
                                                    place_lat,
                                                    place_lng,
                                                    place_name,
                                                    place_address,
                                                    place_city,
                                                    place_state,
                                                    place_zip,
                                                    place_phone,
                                                    place_link,
                                                    place_types,
                                                    place_rating,
                                                    place_ratingct
                                                    ]


def main():
    '''
    Main Function
    Grabs Zip from source (TBD)
    Go to town
    '''

    coord_ct = len(search_coords['coords'])
    keyword_ct = len(search_keywords)
    coord_iter = 0

    #Looping over coordinates
    for x in range(coord_ct):

        coord_iter += 1
        search_lat = search_coords['coords'][x]['lat']
        search_lng = search_coords['coords'][x]['lng']
        keyword_iter = 0

        #Looping over keywords
        for y in range(keyword_ct):

            #Starting the first search
            page_iter = 0
            page_iter += 1
            keyword_iter += 1
            search_keyword = search_keywords[y]
            print('Searching.. Coord #{}, Keyword #{}, Page #{}'.format(coord_iter, keyword_iter, page_iter))

            #Returning the JSON
            search_json = get_nearby_search(    api_key = maps_api_key,
                                                lat = search_lat,
                                                lng = search_lng,
                                                radius = search_radius,
                                                keyword = search_keyword
                                            )
            #Adding to a master data frame of results
            shred_place_search(search_json)
            #Getting next page token IF ANY
            try:
                next_page_token = search_json['next_page_token']
            except:
                continue

            #Attempting to do the same for the max of 2 ADDL pages
            for z in range(max_addl_pages):
                try:
                    page_iter += 1
                    print('Searching.. Coord#{}, Keyword #{}, Page #{}'.format(coord_iter,keyword_iter,page_iter))
                    search_json = get_nearby_search(
                                                    api_key = maps_api_key,
                                                    lat = search_lat,
                                                    lng = search_lng,
                                                    radius = search_radius,
                                                    keyword = search_keyword,
                                                    pagetoken = next_page_token
                                                    )
                    resultct = len(search_json['results'])
                    print('Successfully grabbed {} results..'.format(resultct))
                    shred_place_search(search_json)
                    next_page_token = search_json['next_page_token']
                except:
                    continue

    #Now the whole process is done, just need to grab details for each place ID
    places_ct = len(place_search_df)
    places_iter_ct = 0
    for index, row in place_search_df.iterrows():
        place_id = row['place_id']
        detail_json = get_place_details(api_key = maps_api_key, placeid = place_id)
        shred_place_details(detail_json)
        places_iter_ct += 1
        print('Shredded place {} of {}'.format(places_iter_ct,places_ct))

    place_search_df.to_csv(master_export_dir,index=False)
    place_details_df.to_csv(detail_export_dir,index=False)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(str(e))
