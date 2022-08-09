#%%

import regex as re  # regular expresstions used in manipulating output for reporting solution
import pulp # mathematical programming
import math
import pandas as pd
solver = pulp.getSolver("PULP_CBC_CMD")

#%%

label = "Wk4 / HW2 Baseline"

# Identify names of breweries, packagers, and customers
brewery = ['B1', 'B2', 'B3', 'B4']
packager = ['P1', 'P2', 'P3']
customer = ['C01', 'C02', 'C03', 'C04', 'C05', 'C06', 'C07', 'C08', 'C09', 'C10', 'C11', 'C12', 'C13', 'C14', 'C15']

# Define the min and max of brewery and packaging capacity
brewery_min = {'B1': 100,    'B2': 150,    'B3': 200,    'B4': 100,}
brewery_max = {'B1': 2000,    'B2': 2500,    'B3': 3500,    'B4': 2000,}

packager_min = {'P1': 50,   'P2':100,   'P3':150,}
packager_max = {'P1': 500,   'P2':1500,   'P3':2500,}

# Read in the shipping costs, both from brewery to packager and packager to customer
brewery_to_packager_shipping_costs = [
    #P1     P2    P3   Packagers in columns
    [1.55, 0.51, 0.9],  #B1 Breweries in rows
    [0.81, 3.18, 0.65], #B2
    [2.13, 0.97, 0.51], #B3
    [1.23, 2.15, 2.08]  #B4
]

packager_to_customer_shipping_costs = [
    # Each column is customer C1 - C15
    [4.82, 2.05, 4.42, 3.83, 0.97, 3.04, 3.91, 4.03, 5.11, 0.9, 4.39, 0.85, 2.81, 3.94, 1.04], #P1 Packagers
    [1.83, 4.03, 3.95, 4.21, 4.78, 3.2, 1.88, 2.96, 5.11, 2.67, 4.14, 1.22, 5.1, 3.47, 1.92],  #P2
    [2.66, 0.95, 3.94, 2.04, 2.35, 1.42, 3.6, 3.17, 1.34, 4.51, 0.74, 0.94, 1.98, 4.77, 2.04]  #P3
]

# First costs is Brewery --> Packager
first_costs = pulp.makeDict([brewery,packager],brewery_to_packager_shipping_costs,0)

# Second costs is Packager --> Customer
second_costs = pulp.makeDict([packager,customer],packager_to_customer_shipping_costs,0)

# Read in customer order volume

base_demand = {'C01': 48, 'C02': 84, 'C03': 64, 'C04': 106, 'C05': 47,
               'C06': 57, 'C07': 64, 'C08': 93, 'C09': 74,  'C10': 41,
               'C11': 61, 'C12': 42, 'C13': 57, 'C14': 70,  'C15': 41}

demand_multiplier = 1  # default is 1
demand = base_demand # dictionary with the same structure as base demend
for key in list(base_demand.keys()):
    demand[key] = math.ceil(demand_multiplier * base_demand[key])

total_demand = sum(demand.values())

#%%
# Create variables that will actually sit in the PULP problem

# Create list of tuples containing all the possible brewery-to-packager routes for transport
first_routes = [(i,j) for i in brewery for j in packager]
# A dictionary called 'Vars' is created to contain the referenced variables(the routes)
first_vars = pulp.LpVariable.dicts("route",(brewery,packager),0,None,pulp.LpInteger)

# Create list of tuples containing all the possible packager to customer routes for transport
second_routes = [(j,k) for j in packager for k in customer]
# A dictionary called 'Vars' is created to contain the referenced variables(the routes)
second_vars = pulp.LpVariable.dicts("route",(packager,customer),0,None,pulp.LpInteger)

#%%

##
## THIS IS THE CODE TO EXECUTE THE OPTIMIZATION.
## MAKE SURE THAT ALL VARIABLES ARE CODED CORRECTLY BEFORE NOW
##
## THIS IS THE BASE MODEL WITH ALL CONSTRAINTS AS ORIGINALLY SPECIFIED
##

prob = pulp.LpProblem("HW2/Wk4", pulp.LpMinimize)
# Start defining the constraints of the PULP problem

# Ensure brewery min/max production is resolved
for i in brewery:
    prob += (pulp.lpSum([first_vars[i][j] for j in packager])) >= brewery_min[i], "Brewery_Minimum%s" %i
    prob += (pulp.lpSum([first_vars[i][j] for j in packager])) <= brewery_max[i], "Brewery_Maximum%s" %i


# Ensure packager min/max production is resolved
for j in packager:
    prob += (pulp.lpSum([second_vars[j][k] for k in customer])) >= packager_min[j], "Packager_Minimum%s" %j
    prob += (pulp.lpSum([second_vars[j][k] for k in customer])) <= packager_max[j], "Packager_Maximum%s" %j

# Ensure packager locations are net-zero: that inflows from breweries to each packager equals outflows from the packager
for j in packager:
    prob += pulp.lpSum([first_vars[i][j] for i in brewery]) == pulp.lpSum([second_vars[j][k] for k in customer]), "Packager_in_out%s" %j

# Ensure that each customer receives exactly the amount demanded
for k in customer:
    prob += pulp.lpSum([second_vars[j][k] for j in packager]) == demand[k], "Meet_customer_input%s"%k

# Minimize the objective function, which is the sum of transport costs across each path of the network
prob += \
    pulp.lpSum([first_vars[i][j]*first_costs[i][j] for (i,j) in first_routes]) +  \
    pulp.lpSum([second_vars[j][k]*second_costs[j][k] for (j,k) in second_routes]), "All_Tansportation_Costs"

#%%
status = prob.solve()
print(label)

