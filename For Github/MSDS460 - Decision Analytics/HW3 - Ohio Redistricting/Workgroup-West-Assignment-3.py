
import requests
import csv
import json

#%%
###
###
###
# This big block of code looks at the census source to identify counties
# This code accomplishes a handful of things:
# 1. Downloads a list of Ohio counties with the county ID and name pair
# 2. Downloads a dictionary that contains every county and all of the counties that are contiguous
# 3. Filters the dictionary to include only Ohio counties as keys and only Ohio counties as value pairs
# Note that this #3 item is useful in application, because we will only consider OH counties in our constraints
###
###
###

# Hat tip to:
# https://gist.github.com/cjwinchester/a8ff5dee9c07d161bdf4

def getCounties():
    "Function to return a dict of FIPS codes (keys) of U.S. counties (values)"
    d = {}
    r = requests.get("http://www2.census.gov/geo/docs/reference/codes/files/national_county.txt")
    reader = csv.reader(r.text.splitlines(), delimiter=',')
    for line in reader:
        d[line[1] + line[2]] = line[3].replace(" County","")
    return d

def getOhioCounties():
    "Function to return a dict of FIPS codes (keys) of U.S. counties (values)"
    d = {}
    r = requests.get("http://www2.census.gov/geo/docs/reference/codes/files/national_county.txt")
    reader = csv.reader(r.text.splitlines(), delimiter=',')
    for line in reader:
        if line[0] == "OH":
            d[line[1] + line[2]] = line[3].replace(" County","")
    return d

def getCountyAdj():
    "Return a list of dicts where each dict has a county FIPS code (key) and a list of FIPS codes of the adjacent counties, not including that county (value)"
    adj = requests.get("http://www2.census.gov/geo/docs/reference/county_adjacency.txt")
    #    adj_data = adj.text.encode("utf-8")
    #    reader = csv.reader(adj_data.splitlines(), delimiter='\t')
    reader = csv.reader(adj.text.splitlines(), delimiter='\t')
    ls = []
    d = {}
    countyfips = ""
    for row in reader:
        if row[1] and row[1] != "":
            if d:
                ls.append(d)
            d = {}
            countyfips = row[1]
            d[countyfips] = []
            "Grab the record on the same line"
            try:
                st = row[3]
                if st != countyfips:
                    d[countyfips].append(st)
            except:
                pass
        else:
            "Grab the rest of the records"
            if row[3] and row[3] != "":
                st = row[3]
                if st != countyfips:
                    d[countyfips].append(st)
    #    return json.dumps(ls)
    return ls

#%%
data = getCountyAdj()

#%%
new_dict = {}
for item in data:
    name = list(item)[0]
    new_dict[name] = item
#%%

ohio_counties = getOhioCounties()

print("There are 88 OH counties.  The number of OH counties from the data: ",len(ohio_counties.keys()))
ohio_counties_list = list(ohio_counties.keys())
ohio_counties_set = set(ohio_counties_list)
#print(ohio_counties_list)
#print(ohio_counties_set)
#%%
print(ohio_counties['39007'])

#%%
counties = {}
for county in ohio_counties:
    counties[county] = {}
    counties[county]['name'] = ohio_counties[county]
    full_contiguous = list(new_dict[county].values())[0]
    oh_contiguous = [x for x in full_contiguous if x in ohio_counties_set]
    counties[county]['contiguous'] = oh_contiguous

print(counties)
print(counties['39001'])
print(counties['39001']['contiguous'])
print(counties['39001']['contiguous'][2])
#%%

import pandas as pd
import numpy as np
import censusdata
import requests

#%%
data_ll = pd.read_csv("2021GazCounties.csv", sep="\t")                          ## Sourced from Census.Gov
data_ll.columns = ['NA', 'FIPS', 'NA','NA','NA','NA','NA','NA','LAT','LONG']
data_ll.set_index('FIPS', inplace=True)
data_ll.index = data_ll.index.map(str)
#%%
data = censusdata.download('acs5', 2020,
                           censusdata.censusgeo([('state', '39'),
                                                 ('county', '*')]),
                           ['B02001_001E', 'B02001_002E'])
