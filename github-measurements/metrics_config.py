import pandas as pd
import Metrics
import RepoCentricMeasurements
import UserCentricMeasurements
import math
import json
import argparse
from functools import partial, update_wrapper
from time import time

def named_partial(func, *args, **kwargs):
    partial_func = partial(func, *args, **kwargs)
    update_wrapper(partial_func, func)
    return partial_func

def pretty_time(t):
    """takes a time, in seconds, and formats it for display"""
    m, s = divmod(t, 60)
    h, m = divmod(m, 60)
    s = round(s) #Rounds seconds to the nearest whole number
    h = str(h).rjust(2,"0") #convert to strings,
    m = str(m).rjust(2,"0") #adding 0 if necessary to make 
    s = str(s).rjust(2,"0") #each one two digits long
    return "{}h{}m{}s".format(h,m,s)

contribution_events = ["PullRequestEvent", "PushEvent", "IssuesEvent","IssueCommentEvent","PullRequestReviewComment","CommitCommentEvent","CreateEvent"]
popularity_events = ["WatchEvent", "ForkEvent"]

measurement_params = {
    ### User Centric Measurements

    "user_unique_repos": {
        "question": "17",
        "query": "Do users contribute across many repos?",
        "quantify": "Number of unique repos that a particular set of users contributed too",
        "phenomena": "Persistent minorities",
        "scale": "population",
        "node_type":"user",
        "filters": {"event": contribution_events},
        "measurement": UserCentricMeasurements.getUserUniqueRepos,
        "metrics": { 
            "js_divergence": named_partial(Metrics.js_divergence, discrete=False),
            "rmse": Metrics.rmse,
            "r2": Metrics.r2}
    },

    "user_activity_timeline": {
        "question": "19",
        "query": "Do rockstars provide sustained contributions to repos? Can we measure their volume of activity?",
        "quantify": "Daily contribution counts of the user over time. Number of unique repos contributed to by day",
        "phenomena": "Persistent minorities, Evolution",
        "scale": "node",
        "node_type":"user",
        "filters": {"event": contribution_events},
        "measurement": UserCentricMeasurements.getUserActivityTimeline,
        "metrics": {"rmse": Metrics.rmse,
                    "ks_test": Metrics.ks_test,
                    "dtw": Metrics.dtw}

    },

    "user_activity_distribution": {
        "question": "24a",
        "query": "What are the basic characteristics of developers' population?",
        "quantify": "Distribution over user activity for all users.",
        "phenomena": "Cascade",
        "scale": "population",
        "node_type":"user",
        "measurement": UserCentricMeasurements.getUserActivityDistribution,
        "metrics": {"rmse": Metrics.rmse,
                    "r2": Metrics.r2,
                    "js_divergence": named_partial(Metrics.js_divergence, discrete=True)}
    },

    "most_active_users": {
        "question": "24b",
        "query": "What are the basic characteristics of developers' population?",
        "quantify": "Top K most active users (total number of actions per user)",
        "phenomena": "Evolution",
        "scale": "population",
        "node_type":"user",
        "measurement": named_partial(UserCentricMeasurements.getMostActiveUsers, k=5000),
        "metrics": {"rbo": named_partial(Metrics.rbo_score, p=0.95)}
    },

    "user_popularity": {
        "question": "25",
        "query": "Which users are the most popular?",
        "quantify": "Top K most popular users: #forkEvents + #watchEvents across repos that the users own",
        "phenomena": "Cascade, Evolution",
        "scale": "population",
        "node_type":"user",
        "filters": {"event": popularity_events + ["CreateEvent"]},
        "measurement": named_partial(UserCentricMeasurements.getUserPopularity, k=5000),
        "metrics": {"rbo": named_partial(Metrics.rbo_score, p=0.95)}
    },

    "user_gini_coef": {
        "question": "26a",
        "query": "How much disparity is there among users in the activeness of repo contributions?",
        "quantify": "Gini coefficient for pullRequestEvents, pushEvents and issueEvents",
        "phenomena": "Cascade, Evolution",
        "scale": "population",
        "node_type":"user",
        "filters": {"event": contribution_events},
        "measurement": UserCentricMeasurements.getGiniCoef,
        "metrics": {"absolute difference": Metrics.absolute_difference}
    },

    "user_palma_coef": {
        "question": "26b",
        "query": "How much disparity is there among users in the activeness of repo contributions?",
        "quantify": "Palma ratio for pullRequestEvents, pushEvents and issueEvents",
        "phenomena": "Cascade, Evolution",
        "scale": "population",
        "node_type":"user",
        "filters": {"event":contribution_events},
        "measurement": UserCentricMeasurements.getPalmaCoef,
        "metrics": {"absolute difference": Metrics.absolute_difference}
    },

    "user_diffusion_delay": {
        "question": "27",
        "query": "How soon do users engage with GitHub over time after joining?",
        "quantify": "Diffusion delay of user actions (excluding Fork and Watch events) since the creation of the user account",
        "phenomena": "Cascade, Evolution",
        "scale": "population",
        "node_type":"user",
        "filters": {"event": contribution_events},
        "measurement": UserCentricMeasurements.getUserDiffusionDelay,
        "metrics": {"ks_test": Metrics.ks_test}
    },

}

