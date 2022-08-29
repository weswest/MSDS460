import simpy
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statistics import mean


#%%

# Define the inputs into the system

DURATION = 520  #Weeks.  10 year simulation

# Staff Management Assumptions
# Staff management starts from the presumption the team is under-resourced
# The team grows as new hires are found and shrinks as staff members quit

MODELER_TARGET_TEAM_SIZE = 15
MODELER_START_TEAM_SIZE = 4
MODELER_TO_HIRE_SIZE = MODELER_TARGET_TEAM_SIZE - MODELER_START_TEAM_SIZE
staff_count =[MODELER_START_TEAM_SIZE]

HIRING_MEAN = 26 # Number of weeks on average to find a new hire
HIRING_SDEV = 8 # Variance in time to hire

QUITTING_MEAN = 39 # Number of weeks on average that someone quits
QUITTING_SDEV = 13 # Variance in quitting time

# Model Assumptions
MODELS_TOTAL = 15

# Time to build a model from scratch
MODEL_BUILD_MIN_MONTHS = 6
MODEL_BUILD_MAX_MONTHS = 12

MODEL_BUILD_MIN_WEEKS = MODEL_BUILD_MIN_MONTHS * 4
MODEL_BUILD_MAX_WEEKS = MODEL_BUILD_MAX_MONTHS * 4
MODEL_MONITOR_MIN_WEEKS = 4
MODEL_MONITOR_MAX_WEEKS = 6

# Set up the priorities for different tasks to track
priority_hire = 0
priority_fire = 0
priority_build = 3
priority_monitor = 2
priority_rebuild = 1

scenario_name = 'T%dM%d_%d%d%d%d' % (MODELER_TARGET_TEAM_SIZE, MODELS_TOTAL, MODEL_BUILD_MIN_MONTHS,
                                        MODEL_BUILD_MAX_MONTHS, MODEL_MONITOR_MIN_WEEKS, MODEL_MONITOR_MAX_WEEKS)

#%%

# Control functions

def test_normal(mean, stdev):
    # The function below generates a normal distribution, then takes the inverse, then runs a random check
    # to see if a uniform number from 0-1 is below the value.
    # This allows for us to identify, e.g., that there is an 8-week average time for an event to occur...
    # So is THIS the week that will trigger?

    normal_value = np.random.normal(mean, stdev)
    inverse_value = 1 / normal_value
    uniform = np.random.uniform(0,1)
    if uniform < inverse_value:
        return True
    else:
        return False

def sample_uniform(min, max):
    # This function takes in a min and max range and spits out a random selection
    # The +/- 0.5 is to ensure equal representation for the endcap values
    return round(np.random.uniform(min-0.5, max+0.5),0)

def target_quarter(today, num_quarters_from_now):
    # Function takes in the current week number and spits out the start of a future quarter
    days_into_quarter = today % 13
    target_date = today - days_into_quarter + num_quarters_from_now * 13 + 1
    return(target_date)

def weeks_until_target_quarter(today, num_quarters_from_now):
    target_week = target_quarter(today, num_quarters_from_now)
    return(target_week - today)

#%%

def setup_staff(env):
    # We have a certain number of modelers as resources, with the resource volume defined as target team size
    # However, when we start our simulation we aren't at target team size
    # So we do this initial setup to essentially "fire" all of the excess employees
    num_modelers_to_fire = MODELER_TO_HIRE_SIZE
    for i in range(num_modelers_to_fire):
        env.process(fire_staff(env))
    yield env.timeout(0)


def fire_staff(env):
    global counter_fired, counter_hired
    with modeler_beach.request(priority=priority_fire) as req:
        yield req
        counter_fired = counter_fired + 1
        weeks_remaining = max(1,round(np.random.normal(HIRING_MEAN, HIRING_SDEV),0))
#        print('Fired staff.  Will hire again in # weeks:', weeks_remaining)
        # Note: we use the hiring mean/sdev because that's the time necessary to hire a fired employee
        yield env.timeout(weeks_remaining)
        counter_hired = counter_hired + 1
#        print('Hired a new employee at time ', env.now)

def staff_management(env):
    # This process controls the hiring and quitting of modeling staff.
    # Two potential events can happen: a new employee can be hired, and an existing employee could quit
    # We are tracking two containers: modeler_beach and modeler_to_hire:
    # The beach tracks existing staff levels, "to_hire" is a pool of modelers that we could hire
    #
    while True:
        if (test_normal(QUITTING_MEAN, QUITTING_SDEV)):     # Test whether this is the week someone quits
#            print('A modeler just quit!  Sad face')
            env.process(fire_staff(env))
        yield env.timeout(1)