data.index.name = 'County'
data.index.astype(str, copy = False)
data.set_axis(['Pop_Total', 'Pop_White'], axis=1, inplace = True)
data['Pct_White'] = data['Pop_White'] / data['Pop_Total']
print(data.head())
#%%
data.rename(index=lambda n: '39' + n.geo[1][1], inplace = True)
print(data.head())
#%%
#print(data['Pop_White'])
print(data.loc['39167']['Pop_White'])
print(type(data.loc['39167']['Pop_White']))
print(type(data.loc['39167']['Pop_White'].item()))

#%%
print(data.loc['39001']['Pop_White'])
#%%
for county_id in counties:
    counties[county_id]['Pop_Total'] = data.loc[county_id]['Pop_Total'].item()
    counties[county_id]['Pop_White'] = data.loc[county_id]['Pop_White'].item()
    counties[county_id]['LAT'] = data_ll.loc[county_id]['LAT']
    counties[county_id]['LONG'] = data_ll.loc[county_id]['LONG']

print(counties)

#%%
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpStatus, getSolver, value # mathematical programming
import datetime
import math
import pandas as pd
import numpy as np
from geopy.distance import geodesic
import geopandas as gpd
import plotly.express as px
import json

#%%
print(counties)

#%%
# Set up inputs
n_districts = 16
target_totalpop_swing = 0.05
target_whitepop_swing = 1
target_whitepct = 1
min_allocation_big_districts = 0.4
max_districts = 2

# Note: below is the best pop/weighted value excluding racial balance:
#tightest_pop_distribution = 3189654695  # If d = 16
#tightest_pop_distribution = 23792449955 # If d = 3
#acceptable_pop_distribution = tightest_pop_distribution * 3

# The code above was used in my attempt to run a two-stage optimization.  It was ultimately abandoned

#%%

# Input variables we need for constraints etc:
# c_ij --> whether county i and county j are contiguous   <-- NOTE: THESE ARE INPUTS
# tp_i --> the total population of county i
# wp_i --> the white population of county i

county_id_list = list(counties.keys())
n_counties = len(county_id_list)
c = {}
tp = {}
wp = {}
for i in county_id_list:
    c[i] = {}
    for j in county_id_list:
        c[i][j] = 0
        if j in counties[i]['contiguous']:
            c[i][j] = 1
    tp[i] = counties[i]['Pop_Total']
    wp[i] = counties[i]['Pop_White']

# Encoding of variables
pop_tot = 0
pop_white = 0
for id in counties:
    pop_tot = pop_tot + counties[id]['Pop_Total']
    pop_white = pop_white + counties[id]['Pop_White']
pct_white_state = pop_white / pop_tot
target_district_totalpop = int(pop_tot / n_districts)
target_district_totalpop_max = target_district_totalpop * (1 + target_totalpop_swing)
target_district_totalpop_min = target_district_totalpop * (1 - target_totalpop_swing)

target_district_whitepop = int(pop_white / n_districts)
target_district_whitepop_max = target_district_whitepop * (1 + target_whitepop_swing)
target_district_whitepop_min = target_district_whitepop * (1 - target_whitepop_swing)

ew = {}                                     # ew stands for "Extra Whites."  Used to capture absolute error
for i in county_id_list:
    ew[i] = wp[i] - pct_white_state * tp[i]

#%%
print(pct_white_state)

#%%
print(ew)


#%%

# DECISION variables:
# d_ik --> whether county i is in district k
# a_ik --> the percentage allocation of county i's population to district k
#   Note: this a_ik value is only != 100% for the 2-3 very large districts that get apportioned out

# OUTCOME variables:
# wp_k --> the white population of district k
# pw_k --> percentage of population that's white in district k
# tp_k --> the total population of district k

#%%
#d_latlong = (counties['39041']['LAT'], counties['39041']['LONG']) # Delaware County; v. close to Franklin
#f_latlong = (counties['39049']['LAT'], counties['39049']['LONG']) # Franklin County