repo_measurement_params = {
    "repo_diffusion_delay": {
        "question": "1",
        "query": "How long does it take a new repo to become popular?",
        "quantify": "Distribution over diffusion delays in days/hours for forkEvent and watchEvent (the time between when a repo created and when the subsequent events happen to the repo)",
        "phenomena": "Cascade",
        "scale": "node",
        "node_type":"repo",
        "filters":{"event": popularity_events},
        "measurement": named_partial(RepoCentricMeasurements.getRepoDiffusionDelay,
                                     eventType=popularity_events,
                                     ),
        "metrics": {"ks_test": Metrics.ks_test,
                    "js_divergence": named_partial(Metrics.js_divergence, discrete=False)},
    },
    "repo_growth": {
        "question": "2",
        "query": "How do activity levels on a repo grow and decline over time?",
        "quantify": "Repo growth: the number of daily contributions to a repo as a function of time",
        "phenomena": "Cascade, Evolution",
        "scale": "node",
        "node_type":"repo",
        "filters": {"event": contribution_events},
        "measurement": RepoCentricMeasurements.getRepoGrowth,
        "metrics": {"rmse": named_partial(Metrics.rmse, join="outer"),
                    "dtw": Metrics.dtw}
    },
    "repo_contributors": {
        "question": "4",
        "query": "How many users contribute to a specific repo?",
        "quantify": "Number of daily unique contributors to a repo as a function of time. Percent of unique contributors who have already contributed at time t measured in hours",
        "phenomena": "Cascade, Evolution",
        "scale": "node",
        "node_type":"repo",
        "filters": {"event": contribution_events},
        "measurement": RepoCentricMeasurements.getContributions,
        "metrics": {"rmse": named_partial(Metrics.rmse, join="outer"),
                    "dtw": Metrics.dtw}
    },
    "repo_event_distribution_daily": {
        "question": "5",
        "query": "What are typical patterns of activity observed for developers on Github?",
        "quantify": "Distribution of total events daily",
        "phenomena": "Recurrence",
        "scale": "node",
        "node_type":"repo",
        "measurement": RepoCentricMeasurements.getDistributionOfEvents,
        "metrics": {"js_divergence": named_partial(Metrics.js_divergence, discrete=True)}
    },
    "repo_event_distribution_dayofweek": {
        "question": "5",
        "query": "Recurrence",
        "quantify": "Distribution of total events by day of week",
        "phenomena": "Recurrence",
        "scale": "node",
        "node_type":"repo",
        "measurement": named_partial(RepoCentricMeasurements.getDistributionOfEvents, weekday=True),
        "metrics": {"js_divergence": named_partial(Metrics.js_divergence, discrete=True)}
    },
    "repo_popularity_distribution": {
        "question": "12a",
        "query": "What are the most popular repos in the full population?",
        "quantify": "Distribution of watchEvents across repos.",
        "phenomena": "Cascade, Evolution",
        "scale": "population",
        "node_type":"repo",
        "filters": {"event": ["WatchEvent"]}, 
        "measurement": named_partial(RepoCentricMeasurements.getDistributionOfEventsByRepo, eventType="WatchEvent"),
        "metrics": {"js_divergence": named_partial(Metrics.js_divergence, discrete=False),
                    "rmse": Metrics.rmse,
                    "r2": Metrics.r2}
    },
    "repo_popularity_topk": {
        "question": "12b",
        "query": "What are the most popular repos in the full population?",
        "quantify": "Top K of most watched repos.",
        "phenomena": "Cascade, Evolution",
        "scale": "population",
        "node_type":"repo",
        "filters": {"event": ["WatchEvent"]}, 
        "measurement": named_partial(RepoCentricMeasurements.getTopKRepos, k=5000, eventType="WatchEvent"),
        "metrics": {"rbo": named_partial(Metrics.rbo_score, p=0.95)}
    },
    "repo_liveliness_distribution": {
        "question": "13a",
        "query": "What repos have the highest liveliness?",
        "quantify": "Distribution of forkEvents across repos",
        "phenomena": "Cascade, Evolution",
        "scale": "population",
        "node_type":"repo",
        "filters": {"event": ["ForkEvent"]}, 
        "measurement": named_partial(RepoCentricMeasurements.getDistributionOfEventsByRepo, eventType="ForkEvent"),
        "metrics": {"js_divergence": named_partial(Metrics.js_divergence, discrete=False),
                    "rmse": Metrics.rmse,
                    "r2": Metrics.r2}
    },
    "repo_liveliness_topk": {
        "question": "13b",
        "query": "Are they different from the most popular repos?",
        "quantify": "Top K most forked repos",
        "phenomena": "Cascade, Evolution",
        "scale": "population",
        "node_type":"repo",
        "filters": {"event": ["ForkEvent"]}, 
        "measurement": named_partial(RepoCentricMeasurements.getTopKRepos, k=5000, eventType="ForkEvent"),
        "metrics": {"rbo": named_partial(Metrics.rbo_score, p=0.95)}
    },
    "repo_activity_disparity_gini_fork": {
        "question": "14",
        "query": "How much disparity is there in activity levels across repos?",
        "quantify": "Gini coefficient for forkEvent",
        "phenomena": "Cascade, Persistent minorities",
        "scale": "population",
        "node_type":"repo",
        "filters": {"event": ["ForkEvent"]},
        "measurement": RepoCentricMeasurements.getGiniCoef,
        "metrics": {"absolute_difference": Metrics.absolute_difference}
    },
    "repo_activity_disparity_palma_fork": {
        "question": "14",
        "query": "How much disparity is there in activity levels across repos?",
        "quantify": "Palma ratio for forkEvent",
        "phenomena": "Cascade, Persistent minorities",
        "scale": "population",
        "node_type":"repo",
        "filters": {"event": ["ForkEvent"]},
        "measurement": RepoCentricMeasurements.getPalmaCoef,
        "metrics": {"absolute_difference": Metrics.absolute_difference}
    },
    "repo_activity_disparity_gini_push": {
        "question": "14",
        "query": "How much disparity is there in activity levels across repos?",
        "quantify": "Gini coefficient for pushEvent",
        "phenomena": "Cascade, Persistent minorities",
        "scale": "population",
        "node_type":"repo",
        "filters": {"event": ["PushEvent"]},
        "measurement": RepoCentricMeasurements.getGiniCoef,
        "metrics": {"absolute_difference": Metrics.absolute_difference}
    },
    "repo_activity_disparity_palma_push": {
        "question": "14",
        "query": "How much disparity is there in activity levels across repos?",
        "quantify": "Palma ratio for pushEvent",
        "phenomena": "Cascade, Persistent minorities",
        "scale": "population",
        "node_type":"repo",
        "filters": {"event": ["PushEvent"]},
        "measurement": RepoCentricMeasurements.getPalmaCoef,
        "metrics": {"absolute_difference": Metrics.absolute_difference}
    },
    "repo_activity_disparity_gini_pullrequest": {
        "question": "14",
        "query": "How much disparity is there in activity levels across repos?",
        "quantify": "Gini coefficient for pullRequestEvent",
        "phenomena": "Cascade, Persistent minorities",
        "scale": "population",
        "node_type":"repo",
        "filters": {"event": ["PullRequestEvent"]},
        "measurement": RepoCentricMeasurements.getGiniCoef,
        "metrics": {"absolute_difference": Metrics.absolute_difference}
    },
    "repo_activity_disparity_palma_pullrequest": {
        "question": "14",
        "query": "How much disparity is there in activity levels across repos?",
        "quantify": "Palma ratio for pullRequestEvent",
        "phenomena": "Cascade, Persistent minorities",
        "scale": "population",
        "node_type":"repo",
        "filters": {"event": ["PullRequestEvent"]},
        "measurement": RepoCentricMeasurements.getPalmaCoef,
        "metrics": {"absolute_difference": Metrics.absolute_difference}
    },
    "repo_activity_disparity_gini_issue": {
        "question": "14",
        "query": "How much disparity is there in activity levels across repos?",
        "quantify": "Gini coefficient for issueEvent",
        "phenomena": "Cascade, Persistent minorities",
        "scale": "population",
        "node_type":"repo",
        "filters": {"event": ["IssuesEvent"]},
        "measurement": RepoCentricMeasurements.getGiniCoef,
        "metrics": {"absolute_difference": Metrics.absolute_difference}
    },
    "repo_activity_disparity_palma_issue": {
        "question": "14",
        "query": "How much disparity is there in activity levels across repos?",
        "quantify": "Palma ratio for issueEvent",
        "phenomena": "Cascade, Persistent minorities",
        "scale": "population",
        "node_type":"repo",
        "filters": {"event": ["IssuesEvent"]},
        "measurement": RepoCentricMeasurements.getPalmaCoef,
        "metrics": {"absolute_difference": Metrics.absolute_difference}
    }
}

