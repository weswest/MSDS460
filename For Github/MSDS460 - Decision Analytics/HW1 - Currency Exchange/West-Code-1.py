#%%

#import pulp
from pulp import LpVariable, LpProblem, LpMaximize, LpStatus, value, LpMinimize, makeDict, lpSum
import numpy as np

#%%
# Create functions that spit out results of the model of end currencies

def calcEnd(curr):
    val = start_vol[curr]
    for t in Currencies:
        val = val - vars[curr][t].varValue
    for f in Currencies:
        val = val + Exchange[f][curr] * vars[f][curr].varValue
    return val

def printEnd(curr):
    print (curr, "In USD:", Exchange[curr]['USD'] * calcEnd(curr), "; Original currency: ", calcEnd(curr))


#%%
##
# Problem Setup

# define inputs

label = "Wk2 / HW1 Scenario 1"

Currencies = ['USD', 'EUR', 'GBP', 'HKD', 'JPY']

# Baldwin’s current portfolio of cash holdings includes 2 million USD, 5 million EUR, 1 million GBP, 3 million HKD, and 30 million JPY.
start_vol = {
    'USD': 2000000,
    'EUR': 5000000,
    'GBP': 1000000,
    'HKD': 3000000,
    'JPY': 30000000,
}

exch_df = [# To Currency
    # USD       EUR         GBP         HKD         JPY
    [1,        1.01864,    0.6409,     7.7985,     118.55],  # From USD
    [0.9724,   1,          0.6295,     7.6552,     116.41],  # From EUR
    [1.5593,   1.5881,     1,          12.154,     184.97],  # From GBP
    [0.12812,  0.1304,     0.0821,     1,          15.1005], # From HKD
    [0.00843,  0.00856,    0.0054,     0.0658,     1],       # From JPY
]


Exchange = makeDict([Currencies, Currencies], exch_df, 0)
Pairs = [(f, t) for f in Currencies for t in Currencies]


# Wes has asked you to design a currency trading plan that would
# increase Baldwin’s euro and yen holdings to 8 million EUR and 54 JPY, respectively,
# while maintaining the equivalent of at least $250,000 USD in each currency.

# Define goal EUR and JPY:

goal_EUR = 8000000
goal_JPY = 54000000

# Define minima in USD:
min_USD = 250000
min_EUR = 250000
min_GBP = 250000
min_HKD = 250000
min_JPY = 250000

#%%

# define the problem
# Note: we are trying to maximize the USD-denominated holdings,
# which minimizes the currency exchange fee
prob1 = LpProblem('Cheapest Currency Exchange', LpMaximize)
# Note, LpMaximize for a maximization problem,
# and LpMinimize for a minimization problem

# define variables

vars = LpVariable.dicts('Flow', (Currencies, Currencies), 0, None)

# Define objective Function
# Structure of the objective function is to sum all end currencies and convert to USD

# Define Interim Variables (the end-state currencies, derived by calculating starting currency and then managing in/outflows
end_USD = lpSum(
    [start_vol['USD'], # Starting volume
     [-1*vars['USD'][t] for t in Currencies], # Outflows, in the country's currency
     [Exchange[f]['USD'] * vars[f]['USD'] for f in Currencies] #Inflows, exchanged from originating currency to country's currency
     ])

end_EUR = lpSum(
    [start_vol['EUR'], # Starting volume
     [-1*vars['EUR'][t] for t in Currencies], # Outflows, in the country's currency
     [Exchange[f]['EUR'] * vars[f]['EUR'] for f in Currencies] #Inflows, exchanged from originating currency to country's currency
     ])

end_GBP = lpSum(
    [start_vol['GBP'], # Starting volume
     [-1*vars['GBP'][t] for t in Currencies], # Outflows, in the country's currency
     [Exchange[f]['GBP'] * vars[f]['GBP'] for f in Currencies] #Inflows, exchanged from originating currency to country's currency
     ])

end_HKD = lpSum(
    [start_vol['HKD'], # Starting volume
     [-1*vars['HKD'][t] for t in Currencies], # Outflows, in the country's currency
     [Exchange[f]['HKD'] * vars[f]['HKD'] for f in Currencies] #Inflows, exchanged from originating currency to country's currency
     ])

end_JPY = lpSum(
    [start_vol['JPY'], # Starting volume
     [-1*vars['JPY'][t] for t in Currencies], # Outflows, in the country's currency
     [Exchange[f]['JPY'] * vars[f]['JPY'] for f in Currencies] #Inflows, exchanged from originating currency to country's currency
     ])

# Constraints.  These are the goal currencies
prob1 += end_EUR >= goal_EUR
prob1 += end_JPY >= goal_JPY