class Model(object):
    def __init__(self, env, name):
        self.env = env
        self.name = name

        self.process = env.process(self.build_model(name, 'build', 5, DURATION, priority_build))

    def build_model(self, name, build_or_rebuild, week_start_after, week_start_by, given_priority):
        # Name is self-evident.  It's the model number
        # Build or rebuild is just a text field to help with reporting.  Has no impact on anything
        # week_start_after is the number in the simulation when the model can begin being worked on.
        #   Note that this needs to get translated into a "weeks from now" measure for use in simpy
        # week_start_by is the number in the simulation when the model must start being worked on otherwise
        #   There's a risk that the model won't be done in time
        # Given Priority is a variable set earlier.  Build is lowest priority, then monitor, then rebuild

        # Translate the week variables from straight periods in the simulation to "weeks from now"
        global counter_models_completed, counter_failed_rebuilds
        weeks_until_start = max(0, week_start_after - env.now)
        weeks_until_deadline = max(0, week_start_by - env.now - MODEL_BUILD_MAX_WEEKS)
#        print('In Build Model.  Modelers available: ', modeler_beach.capacity - modeler_beach.count)
        yield env.timeout(weeks_until_start)
        with modeler_beach.request(priority=given_priority) as req:
            results = yield req | env.timeout(weeks_until_deadline)
            if req in results:
                model_build_weeks = sample_uniform(MODEL_BUILD_MIN_WEEKS, MODEL_BUILD_MAX_WEEKS)
#                print('%d: Modeler assigned to %s %s for %d weeks' % (env.now, build_or_rebuild, name, model_build_weeks))
#                print('There are now %d modelers' % (modeler_beach.capacity - modeler_beach.count))
                yield env.timeout(model_build_weeks)
                yield modeler_beach.release(req)
#                print('%d: %s %s complete; modeler released' % (env.now, build_or_rebuild, name))
#                print('There are now %d modelers' % (modeler_beach.capacity - modeler_beach.count))
                # If this was a build (and not a rebuild), increment the models active counter
                if build_or_rebuild == 'build':
                    counter_models_completed += 1
                # Next set of code sets up rebuilding the model
                # Rebuilding the model builds a number of follow-up events:
                #   1. A Rebuild Model step, which can start 6 quarters from now and needs to end by 12 quarters from now
                s_delay = 6
                e_delay = 12
                #   2. Six Monitor Models steps, which need to start in each of the following quarters and end by quarter-end

                # 1. Rebuild Model step
                # Figure out the inputs
                # 1a. If the model is finished in, say, quarter 3, then new model can start being worked on
                #     at the beginning of quarter 10 and must be finished by the start of quarter 16
                rebuild_start_after = target_quarter(env.now,s_delay + 1)
                rebuild_finish_by = target_quarter(env.now, e_delay + 1)
                rebuild = self.build_model(name, 'rebuild',rebuild_start_after, rebuild_finish_by, priority_rebuild)
                for i in range(1, s_delay+1):
#                    print('In monitoring loop for %s,  step # %d' %(name, i))
                    monitor_start_after = target_quarter(env.now, 1)
                    monitor_finish_by = target_quarter(env.now, 2)
                    monitor = self.monitor_model(name, monitor_start_after, monitor_finish_by, priority_monitor)
                    yield env.process(monitor)
                yield env.process(rebuild)

            else:
                counter_failed_rebuilds += 1
#                print('%s failed to be worked on in the deadline. %d total failed rebuilds' % (name, counter_failed_rebuilds))

    def monitor_model(self, name, week_start_after, week_start_by, given_priority):
        global counter_failed_monitors
        # Monitor model doesn't carry the baggage of triggering follow-on events
        # So the drivers are very similar to what we see in the build model world
        weeks_until_start = max(0, week_start_after - env.now)
        weeks_until_deadline = max(0, week_start_by - env.now - MODEL_MONITOR_MAX_WEEKS)
#        print('In Monitor %s.  Modelers available: %d' %( name, modeler_beach.capacity - modeler_beach.count))
        yield env.timeout(weeks_until_start)
        with modeler_beach.request(priority=given_priority) as req:
            results = yield req | env.timeout(weeks_until_deadline)
            if req in results:
                model_monitor_weeks = sample_uniform(MODEL_MONITOR_MIN_WEEKS, MODEL_MONITOR_MAX_WEEKS)
#                print('%d: Modeler assigned to MONITOR %s for %d weeks' % (env.now, name, model_monitor_weeks))
#                print('There are now %d modelers' % (modeler_beach.capacity - modeler_beach.count))
                yield env.timeout(model_monitor_weeks)
                yield modeler_beach.release(req)
