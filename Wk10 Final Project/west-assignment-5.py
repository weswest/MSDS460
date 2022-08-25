import simpy
import numpy as np

#%%
print(simpy.__version__)

#%%

# Define the inputs into the system

DURATION = 1000  #Weeks

# Staff Management Assumptions
# Staff management starts from the presumption the team is under-resourced
# The team grows as new hires are found and shrinks as staff members quit

MODELER_TARGET_TEAM_SIZE = 10
MODELER_START_TEAM_SIZE = 4
MODELER_TO_HIRE_SIZE = MODELER_TARGET_TEAM_SIZE - MODELER_START_TEAM_SIZE

HIRING_MEAN = 20 # Number of weeks on average to find a new hire
HIRING_SDEV = 8 # Variance in time to hire

QUITTING_MEAN = 40 # Number of weeks on average that someone quits
QUITTING_SDEV = 8 # Variance in quitting time

# Model Assumptions
MODELS_TOTAL = 15
MODELS_ACTIVE = 0   # This is a counter to help apportion out models

# Time to build a model from scratch
MODEL_BUILD_MIN_MONTHS = 6
MODEL_BUILD_MAX_MONTHS = 9

MODEL_BUILD_MIN_WEEKS = MODEL_BUILD_MIN_MONTHS * 4
MODEL_BUILD_MAX_WEEKS = MODEL_BUILD_MAX_MONTHS * 4
MODEL_MONITOR_MIN_WEEKS = 3
MODEL_MONITOR_MAX_WEEKS = 5

#%%

# Control functions

# The function below generates a normal distribution, then takes the inverse, then runs a random check
# to see if a uniform number from 0-1 is below the value.
# This allows for us to identify, e.g., that there is an 8-week average time for an event to occur...
# So is THIS the week that will trigger?
def test_normal(mean, stdev):
    normal_value = np.random.normal(mean, stdev)
    inverse_value = 1 / normal_value
    uniform = np.random.uniform(0,1)
    if uniform < inverse_value:
        return True
    else:
        return False

def sample_uniform(min, max):
    return round(np.random.uniform(min-0.5, max+0.5),0)

#%%

def week_control(env, modeler_beach):
    while True:
        print (env.now, "Modeler Beach: Max: ",modeler_beach.capacity, "Current: ", modeler_beach.level)
        print (env.now, "Modeler Hire: Max: ",modeler_hire_pool.capacity, "Current: ", modeler_hire_pool.level)
        yield env.process(staff_management(env))
        yield env.process(build_model('ModelX',DURATION))
        yield env.process(build_model('ModelY',DURATION))

        yield env.timeout(1)

def staff_management(env):
    # This process controls the hiring and quitting of modeling staff.
    # Two potential events can happen: a new employee can be hired, and an existing employee could quit
    # We are tracking two containers: modeler_beach and modeler_to_hire:
        # The beach tracks existing staff levels, "to_hire" is a pool of modelers that we could hire
    #
    # Hiring stage:
    if modeler_hire_pool.level > 0:                     # If there's available capacity to grow the team...
        if test_normal(HIRING_MEAN, HIRING_SDEV):     # Test whether this is the week someone is found
            yield modeler_hire_pool.get(1)              # Take a modeler from the "to be hired" pool
            yield modeler_beach.put(1)                  # And put the modeler in the "hired" pool

    if modeler_beach.level > 0:                               # Staff won't quit in the middle of their work.  Yay.
        if (test_normal(QUITTING_MEAN, QUITTING_SDEV)): # Test whether this is the week someone quits
            yield modeler_beach.get(1)                  # Take an employee out of the hired pool
            yield modeler_hire_pool.put(1)            # Put the modeler in the "to be hired" pool

    staff_count.append(MODELER_TARGET_TEAM_SIZE - modeler_hire_pool.level)
    print(env.now)

def assign_models(env):
    print('In assign_models')
    global MODELS_ACTIVE
    available_modelers = modeler_beach.level
    remaining_models = MODELS_TOTAL - MODELS_ACTIVE
    assignments = min(available_modelers, remaining_models)
    m = build_model('ModelX', DURATION)
    env.process(m)
    print('End of Assign Models')

#def model_monitoring(env, model, time_start, time_end):
#    if env.now < time_start:
#        yield env.timeout(time_start - env.now)
#    with modeler_beach.request() as modeler_request:

def build_model(name, week_deadline):
    print(env.now, ': In Build a',name,'.  Modelers available: ', modeler_beach.level)
    yield modeler_beach.request()
    print(env.now, ': In Build b',name,'.  Modelers available: ', modeler_beach.level)
    yield env.timeout(1)
    print(env.now, ': In Build c',name,'.  Modelers available: ', modeler_beach.level)


#%%
staff_count =[MODELER_START_TEAM_SIZE]
# Create environment and start processes
env = simpy.Environment()
modeler_beach = simpy.Resource(env, capacity = MODELER_TARGET_TEAM_SIZE, init = MODELER_START_TEAM_SIZE)
modeler_hire_pool = simpy.Resource(env, capacity = MODELER_TARGET_TEAM_SIZE, init = (MODELER_TO_HIRE_SIZE))
env.process(week_control(env, modeler_beach))
env.run(until=DURATION)