# Constraints.  These are the minimum currencies.  Note that the goal currencies above are more constraining for EUR/JPY than below
prob1 += Exchange['USD']['USD'] * end_USD >= min_USD
prob1 += Exchange['EUR']['USD'] * end_EUR >= min_EUR
prob1 += Exchange['GBP']['USD'] * end_GBP >= min_GBP
prob1 += Exchange['HKD']['USD'] * end_HKD >= min_HKD
prob1 += Exchange['JPY']['USD'] * end_JPY >= min_JPY

# Objective function.  This takes all of the end currency volumes and pushes them back to USD, then sums
prob1 += lpSum([
    [Exchange['USD']['USD'] * end_USD],
    [Exchange['EUR']['USD'] * end_EUR],
    [Exchange['GBP']['USD'] * end_GBP],
    [Exchange['HKD']['USD'] * end_HKD],
    [Exchange['JPY']['USD'] * end_JPY]
])


# Print Results

status = prob1.solve()
print(label)

# print the results
for variable in prob1.variables():
    print(f"{variable.name} = {variable.varValue}")

print(f"Objective = {value(prob1.objective)}")
print(f"")

for c in Currencies:
    printEnd(c)

print(f"status={LpStatus[status]}")



#%%
# Part 4: 4. Suppose another executive thinks that holding $250,000 USD in each currency is excessive
# and wants to lower the amount to $50,000 USD in each currency.
# Does this help to lower the transaction cost? Why or why not?

label = "Wk2 / HW1 Scenario 2"

# Define new minima in USD:
min_USD = 50000
min_EUR = 50000
min_GBP = 50000
min_HKD = 50000
min_JPY = 50000

# define the problem
prob1 = LpProblem('Cheapest Currency Exchange', LpMaximize)
# Note, LpMaximize for a maximization problem,
# and LpMinimize for a minimization problem

# define variables

vars = LpVariable.dicts('Flow', (Currencies, Currencies), 0, None)

# Define objective Function
# Structure of the objective function is to sum all end currencies and convert to USD


# Define Interim Variables (the end-state currencies, derived by calculating starting currency and then managing in/outflows
end_USD = lpSum(
    [start_vol['USD'], # Starting volume
     [-1*vars['USD'][t] for t in Currencies], # Outflows, in the country's currency
     [Exchange[f]['USD'] * vars[f]['USD'] for f in Currencies] #Inflows, exchanged from originating currency to country's currency
     ])

end_EUR = lpSum(
    [start_vol['EUR'], # Starting volume
     [-1*vars['EUR'][t] for t in Currencies], # Outflows, in the country's currency
     [Exchange[f]['EUR'] * vars[f]['EUR'] for f in Currencies] #Inflows, exchanged from originating currency to country's currency
     ])

end_GBP = lpSum(
    [start_vol['GBP'], # Starting volume
     [-1*vars['GBP'][t] for t in Currencies], # Outflows, in the country's currency
     [Exchange[f]['GBP'] * vars[f]['GBP'] for f in Currencies] #Inflows, exchanged from originating currency to country's currency
     ])

end_HKD = lpSum(
    [start_vol['HKD'], # Starting volume
     [-1*vars['HKD'][t] for t in Currencies], # Outflows, in the country's currency
     [Exchange[f]['HKD'] * vars[f]['HKD'] for f in Currencies] #Inflows, exchanged from originating currency to country's currency
     ])

end_JPY = lpSum(
    [start_vol['JPY'], # Starting volume
     [-1*vars['JPY'][t] for t in Currencies], # Outflows, in the country's currency
     [Exchange[f]['JPY'] * vars[f]['JPY'] for f in Currencies] #Inflows, exchanged from originating currency to country's currency
     ])

# Constraints.  These are the goal currencies
prob1 += end_EUR >= goal_EUR
prob1 += end_JPY >= goal_JPY

# Constraints.  These are the minimum currencies.  Note that the goal currencies above are more constraining for EUR/JPY than below
prob1 += Exchange['USD']['USD'] * end_USD >= min_USD
prob1 += Exchange['EUR']['USD'] * end_EUR >= min_EUR
prob1 += Exchange['GBP']['USD'] * end_GBP >= min_GBP
prob1 += Exchange['HKD']['USD'] * end_HKD >= min_HKD
prob1 += Exchange['JPY']['USD'] * end_JPY >= min_JPY

# Objective function.  This takes all of the end currency volumes and pushes them back to USD, then sums
prob1 += lpSum([
    [Exchange['USD']['USD'] * end_USD],
    [Exchange['EUR']['USD'] * end_EUR],
    [Exchange['GBP']['USD'] * end_GBP],
    [Exchange['HKD']['USD'] * end_HKD],
    [Exchange['JPY']['USD'] * end_JPY]
])