#                print('%d: MONITOR %s complete; modeler released' % (env.now, name))
#                print('There are now %d modelers' % (modeler_beach.capacity - modeler_beach.count))

            else:
#                print('%s failed to be monitored in the deadline' % name)
                counter_failed_monitors += 1


def weekly_reporting(env):
    global bool_models_all_built, time_models_completed
    while True:
        available_modelers = modeler_beach.capacity - modeler_beach.count
        ds_available_modelers.append(available_modelers)
        if counter_models_completed == MODELS_TOTAL:
            ds_available_modelers_at_full_modeling.append(available_modelers)

            if bool_models_all_built == False:
                bool_models_all_built = True
                time_models_completed = env.now

        ds_models_completed.append(counter_models_completed)
        ds_hired.append(counter_hired)
        ds_fired.append(counter_fired)
        yield env.timeout(1)

#%%
# Create environment and start processes
ds_iter_hired = []
ds_iter_fired = []
ds_iter_failed_rebuilds = []
ds_iter_failed_monitors = []
ds_iter_failed_monitor_pct = []
ds_iter_end_period = []
ds_iter_capacity = []

iter = 1000

for i in range(iter):
    if i % 50 == 0:
        print('Iteration %d' % i)
    # Setup counters etc
    # Reporting Metrics
    counter_fired = 0
    counter_hired = 0
    counter_failed_rebuilds = 0
    counter_failed_monitors = 0
    counter_models_completed = 0
    bool_models_all_built = False
    time_models_completed = DURATION

    ds_fired = [0]
    ds_hired = [0]
    ds_models_completed = [0]
    ds_available_modelers = [0]
    ds_available_modelers_at_full_modeling = [0]

    # Run environment
    env = simpy.Environment()
    modeler_beach = simpy.PriorityResource(env, capacity = MODELER_TARGET_TEAM_SIZE)
    env.process(setup_staff(env))
    env.process(staff_management(env))
    env.process(weekly_reporting(env))
    models = [Model(env, 'Model %d' % i) for i in range(1,MODELS_TOTAL+1)]
    env.run(until=DURATION)

    # Report results
#    avg_capacity = round(mean(ds_available_modelers),3)
    avg_capacity_at_full_modeling = round(mean(ds_available_modelers_at_full_modeling),3)

    monitor_attempts = MODELS_TOTAL * ((DURATION / 52) - 1) * 4
    failed_monitor_percentage = round(counter_failed_monitors / monitor_attempts,2)

    ds_iter_hired.append(counter_hired)
    ds_iter_fired.append(counter_fired)
    ds_iter_failed_rebuilds.append(counter_failed_rebuilds)
    ds_iter_failed_monitors.append(counter_failed_monitors)
    ds_iter_failed_monitor_pct.append(failed_monitor_percentage)
    ds_iter_end_period.append(time_models_completed)
    ds_iter_capacity.append(avg_capacity_at_full_modeling)

#    print('hired / fired', counter_hired, counter_fired)
#    print('Failed rebuilds / monitors', counter_failed_rebuilds, counter_failed_monitors)
#    print('Failed monitor percentage', failed_monitor_percentage, monitor_attempts)
#    print('Did all models finish (true/false) and if so, in what period', bool_models_all_built, time_models_completed)
#    print('Avg FTE capacity and after full modeling', avg_capacity, avg_capacity_at_full_modeling)

print ('DONE WITH THE SCENARIO RUNS!')
#%%
# Create histogram of Time to Complete All Models
df_iter_end_period = pd.DataFrame(ds_iter_end_period)

plt.close()
timeframe_hist = df_iter_end_period.plot.hist(density=True, alpha=0.6, color='b')
plt.title('Histogram of Timeframes to Complete All Models')
fig = plt.gcf()
filename = 'Graphs/TimeHist' + scenario_name + '.png'
fig.savefig(filename)
plt.close()

#%%
# Create histogram of FTE capacity
df_iter_capacity = pd.DataFrame(ds_iter_capacity)

plt.close()
capacity_hist = df_iter_capacity.plot.hist(density=True, alpha=0.6, color='b')
plt.title('Histogram of available FTE once all models built')
fig = plt.gcf()
filename = 'Graphs/FTEHist' + scenario_name + '.png'
fig.savefig(filename)
plt.close()

#%%
# Create histogram of failed monitor percentage
df_iter_failed_monitor_pct = pd.DataFrame(ds_iter_failed_monitor_pct)

plt.close()
failure_hist = df_iter_failed_monitor_pct.plot.hist(density=True, alpha=0.6, color='b')
plt.title('Histogram of Pct of Model Monitoring that failed')
fig = plt.gcf()
filename = 'Graphs/FailHist' + scenario_name + '.png'
fig.savefig(filename)
plt.close()


