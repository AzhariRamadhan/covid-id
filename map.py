from math import radians, cos, sin, asin, sqrt
import pandas as pd
from tqdm import tqdm
import folium
import numpy as np
import requests

pd.set_option('max_rows', 500)
pd.set_option('max_columns', 500)

idn_json_url = "https://raw.githubusercontent.com/adamaulia/indonesia-geojson/master/indonesia-province-simple.json"
corona_url = "https://api.kawalcorona.com/indonesia/provinsi"

json_map = requests.get(idn_json_url).json()

df_json = pd.DataFrame(requests.get(idn_json_url).json())

json_corona = requests.get(corona_url).json()

df_corona = pd.DataFrame(list(map(lambda n: n['attributes'], json_corona)))

df_corona = df_corona[['Kode_Provi', 'Kasus_Posi', 'Kasus_Semb','Kasus_Meni','FID','Provinsi']]

df_corona['log_positif'] = df_corona['Kasus_Posi'].apply(lambda x:np.log(x))

df_json_prov = pd.DataFrame(list(map(lambda n: {'prov_id' : n['properties']['kode'], 'prov_name' : n['properties']['Propinsi']}, df_json['features'])))

df_join = pd.merge(df_corona,df_json_prov,left_on='Kode_Provi', right_on='prov_id',how='outer')


m = folium.Map(location=[-0.4471383, 117.1655734], zoom_start=3)

folium.Choropleth(
    geo_data=idn_json_url,
    name='choropleth',
    data=df_corona,
    columns=['Kode_Provi','log_positif','Kasus_Posi'],
    key_on='feature.properties.kode',
    fill_color='YlOrRd',
    fill_opacity=0.9,
    line_opacity=0.2,
    legend_name='Kasus_Positif logaritmic scale'
).add_to(m)

m

province_list , coord_list, province_id = [], [],[]
for item in df_json['features']:
#     province_list.append(df_json['properties']['Propinsi'])
    province_list.append(item['properties']['Propinsi'])
    province_id.append(item['properties']['kode'])
    tmp = item['geometry']['coordinates']
    flat_list = []
    for item in tmp :
        for subitem in item:
            for subsubitem in subitem:
                flat_list.append(subsubitem)
    coord_list.append(flat_list)

df_tmp = pd.DataFrame({'province':province_list,'coord_tmp':coord_list,'ID':province_id})
df_tmp['length'] = df_tmp['coord_tmp'].apply(len)

spc_city = ['GORONTALO', "DKI JAKARTA", "JAWA BARAT", "KALIMANTAN TENGAH", "SUMATERA SELATAN", "JAMBI", "LAMPUNG","DAERAH ISTIMEWA YOGYAKARTA"]

def get_lat_long(list_input):
    lat_long = []
    lat = []
    long = []
    for i in list_input:
        if i > 50:
            long.append(i)
        else :
            lat.append(i)
    if len(lat) == len(long):
        for i in range(len(lat)):
            lat_long.append([long[i],lat[i]])
    return lat_long

df_tmp1_a = df_tmp[df_tmp['province'].isin(spc_city)]

# city with normal coord structure
df_tmp1_b = df_tmp[~df_tmp['province'].isin(spc_city)]

df_tmp1_a['coord_tmp2'] = df_tmp1_a['coord_tmp'].apply(get_lat_long)

df_tmp1_a.drop('coord_tmp', inplace=True,axis=1)

df_tmp1_a = df_tmp1_a[['province','coord_tmp2','length','ID']]

df_tmp1_a.columns = ['province','coord_tmp','length','ID']

# explode lat long
df_tmp2 = pd.concat([df_tmp1_a,df_tmp1_b])
df_tmp2 = df_tmp2.explode('coord_tmp')

# extract lat and long into their column
df_tmp2['lat'] = df_tmp2['coord_tmp'].str[1]
df_tmp2['long'] = df_tmp2['coord_tmp'].str[0]

# avg lat and long per province 
df_tmp2_gb = df_tmp2.groupby(['province','ID']).agg( {'lat':'mean','long':'mean'})

df_tmp2_gb = df_tmp2_gb.dropna()
df_tmp2_gb = df_tmp2_gb.reset_index()

#join with corona data 
df_province_point = pd.merge(df_tmp2_gb,df_corona,left_on='ID',right_on='Kode_Provi',how='inner')

df_province_point.head()

for row in df_province_point.itertuples():    
    folium.Marker(
        location=[row.lat, row.long],
        icon=folium.Icon(color='blue', icon='info-sign'),
        popup = row.province +' '+str(row.Kasus_Posi) 
    ).add_to(m)

m.save('map.html')