# Print Results

status = prob1.solve()
print(label)

# print the results
for variable in prob1.variables():
    print(f"{variable.name} = {variable.varValue}")

print(f"Objective = {value(prob1.objective)}")
print(f"")

for c in Currencies:
    printEnd(c)

print(f"status={LpStatus[status]}")

#%%

# Part 5:

exch_df = [# To Currency
    # USD       EUR         GBP         HKD         JPY
    [1,        1.01864,    0.6414,     7.7985,     118.55],  # From USD
    [0.9724,   1,          0.6295,     7.6552,     116.41],  # From EUR
    [1.5593,   1.5881,     1,          12.154,     184.97],  # From GBP
    [0.12812,  0.1304,     0.0821,     1,          15.1005], # From HKD
    [0.00843,  0.00856,    0.0054,     0.0658,     1],       # From JPY
]
Exchange = makeDict([Currencies, Currencies], exch_df, 0)

# Reset minima to the original $250k (note: this doesn't matter, given the problem introduced above but c'est la vie):
min_USD = 250000
min_EUR = 250000
min_GBP = 250000
min_HKD = 250000
min_JPY = 250000

label = "Week 2 / HW 1 Scenario 5"

# define the problem
prob1 = LpProblem('Cheapest Currency Exchange', LpMaximize)
# Note, LpMaximize for a maximization problem,
# and LpMinimize for a minimization problem

# define variables

vars = LpVariable.dicts('Flow', (Currencies, Currencies), 0, None)

# Define objective Function
# Structure of the objective function is to sum all end currencies and convert to USD


# Define Interim Variables (the end-state currencies, derived by calculating starting currency and then managing in/outflows
end_USD = lpSum(
    [start_vol['USD'], # Starting volume
     [-1*vars['USD'][t] for t in Currencies], # Outflows, in the country's currency
     [Exchange[f]['USD'] * vars[f]['USD'] for f in Currencies] #Inflows, exchanged from originating currency to country's currency
     ])

end_EUR = lpSum(
    [start_vol['EUR'], # Starting volume
     [-1*vars['EUR'][t] for t in Currencies], # Outflows, in the country's currency
     [Exchange[f]['EUR'] * vars[f]['EUR'] for f in Currencies] #Inflows, exchanged from originating currency to country's currency
     ])

end_GBP = lpSum(
    [start_vol['GBP'], # Starting volume
     [-1*vars['GBP'][t] for t in Currencies], # Outflows, in the country's currency
     [Exchange[f]['GBP'] * vars[f]['GBP'] for f in Currencies] #Inflows, exchanged from originating currency to country's currency
     ])

end_HKD = lpSum(
    [start_vol['HKD'], # Starting volume
     [-1*vars['HKD'][t] for t in Currencies], # Outflows, in the country's currency
     [Exchange[f]['HKD'] * vars[f]['HKD'] for f in Currencies] #Inflows, exchanged from originating currency to country's currency
     ])

end_JPY = lpSum(
    [start_vol['JPY'], # Starting volume
     [-1*vars['JPY'][t] for t in Currencies], # Outflows, in the country's currency
     [Exchange[f]['JPY'] * vars[f]['JPY'] for f in Currencies] #Inflows, exchanged from originating currency to country's currency
     ])

# Constraints.  These are the goal currencies
prob1 += end_EUR >= goal_EUR
prob1 += end_JPY >= goal_JPY

# Constraints.  These are the minimum currencies.  Note that the goal currencies above are more constraining for EUR/JPY than below
prob1 += Exchange['USD']['USD'] * end_USD >= min_USD
prob1 += Exchange['EUR']['USD'] * end_EUR >= min_EUR
prob1 += Exchange['GBP']['USD'] * end_GBP >= min_GBP
prob1 += Exchange['HKD']['USD'] * end_HKD >= min_HKD
prob1 += Exchange['JPY']['USD'] * end_JPY >= min_JPY

# Objective function.  This takes all of the end currency volumes and pushes them back to USD, then sums
prob1 += lpSum([
    [Exchange['USD']['USD'] * end_USD],
    [Exchange['EUR']['USD'] * end_EUR],
    [Exchange['GBP']['USD'] * end_GBP],
    [Exchange['HKD']['USD'] * end_HKD],
    [Exchange['JPY']['USD'] * end_JPY]
])


# Print Results

status = prob1.solve()
print(label)

# print the results
for variable in prob1.variables():
    print(f"{variable.name} = {variable.varValue}")

print(f"Objective = {value(prob1.objective)}")
print(f"")

for c in Currencies:
    printEnd(c)

print(f"status={LpStatus[status]}")