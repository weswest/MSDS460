# Overview of Project

This was my Northwestern MSDS460 Decision Analytics final project.  Expectation was to take a business problem that we were somewhat familiar with, and figure out how to model it using Python (strong encouragement to use SimPy to manage the simulation).

When I built this I ran the Balance Sheet Management team at Huntington Bank, and one of the most important problems we were working through was improving the scope and quality of behavioral models we used to make our balance sheet forecasts.  I ran the Modeling and Analytics team, and had worked with some external consultants to identify how big that team should be.  Consultants said that my 4-person modeling group should be more like 10, given the run-rate scope of work the team was expected to build and maintain.

I wanted to challenge that assumption, so I built a simulation of my modeling team's workflow using SimPy.  For a given set of inputs (largely, current and target FTE levels; number of models to be completed), I ran a thousand 10-year simulations, capturing typical time to build all of the models, frequency of failing to deliver on model monitoring tasks, and the run-rate average excess staff capacity once all models were built.

### Overview of Simulation
![Summ1](https://github.com/weswest/MSDS460/blob/master/Wk10%20Final%20Project/Graphs/MSDS460%20Final%20Project%20Diagram1.jpg)
![Summ2](https://github.com/weswest/MSDS460/blob/master/Wk10%20Final%20Project/Graphs/MSDS460%20Final%20Project%20Diagram2.jpg)

### Conclusion: 10 FTE is a Good Balance

| Max FTE | \# Models | Time Complete (wks) | Avg Capacity (FTE) | % Monitor Fails |
| ------- | --------- | ------------- | ------------------ | --------------- |
| 6       | 15        | 150           | 0.8                | 12%             |
| 8       | 15        | 120           | 1.2                | 10%             |
| **10**      | **15**        | **100**           | **2.1**                | **3%**              |
| 15      | 15        | 80            | 6.3                | 0%              |
| 10      | 25        | 150           | 1.1                | 13%             |
| 15      | 25        | 115           | 2.7                | 5%              |

Given a workload of ~15 models, 10 FTE provides a good time to completion (~2 years), a low failure-to-deliver rate, and a strong post-completion size of the team available to accomplish other, non-modeled work.

# Structure of the Simulation

One piece of the simulation tracks the number of modelers available to work on models.  Another piece tracks where models are in their build / monitor / rebuild lifecycle.	

### Structure - Staffing Module
The staffing module takes as inputs the current staff level at the start of the simulation, and the target size the modeler team will grow to.  Inherent in these assumptions is the expectation that the team is at most fully staffed, and that we do not need to fire a modeler at time 0.  

Modelers are managed as a SimPy "resource", which allows for useful simulation features like forcing a model to request a modeler and then wait in a queue for said modeler to become available.  A "fire staff" event was used to handle the concept of understaffing - both at the start of the simulation and as the result of a modeler quitting during the simulation.  When this event triggers, a modeler resource is consumed for the duration until "time to rehire".

The pace of hiring and firing are both modeled as random processes with normal distributions.  The inputs are generally based on my team's lived experience with staff turnover and with the time investment necessary to onboard a new employee.  For simplicity, the time to hire is quicker than time to fire, which ensures staff levels trend to full capacity relatively quickly.

### Structure - Model Management Module
The model management module creates n "Model" objects, each of which manages that model's evolution through its life cycle.  When a modeler is available, a Model begins its "build" phase.  Once that phase ends, the model needs to be monitored each quarter for the next six quarters, at which point it needs to be rebuilt.  After the rebuild, it perpetually executes in the monitor / rebuild cycle.

At the end of each touchpoint event, the next touchpoint event is created with "start after" date and a "due by" dates, reflecting the fact that model management must happen within a given window of time.  If the simulation passes the due date without the task being executed, then a failure counter is incremented.

Time to complete model (re)building and monitoring are set as uniform distributions.  As with staffing, this generally reflects the lived experience of the modeling team.  The number of models under management is a key input that dictates total workload.

# Areas for Improvement
It's important to remember that coursework - as with professional work - is a balancing act of delivering work that is good enough in the timeframe available.  My grand plans for this project had to be pared down as I got into the weeds (and as life got in the way, like unexpected 3am toddler wakeups eating into my coursework time).  That said, I got a 100% on my project and writeup, so I feel good about how I invested my time.

So here's the punchlist, given infinite time to make this perfect.

* Structural:
  * All models are structured identically, with the same range of completion time, monitoring expectations, and cadence to rebuild.  I would like to edit the structure to allow for multiple levels of model risk and complexity, which would deviate these management inputs
  * Modelers are entirely undifferentiated.  In practice, a modeler will "own" a model, and so long as that modeler is available they will be put against a model in their stable.  Further, modelers are differently skilled: a new hire would probably be slower than a seasoned employee, and a senior modeler would be faster than a junior modeler
  * In practice, we have identified "families" of models, and modelers specialize in a "family" of models.  I'd love to set this up so that our groups of modelers are appropriately tagged to model families, which would then require additional functionality to move existing staff from one family to another, based on capacity constraints
  * The way I initialized staff levels at time 0 resulted in faster-than-expected hiring in the first year of the simulation
  * I wanted to add in breakage events on a random cadence, including:
    * Early model breakage.  End the "monitoring" phase early and move directly into "rebuild"
    * Non-model effort.  At some cadence, some group of modelers are diverted away from their BAU tasks to address some non-modeled need that has arisen
* Coding:
  * I could've done a better job building the Model object and generalizing its methods.  I was a little lazy creating separate "build" and "monitor" methods, when I could've refactored this into a single "work on" method with different inputs
  * I built global counters to track key features, and rather than appropriately controlling the flow of these variables into the various methods, I lazily created "global" indicators within the methods.  It worked fine, but introduced unnecessary risks
  * My output graphs look like garbage.  Seriously, so embarassing.

# Example Outputs from the Benchmark Scenario
*I reiterate my coding callout above: these graphs are embarassingly bad.  But they serve their purpose*

### Histogram of % Model Monitoring that Fails to be Done On Time
*No clue why the frequency on the left is so weird.  Like I said, I did a bad job with the graphs*
![FailHist](https://github.com/weswest/MSDS460/blob/master/Wk10%20Final%20Project/Graphs/FailHistT10M15_61246.png)

### Histogram of Weeks to Completion to Build All Models
![FinishHist](https://github.com/weswest/MSDS460/blob/master/Wk10%20Final%20Project/Graphs/TimeHistT10M15_61246.png)

### Histogram of Average Excess Headcount Once All Models Built
*Note: Advantage here is how many additional heads are available to do non-model-management analytics*
![HeadcountHist](https://github.com/weswest/MSDS460/blob/master/Wk10%20Final%20Project/Graphs/FTEHistT10M15_61246.png)