#print(d_latlong, f_latlong)
#print(geodesic(d_latlong, f_latlong).miles)


# This code is used to identify the distances between any pair of counties
# The distance squared is used in the Hess penalty function
dist = {}
distsq = {}
for i in counties:
    dist[i] = {}
    distsq[i] = {}
    loc_i = (counties[i]['LAT'], counties[i]['LONG'])
    for j in counties:
        loc_j = (counties[j]['LAT'], counties[j]['LONG'])
        distance = geodesic(loc_i, loc_j).miles
        dist[i][j] = distance
        distsq[i][j] = distance * distance

#%%
# Create the linear programming model.
model = LpProblem("Racial Balance by District", LpMinimize)
variable_names_ij = [str(i)+str(j) for j in county_id_list for i in county_id_list]
variable_names_ik = [str(i)+str(k) for k in range(1, n_districts+1) for i in county_id_list]
variable_names_j = [str(j) for j in county_id_list]
variable_names_ij.sort()
variable_names_ik.sort()
variable_names_j.sort()
#%%
print(variable_names_ij)
#%%

# The Decision Variable is 1 if the county is assigned to the district centered on county k.
DV_variable_d = LpVariable.matrix("d", variable_names_ij, cat="Binary", lowBound=0, upBound=1)
d = np.array(DV_variable_d).reshape(n_counties, n_counties)
# keep in mind: d[i][j] references the indx number.  i != county ID

# The Allocation Variable is the percentage of population allocated to the district
# Note: The allocation is forced to 100% for all but the largest 2-3 counties
DV_variable_a = LpVariable.matrix("a", variable_names_ij, cat="Continuous", lowBound=0, upBound=1)
a = np.array(DV_variable_a).reshape(n_counties, n_counties)
# keep in mind: a[i][j] references the indx number.  i != county ID

# The District Delta Whites variable is set to equal the absolute value difference
#   between the actual number of whites in a district and the "target" number given Ohio's total percentage
#   note this is accomplished by capturing target - actual and actual - target as different values
#   and then "deciding" that district delta will be greater than both values.  Thus, abs value
#DV_variable_dw = LpVariable.matrix('district_delta_whites', variable_names_j, cat = "Continuous", lowBound=0)
#district_delta_whites = np.array(DV_variable_dw).reshape(n_counties)

#DV_variable_cl = LpVariable.matrix("cl", variable_names_ij, cat="Binary", lowBound=0, upBound=1)
#cl = np.array(DV_variable_cl).reshape(n_counties, n_counties)
# keep in mind: cl[i][j] references the indx number.  i != county ID
#%%
print(d)
print(d[1][2])
#%%
# Objective Function is to minimize moment of inertia d^2 * p * x_ik

district_weight = {}
for j in county_id_list:
    district_weight[j] = lpSum(distsq[i][j] * tp[i] * d[county_id_list.index(i)][county_id_list.index(j)] for i in county_id_list)
model += lpSum(district_weight[j] for j in county_id_list)

#%%
#%%
# Add constraint that each county is assigned to one district

# below code works if there's no allocation of counties
#for i in range(n_counties):
#    model += lpSum(d[i][j] for j in range(n_counties)) == 1

# Code below creates separate rules for handling large counties vs small counties
# Larger counties are apportioned into multiple districts using the allocation approach
# Smaller counties are forced into a single district

for i in range(n_counties):
    if tp[county_id_list[i]] > target_district_totalpop_max:
        model += lpSum(d[i][j] for j in range(n_counties)) <= max_districts
        for j in range(n_counties):
            model += a[i][j] >= d[i][j] * min_allocation_big_districts
            model += d[i][j] >= a[i][j]
        model += lpSum(a[i][j] for j in range(n_counties)) == 1
    else:
        model += lpSum(d[i][j] for j in range(n_counties)) == 1
        for j in range(n_counties):
            model += a[i][j] == d[i][j]


