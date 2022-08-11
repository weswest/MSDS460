import pandas as pd
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
from fitter import Fitter, get_common_distributions
import random
import simpy

seed = 460  # Set the random seed for the assignment

#%%
# Note: per this link: https://www.weather.gov/climateservices/nowdatafaq
# It seems that the data below is going to be the rainfall measured in inches

df_rainfall = pd.read_csv ('monthly-rainfall-data.csv')

print(df_rainfall.head())
print(df_rainfall.columns)
df_rainfall.set_index('Year', inplace=True)
print(df_rainfall.head())
print(df_rainfall.columns)

#%%
months = list(df_rainfall.columns)
print(months)

#%%
plot_rainfallmonthly = df_rainfall.boxplot(column=months)
print(plot_rainfallmonthly)
plt.title('Monthly Rainfall 2000-2011 Box-Whisker')
fig = plt.gcf()
fig.savefig('MonthlyRainfall.png')
#%%

df_rainfall_values = df_rainfall.melt()['value']
#print(df_rainfall_values)
rf_mu, rf_std = stats.norm.fit(df_rainfall_values)
print(rf_mu, rf_std)

rf_hist = plt.hist(df_rainfall_values, bins=50, density=True, alpha=0.6, color='b')

plt.show()
#%%
print(type(df_rainfall_values))
pd.set_option('display.max_rows', None)
print(df_rainfall_values.sort_values())
pd.set_option('display.max_rows', 10)



#%%
###
# Figure out which distribution fits the data the best
# Note: hat tip to https://medium.com/the-researchers-guide/finding-the-best-distribution-that-fits-your-data-using-pythons-fitter-library-319a5a0972e9
###

df = df_rainfall_values.copy()

print(df)
f = Fitter(df,
           distributions= get_common_distributions())
f.fit()
print(f.summary())

#%%
# Note: gamma fits the best
# The code below extracts the data-fit gamma distribution of alpha and scale / beta
# Note that location is essentially 0.

rf_gamma = f.get_best(method = 'sumsquare_error')['gamma']
print(rf_gamma)

alpha = rf_gamma['a']
shape = alpha
loc = rf_gamma['loc']
scale = rf_gamma['scale']
beta = 1 / scale

sample_gamma = random.gammavariate(alpha, beta)
print('Gamma: ', sample_gamma)

#%%
s = np.random.gamma(shape, scale, 10000)
s_avg = sum(s) / 10000
print(s_avg)

#%%
# As some back of the envelope math:
#   Cross-referencing with this site: http://gradybarrels.com/how_much_rain_can_i_collect.html
#   It seems that each square foot can capture ~0.6 gallons of rain
#   So if the problem statement shows a roof of 3k sqft, then each inch of rain will capture ~1800 gallons
#   Note: the average rain catchment from the data shows an average of 2.3, whereas the gamma sample avg is 1.9
# So the data itself would show ~4000 gal / month (2.3 x 1800) while the sample distribution shows ~3400 gal / month
#%%

# Scenario creation

# Every month, our Texas ranch uses a volume of water to water the crops.  This depletes the water reservoir
# Also, each month, our ranch's water reservoir is replenished with this month's rain.
# The reservoir is replenished based on four dynamics:
# 1. What was this month's rainfall?  <-- Gamma distribution based on 2000-2011 historic rainfall
# 2. How effective was our catchment system <-- From 90-98% effective.  Assume a uniform distribution
# 3. How big was our catchment system <-- Set at 3,000 sqft.  Although the Rancher may want to expand
# 4. How big is our water tank, and is it full? <-- Set at 25k gallons.

# And then every month the field needs anywhere from 4,000 - 5,200 gallons of water.  Assume uniform distribution.

WATER_TANK_SIZE = 25000 # Gallons
WATER_TANK_INIT = 10000 # Gallons.  Per the problem, presume we start with 10k gal of water
CATCHMENT_EFFICIENCY = [90,98] # Ranges between 90 and 98%
CATCHMENT_SIZE = 30000 # Sq. Ft.  Note the conversion provided in the assignment
CUBIC_FT_TO_GAL = 7.48 # Input given by the problem
WATER_USAGE = [4000, 5200] # Range of water used to water crops each month
DURATION = 360 # Number of months in the 30 year forecast
ITERATIONS = 1000 # Number of scenario runs executed
#DURATION = 5 # placeholder as a debugger

# Delivery agent will bring water every month
# Retrieval agent will take water every month
# The water tank is a storage facility

def monthly_rain(name, env):
    """ Every month a volume of rain falls.  The rain is put into the storage tank"""

    rainfall_level_inches = random.gammavariate(shape, scale)
    rainfall_catchment_pct = random.randint(*CATCHMENT_EFFICIENCY) / 100
    rainfall_capture_inches = rainfall_level_inches * rainfall_catchment_pct
    rainfall_capture_cubicft = rainfall_capture_inches * CATCHMENT_SIZE / 12
    rainfall_capture_gallons = rainfall_capture_cubicft * CUBIC_FT_TO_GAL
#    print('Debug:')
#    print('rainfall_level_inches: ', rainfall_level_inches)
#    print('rainfall_catchment_pct: ', rainfall_catchment_pct)
#    print('rainfall_capture_inches: ', rainfall_capture_inches)
#    print('rainfall_capture_cubicft: ', rainfall_capture_cubicft)
#    print('rainfall_capture_gallons: ', rainfall_capture_gallons)
    tank_gap = water_tank.capacity - water_tank.level
    amount = min(tank_gap, rainfall_capture_gallons) # This ensures the tank won't overflow
    yield water_tank.put(amount)

def monthly_watering(name, env):
    water_used = random.randint(*WATER_USAGE)
#    print('Water used: ', water_used)
    yield water_tank.get(water_used)

def month_control(env, water_tank):
    while True:
        """Drive the monthly process of triggering monthly rains and then triggering monthly crop watering"""
#        print('Water in tank: ', water_tank.level, 'Calling rain and watering at %d' % env.now)
        yield env.process(monthly_rain('Rain %d' % env.now, env))
        yield env.process(monthly_watering('Water %d' % env.now, env))
#        print('Finished rain and watering at %d' % env.now)
#        print('Water left in the tank:', water_tank.level)
        iter_tanklevel[env.now + 1] = water_tank.level
        yield env.timeout(1)

#%%
df_tanklevel = pd.DataFrame()
for i in range(1,ITERATIONS+1):

    # Create environment and start processes
    env = simpy.Environment()
    #gas_station = simpy.Resource(env, 2)
    #fuel_pump = simpy.Container(env, GAS_STATION_SIZE, init=GAS_STATION_SIZE)
    water_tank = simpy.Container(env, WATER_TANK_SIZE, init = WATER_TANK_INIT)
    env.process(month_control(env, water_tank))
    #env.process(car_generator(env, gas_station, fuel_pump))

    # Execute!
    iter_tanklevel = []
    iter_tanklevel = [0] * (DURATION+1)
    iter_tanklevel[0] = WATER_TANK_INIT
    env.run(until=DURATION)
#    print('Scenario ran until: ', env.now)
    col_name = 'Iter%d' % i
    df_tanklevel[col_name] = iter_tanklevel
    if i % 50 == 0:
        print('On scenario # %d' % i)

print(df_tanklevel)

#%%

