import os
import pathlib
import pandas as pd
import json

# change current working directory for convenience
os.chdir(pathlib.Path(__file__).parent)

# read factory info
factory_info_df   = pd.read_csv('factory_info.csv')

# create list of factories and inverse dict
# factories are sorted alphabetically
factory_list      = list( factory_info_df['factory_id'] )
factory_list.sort()
factory_to_int    = { factory_list[i]:i for i in range(len(factory_list)) }

# read route info
route_info_df     = pd.read_csv('route_info.csv')

# get distance mtx and save as list of lists
route_distance_df = route_info_df.pivot_table( index='start_factory_id', columns='end_factory_id', values='distance', fill_value=0 )
route_distance_df = route_distance_df.rename( index=factory_to_int, columns=factory_to_int )

n = len(route_distance_df.index)
distance_mtx = [ [ route_distance_df[i][j] for j in range(n) ] for i in range(n) ]

with open('distance_mtx.json', 'w') as f:
    json.dump(distance_mtx, f, indent=2) 

# get time mtx and save as list of lists
route_time_df     = route_info_df.pivot_table( index='start_factory_id', columns='end_factory_id', values='time', fill_value=0 )
route_time_df     = route_time_df.rename( index=factory_to_int, columns=factory_to_int )

n = len(route_time_df.index)
time_mtx = [ [ route_time_df[i][j] for j in range(n) ] for i in range(n) ]
with open('time_mtx.json', 'w') as f:
    json.dump(time_mtx, f, indent=2) 


'''
Test if saved matrices are correct
'''

# original data
orig_df = pd.read_csv('route_info.csv')

# saved data
with open("distance_mtx.json", 'r') as f:
    dist_saved = json.load(f)
with open("time_mtx.json", 'r') as f:
    time_saved = json.load(f)

# check if data are matching
for ind in orig_df.index:
    tail = orig_df['start_factory_id'][ind]
    head = orig_df['end_factory_id'][ind]
    dist = orig_df['distance'][ind]
    time = orig_df['time'][ind]
    assert dist_saved[ factory_to_int[tail] ][ factory_to_int[head] ] == dist, f'distance mismatch from "{tail}" to "{head}"'
    assert time_saved[ factory_to_int[tail] ][ factory_to_int[head] ] == time, f'time mismatch from "{tail}" to "{head}"'

# check if distance and time from a factory to itself is 0
for i in range(len(dist_saved)):
    assert dist_saved[i][i] == 0, f'distance from "{i}" to "{i}" should be 0'
for i in range(len(time_saved)):
    assert time_saved[i][i] == 0, f'time from "{i}" to "{i}" should be 0'

# happy end
print('SUCCESS')