model += lpSum(d[j][j] for j in range(n_counties)) == n_districts

# District population is used in two ways:
# 1. The total district population needs to be between upper and lower bounds
# 2. The white district population needs to be below a target percentage level
# Note: if the target percentage is at all binding then the resultant district map is noncontiguous

# Other lines of code are commented out, representing different approaches for handling population allocations
district_pop = {}
for j in range(n_counties):
    district_pop[j] = lpSum(tp[county_id_list[i]] * a[i][j] for i in range(n_counties))
    #   The commented code is with single assignment.  the a[i][j] is where there's allocation
    #    model += lpSum(tp[county_id_list[i]] * d[i][j] for i in range(n_counties)) >= target_district_pop_min * d[j][j]
    #    model += lpSum(tp[county_id_list[i]] * d[i][j] for i in range(n_counties)) <= target_district_pop_max * d[j][j]
    model += district_pop[j] >= target_district_totalpop_min * d[j][j]
    model += district_pop[j] <= target_district_totalpop_max * d[j][j]
    model += lpSum(wp[county_id_list[i]] * a[i][j] for i in range(n_counties)) <= target_whitepct * district_pop[j]

#    model += lpSum(wp[county_id_list[i]] * a[i][j] for i in range(n_counties)) >= target_district_whitepop_min * d[j][j]
#    model += lpSum(wp[county_id_list[i]] * a[i][j] for i in range(n_counties)) <= target_district_whitepop_max * d[j][j]


for i in range(n_counties):
    for j in range(n_counties):
        model += d[i][j] <= d[j][j]

#%%
# Add contiguity constraints


#%%
print('Model starting at ', datetime.datetime.now())
status = model.solve()
print(LpStatus[model.status])
print(f"Objective = {value(model.objective)}")

#%%
# print the results
#for variable in model.variables():
#    print(f"{variable.name} = {variable.varValue}")

#print(f"Objective = {value(model.objective)}")
#print(f"")

#%%
centers = []
for j in range(n_counties):
    if d[j][j].varValue == 1:
        centers.append(j)

districts = {}
for j in centers:
    districts[j] = []
    for i in range(n_counties):
        if d[i][j].varValue == 1:
            districts[j].append(i)

print(districts)

#%%
plot_df = pd.DataFrame()
plot_df['fips'] = county_id_list

print(plot_df)

#%%

assignment = [-1 for u in county_id_list]

u = -1
for j in districts:
    u = u + 1
    print(j, districts[j])
    for i in districts[j]:
        #     print(j, i, county_id_list[i])
        assignment[i] = u

print(assignment)
#%%
plot_df['assignment'] = assignment
print(plot_df)
#%%
f = open('geojson-counties-fips.json')
fullcounties = json.load(f)

fig = px.choropleth(plot_df, geojson=fullcounties, locations='fips', color='assignment',
                    scope="usa",
                    )
fig.update_geos(fitbounds="locations", visible=False)
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
fig.show()

#%%

for n in range(len(assignment)):
    if assignment[n] == -1:
        print(county_id_list[n], counties[county_id_list[n]]['name'])


print(counties[county_id_list[17]]['name'], assignment[17])

#%%
t = 0
for i in range(n_counties):
    print(a[17][i].varValue)
    t = t + a[17][i].varValue
print(t)

#%%
print(counties['39035']['name'])

#%%
print(centers)
print(districts)

for j in centers:
    center_county = counties[county_id_list[j]]['name']
    tp_district = 0
    wp_district = 0
    for i in districts[j]:
        #        print(counties[county_id_list[i]]['name'], ": Pop: ",counties[county_id_list[i]]['Pop_Total'])
        tp_district = tp_district + counties[county_id_list[i]]['Pop_Total'] * a[i][j].varValue
        wp_district = wp_district + counties[county_id_list[i]]['Pop_White'] * a[i][j].varValue
    print(center_county," DistPop: ", tp_district, "WhitePop: ", wp_district, "PctWhite: ", round(wp_district / tp_district,2))