measurement_params.update(repo_measurement_params)


def prefilter(data, filters):

    """
    Filter the data frame based on a set of fields and values.  
    Used to subset on specific event types and on specific users and repos for node-level measurements

    Inputs:
    data - DataFrame in 4-column format
    filters - A dictionary with keys indicating the field to filter, and values indicating the values of the field to keep

    Outputs:
    data - The filtered data frame

    """
#     print ("Applying filter " + str(filters) + " to data " + str(data))
    data.columns = ["time", "event", "user", "repo"]
    for field, values in filters.items():
        data = data[data[field].isin(values)]
#     print ("Filtered data: " + str(data))
    return data

def run_metrics(ground_truth, simulation, measurement_name,users=None,repos=None):

    """
    Run all of the assigned metrics for a given measurement.

    Inputs:
    ground_truth - DataFrame of ground truth data
    simulation - DataFrame of simulated data
    measurement_name - Name of measurement corresponding to keys of measurement_params
    users - list of user IDs for user-centric, node-level measurements
    repos - list of repo IDs for repo-centric, node-level measurements

    Outputs:
    measurement_on_gt - Output of the measurement for the ground truth data
    measurement_on_sim - Output of the measurement for the simulation data
    metrics_output - Dictionary containing metric results for each metric assigned to the measurement   
    """
    metrics_output = {}
    measurement_on_gt = measurement_on_sim = None
 
    start_time = time()
    p = measurement_params[measurement_name]
    print ("<-- " + str(p["question"]))
    if p["node_type"] == "user":
        nodes = users
    else:
        nodes = repos

    if "filters" in p:
        ground_truth = prefilter(ground_truth, p["filters"])
        simulation = prefilter(simulation, p["filters"])
        if ground_truth.empty or simulation.empty:
            print ("ERROR> pre-filtered " + ("ground truth" if ground_truth.empty else "prediction") + " is empty using filter: "+str(p["filters"]))
            return None, None, None

    #for node-level measurements default to the most active node if a 
    #list of nodes is not provided
    if p["scale"] == "node" and nodes is None:
        nodes = ground_truth.groupby([p["node_type"],"event"])["time"].count().reset_index()
        nodes = nodes.groupby(p["node_type"])["time"].median().sort_values(ascending=False).reset_index()
        nodes = nodes.head(100)[p["node_type"]]
    elif p["scale"] != "node":
        nodes = [""]


    #for node level measurements iterate over nodes
    for node in nodes:
        
        if p["scale"] == "node":

            metrics_output[node] = {}

            #select data for individual node
            filter = {p["node_type"]:[node]}
            gt = prefilter(ground_truth, filter)
            if gt.empty:
                print ("Groundtruth not matching filter "+str(filter))
            sim = prefilter(simulation, filter)
            if sim.empty:
                print ("Groundtruth not matching filter "+str(sim))
        else:
            gt = ground_truth.copy()
            sim = simulation.copy()
            
        measurement_function = p["measurement"]

        empty_df = False
        if len(gt.index) > 0:
            print("Measuring {} for ground truth data".format(measurement_function.__name__))
            measurement_on_gt = measurement_function(gt)
        else:
            print("Ground truth data frame is empty for {} measurement".format(measurement_function.__name__))
            empty_df = True
            measurement_on_gt = []

        if len(sim.index) > 0:
            print("Measuring {} for simulation data".format(measurement_function.__name__))
            measurement_on_sim = measurement_function(sim)
        else:
            print("Simulation data frame is empty for {} measurement".format(measurement_function.__name__))
            empty_df = True
            measurement_on_sim = []


        metrics = p["metrics"]

        #iterate over the metrics assigned to the measurement
        for m, metric_function in metrics.items():
            print("Calculating {} for {}".format(metric_function.__name__, measurement_function.__name__))
            if not empty_df:
                metric = metric_function(measurement_on_gt, measurement_on_sim)   
            else:
                metric = None

            mtrdic = None
            if p["scale"] == "node":
                mtrdic = metrics_output[node]
            else:
                mtrdic = metrics_output
                
            mtrdic[m] = metric 
            
            end_time = time()
            mtrdic["eta"] = pretty_time(end_time-start_time)
            
    return measurement_on_gt, measurement_on_sim, metrics_output
    