#%%
# print the results
for variable in prob.variables():
    print(f"{variable.name} = {variable.varValue}")

print(f"Objective = {pulp.value(prob.objective)}")
print(f"")

# Printing Reduced Costs
for v in prob.variables():
    print (v.name, "=", v.varValue, "\tReduced Cost =", v.dj)
print(f"")

# Printing Shadow Prices
o = [{'name':name, 'shadow price':c.pi, 'slack':c.slack}
     for name, c in prob.constraints.items()]
print(pd.DataFrame(o))
print(f"")

#%%

# Execute an iteration where Brewery 4 is closed
label = "Wk4 / HW2 Close B4, Demand = 4.7x"

brewery_min = {'B1': 100,    'B2': 150,    'B3': 200,    'B4': 0,}
brewery_max = {'B1': 2000,    'B2': 2500,    'B3': 3500,    'B4': 0,}

##
## THIS IS THE CODE TO EXECUTE THE OPTIMIZATION.
## MAKE SURE THAT ALL VARIABLES ARE CODED CORRECTLY BEFORE NOW
##
## THIS IS THE BASE MODEL WITH ALL CONSTRAINTS AS ORIGINALLY SPECIFIED
##

prob = pulp.LpProblem("HW2/Wk4", pulp.LpMinimize)
# Start defining the constraints of the PULP problem

# Ensure brewery min/max production is resolved
for i in brewery:
    prob += (pulp.lpSum([first_vars[i][j] for j in packager])) >= brewery_min[i], "Brewery_Minimum%s" %i
    prob += (pulp.lpSum([first_vars[i][j] for j in packager])) <= brewery_max[i], "Brewery_Maximum%s" %i


# Ensure packager min/max production is resolved
for j in packager:
    prob += (pulp.lpSum([second_vars[j][k] for k in customer])) >= packager_min[j], "Packager_Minimum%s" %j
    prob += (pulp.lpSum([second_vars[j][k] for k in customer])) <= packager_max[j], "Packager_Maximum%s" %j

# Ensure packager locations are net-zero: that inflows from breweries to each packager equals outflows from the packager
for j in packager:
    prob += pulp.lpSum([first_vars[i][j] for i in brewery]) == pulp.lpSum([second_vars[j][k] for k in customer]), "Packager_in_out%s" %j

# Ensure that each customer receives exactly the amount demanded
for k in customer:
    prob += pulp.lpSum([second_vars[j][k] for j in packager]) == demand[k], "Meet_customer_input%s"%k

# Minimize the objective function, which is the sum of transport costs across each path of the network
prob += \
    pulp.lpSum([first_vars[i][j]*first_costs[i][j] for (i,j) in first_routes]) + \
    pulp.lpSum([second_vars[j][k]*second_costs[j][k] for (j,k) in second_routes]), "All_Tansportation_Costs"


status = prob.solve()
print(label)


# print the results
for variable in prob.variables():
    print(f"{variable.name} = {variable.varValue}")

print(f"Objective = {pulp.value(prob.objective)}")
print(f"")

#%%
# Execute an iteration where Brewery 4 is closed
label = "Wk4 / HW2 Keep All Breweries Open, Demand = 4.7x"

brewery_min = {'B1': 100,    'B2': 150,    'B3': 200,    'B4': 100,}
brewery_max = {'B1': 2000,    'B2': 2500,    'B3': 3500,    'B4': 2000,}

demand_multiplier = 4.7  # default is 1
demand = base_demand # dictionary with the same structure as base demend
for key in list(base_demand.keys()):
    demand[key] = math.ceil(demand_multiplier * base_demand[key])

total_demand = sum(demand.values())


##
## THIS IS THE CODE TO EXECUTE THE OPTIMIZATION.
## MAKE SURE THAT ALL VARIABLES ARE CODED CORRECTLY BEFORE NOW
##
## THIS IS THE BASE MODEL WITH ALL CONSTRAINTS AS ORIGINALLY SPECIFIED
##

prob = pulp.LpProblem("HW2/Wk4", pulp.LpMinimize)
# Start defining the constraints of the PULP problem

# Ensure brewery min/max production is resolved
for i in brewery:
    prob += (pulp.lpSum([first_vars[i][j] for j in packager])) >= brewery_min[i], "Brewery_Minimum%s" %i
    prob += (pulp.lpSum([first_vars[i][j] for j in packager])) <= brewery_max[i], "Brewery_Maximum%s" %i


# Ensure packager min/max production is resolved
for j in packager:
    prob += (pulp.lpSum([second_vars[j][k] for k in customer])) >= packager_min[j], "Packager_Minimum%s" %j
    prob += (pulp.lpSum([second_vars[j][k] for k in customer])) <= packager_max[j], "Packager_Maximum%s" %j

# Ensure packager locations are net-zero: that inflows from breweries to each packager equals outflows from the packager
for j in packager:
    prob += pulp.lpSum([first_vars[i][j] for i in brewery]) == pulp.lpSum([second_vars[j][k] for k in customer]), "Packager_in_out%s" %j

# Ensure that each customer receives exactly the amount demanded
for k in customer:
    prob += pulp.lpSum([second_vars[j][k] for j in packager]) == demand[k], "Meet_customer_input%s"%k

# Minimize the objective function, which is the sum of transport costs across each path of the network
prob += \
    pulp.lpSum([first_vars[i][j]*first_costs[i][j] for (i,j) in first_routes]) + \
    pulp.lpSum([second_vars[j][k]*second_costs[j][k] for (j,k) in second_routes]), "All_Tansportation_Costs"


status = prob.solve()
print(label)


# print the results
for variable in prob.variables():
    print(f"{variable.name} = {variable.varValue}")

print(f"Objective = {pulp.value(prob.objective)}")
print(f"")