# Assignment

Purpose of this week's assignment is to practice building monte carlo simulations.  In brief, we needed to build a system that represented a rancher's struggles watering his crops.  He has a water tank of a certain size, and every month some volume of rain falls on his crops and he needs to use some volume of water to water the crops.  If more rain falls than necessary, store it in the water tank; if there's insufficient rainfall, supplement with the tank.

Key question: if you run this simulation out for 30 years, will the rancher run out of water?

Everything else is just permutations off of that.  See the paper if you want to look at my chicken-scratch representation of the model and pretty graphs that show distributions of rainfall, etc.

# Approach

This is my first project using the SimPy package, which is a for-purpose set of code to easily represent the different actors and items you could find in a simulation (e.g., there is a built-in Container which is convenient when you're trying to model a, y'know, container of water).  I plan on using SimPy for the final project in the class, so I'm trying to get my reps in.

# What I'm proud of and what could be improved

I'm proud of the following:
* A key aspect of the assignment was to take historic rainfall data and determine an appropriate distribution for use in simulation.  I found the Fitter package that allowed me to batch-examine a bunch of different distributions and easily identify which one fit the best
* I'm really digging the graphs that I was able to make based on the simulation results.  I would score the *quality* of my graphs as a "D", just because I didn't spend enough time on labeling etc, but I think they convey interesting information

Items on my punchlist for refinement:
* I was lazy in my approach to scenario termination.  The assignment defines running out of water as a terminal failure, and I never assertively coded an end to the simulation when that happened.  Instead, the simulation worked fine using only the terminal time period (360 months), and some creative initialization of the output data series.  My solution was good enough for a homework assignment, but leaves me unsatisfied
* I treated water management as a two-step process, with rainfall happening prior to watering crops.  It probably would have been more appropriate to model these items as a single step, with a net positive rainfall contributing to the reservoir and a net negative rainfall detracting.  C'est la vie, my two-stage approach has a minor bias downward, driven by specific treatment in months when the water tank is filled to capacity
* Definitely some lazy points in here.  An aspect of the problem is that we catch rain with a certain efficiency from 90-98%, which I simply treated as a uniform distribution if discrete integers.  I really should've made a continuous pull, but this is minor.