def run_all_metrics(ground_truth, simulation, scale=None, node_type = None, users = None, repos = None):

    """
    Calculate metrics for multiple measurements.

    Inputs:
    ground_truth - Ground truth data frame
    simulation - Simulation data frame
    scale = Select measurements of a particular scale, possible values are currently "node" or "population".  If None, measurements of all scales are included.
    node_type = Select measurements of particular node-type, possible values are "repo" or "user".  If None, measurements of both node types are included.
    users = List of users to use for node-level user measurements.  If None, the most active user from the ground truth data is selected for all user node-level measurements
    repos = List of repos to user for node-level repo measurements. If None, the most active repo from the ground truth data is selected for all repo node-level measurements
    """
    def without_keys(d, keys):
        """
        Return a copy of the provided dictionary excluding keys.
        """
        return {x: d[x] for x in d if x not in keys}
    
    results = {}
    start_time = time()
    #select measurements of desired scale and node type
    measurements = [m for m, m_info in measurement_params.items() if (scale is None or m_info["scale"] == scale) and (node_type is None or m_info["node_type"] == node_type)] 

    for measurement_name in measurements:
        gt, sim, metric_results = run_metrics(ground_truth.copy(), simulation.copy(), measurement_name, users=users, repos=repos)
        results[measurement_name] = metric_results
        results[measurement_name]["metadata"] = without_keys(measurement_params[measurement_name], ["measurement"])
    end_time = time()
    results["eta"] = pretty_time(end_time-start_time)

    return results

def json_convert(obj):
    if obj == None:
        return "None"
    if obj == math.nan:
        return "NaN"
    if callable(obj):
        return obj.__name__
    if isinstance(obj, float):
        return str(obj)
    if isinstance(obj, (list, tuple)):
        return [json_convert(item) for item in obj]
    if isinstance(obj, dict):
        return {json_convert(key):json_convert(value) for key, value in obj.items()}
    return obj

class EvaluationEngine:
    """
    Engine loading groundtruth and predicted events, processing all metrics evaluations.
    """
    def __init__(self, gt_file, sim_file):
        """
        Load event files
        Data should be in 4-column format: time, event, user, repo
        @param sim_file:  predicted event file in .csv format 
        @param gt_file: ground_truth event file in .csv format 
        """
        if not gt_file or not sim_file:
            self.simulation = self.ground_truth = {}
            return
        
        print ("Parsing simulated and groundtruth events from .csv...")
        print ("GT: " + gt_file)
        print ("SIM: " + sim_file)
        start_time = time()
        self.simulation = pd.read_csv(sim_file,
                             names=["time","event","user","repo"])
    
        self.ground_truth = pd.read_csv(gt_file,
                               names=["time","event","user","repo"])
        print ("Elapsed time: " + pretty_time(time() - start_time))

    def evaluate (self, json_output_file):
        """
        Run all metrics evaluation methods against the loaded ground_truth and simulation
        """
        if self.ground_truth.empty or self.simulation.empty:
            return
        print ("Starting evaluation...")
        
        # Single metrics
        # gt_measurement, sim_measurement, metrics = run_metrics(self.ground_truth, self.simulation, "repo_contributors")
        
        # Run all metrics
        metrics = run_all_metrics(self.ground_truth, self.simulation)
        
        # Print and save results to output json file
        res = json.dumps(json_convert(metrics), indent=2, sort_keys=True)
        if res:
            print(res)
            if json_output_file:
                with open(json_output_file, 'w') as f:
                    print('Saving results to file '+json_output_file)
                    f.write(res)
        
        
def main():
    parser = argparse.ArgumentParser(description='Run SocialSim Metrics evaluation functions')
    parser.add_argument('-s', '--simulated_events', dest='sim', 
                        help='path to the .csv file containing predicted events')
    parser.add_argument('-g', '--groundtruth_events', dest='gt',
                        help='path to the .csv file containing the events to use as ground_truth')
    parser.add_argument('-o', '--output_json_file', dest='json_output_file', default='eval_output.json',
                        help='path to the .json output file to store evaluation results')
    
    
    args = parser.parse_args()
    
    if args.sim and args.gt:
        engine = EvaluationEngine(args.gt, args.sim)
        engine.evaluate(args.json_output_file)
    else:
        print (parser.print_help())

if __name__ == "__main__":
    main()
