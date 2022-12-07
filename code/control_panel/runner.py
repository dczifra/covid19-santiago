import os
import json
import yaml
import argparse
import itertools
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from subprocess import Popen, STDOUT, PIPE
from multiprocessing import Pool
from logger import TBLogger

from losses import get_county_loss, get_global_loss

def read_yaml(filename="input.yaml"):
    with open(filename) as file:
        args = yaml.load(file, Loader=yaml.FullLoader)
    return args

def run(c_args, R0, R1, shift):
    c_args["--R0"]=R0
    c_args["--R1"]=R1
    c_args["--second_wave"] = shift
    c_args["--out"]=c_args["--out"]+f"R0={R0}_R1={R1}_shift={shift}"

    str_args = [str(item) for pair in c_args.items() for item in pair]
    p = Popen([ "../bin/main"] + str_args,
          stdout=PIPE, stdin=PIPE, stderr=STDOUT, bufsize=1, universal_newlines=True)
    p.communicate()

def get_inf_curve(df, K, death_rate):
    # Works for only 2 I compartment
    # TODO: make it tiny
    inf_cols = [c for c in df.columns if c[0:2]=='I_']
    inf_cols2 = [c for c in df.columns if c[0:2]=='I2']
    Is = df.filter(inf_cols, axis=1)
    Is2 = df.filter(inf_cols2, axis=1)
    
    I = np.zeros((len(Is), K, len(Is.columns)//K))
    for c in Is.columns:
        _,city,age = c.split("_")
        I[:,int(age), int(city)] = Is.loc[:, c]
    I2 = np.zeros((len(Is2), K, len(Is2.columns)//K))
    for c in Is2.columns:
        _,city,age = c.split("_")
        I2[:,int(age), int(city)] = Is2.loc[:, c]
    
    I = np.sum(I, axis=2)
    I2 = np.sum(I2, axis=2)
    # Aggregate over cities
    return np.sum(I*death_rate, axis=1)+np.sum(I2*death_rate, axis=1), Is.sum(axis=1), Is2.sum(axis=1)

def aggregate_county(df, K, pop_file):
    # Get city indexes of county
    with open(pop_file) as file:
        rows = []
        for row in json.load(file)["populations"]:
            rows.append((row["index"], row["city"],row["admin_municip"], row["admin_county"]))
        city_df = pd.DataFrame(rows, columns=["index", "city", "municip", "county"])
        network_size = len(city_df)
        county_IDs = city_df.groupby('county').index.apply(list).to_dict()

    charts = []
    for county, cities in county_IDs.items():
        infs = [f"I_{city}_{age}" for city in cities for age in range(K)] + \
               [f"I2_{city}_{age}" for city in cities for age in range(K)]
        chart = df[infs].agg(sum, axis=1)
        charts.append((county, chart))
    
    df = pd.DataFrame({county:chart for county,chart in charts})
    #df.to_csv(f"log/{args['sim_id']}/county.csv")
    return network_size, charts

def aggregate_age(df, K, network_size):
    charts = []
    for age in range(K):
        infs = [f"I_{city}_{age}" for city in range(network_size)] + \
               [f"I2_{city}_{age}" for city in range(network_size)]
        chart = df[infs].agg(sum, axis=1)
        charts.append(chart)
            
    df = pd.DataFrame({str(age):charts[age] for age in range(K)})
    #df.to_csv(f"log/{args['sim_id']}/ages.csv")


def aggregate_all(df, K, network_size):
    # TODO multiply with death ratio
    infs = [f"I_{city}_{age}" for city in range(network_size) for age in range(K)] + \
            [f"I2_{city}_{age}" for city in range(network_size) for age in range(K)]
    chart = df[infs].agg(sum, axis=1)

def get_optimal_shift(county_data, c_charts):
    sim_aggregated = np.sum([chart for label,chart in c_charts], axis=0)
    losses = []
    for i in range(80):
        # Compute shift
        shifted_GT = county_data.iloc[154-i:154+args['simulated_days']-i]

        # Normalize
        equal_ratio = np.sum(shifted_GT["Összesen"])/np.sum(sim_aggregated)

        # Get loss components
        county_loss = get_county_loss(shifted_GT, c_charts, equal_ratio)
        global_loss = get_global_loss(shifted_GT["Összesen"].to_numpy(), sim_aggregated, equal_ratio)

        # Compute final loss
        r = args["loss"]["global_rate"]
        loss = (1-r)*county_loss + r*global_loss
        losses.append((loss, equal_ratio, i))

    ind_min = np.argmin(losses)
    return losses[ind_min]

def get_str(arr):
    return "_".join([str(a) for a in arr])

if __name__ == "__main__":
    ########################
    #         ARGS         #
    ########################
    # === Script Options ===
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--yaml', dest='yaml', default="input.yaml", help='Input yaml file')
    parser.add_argument('--sim', dest='sim', action='store_true',default=False, help='Do simulation, or use already simulated')
    parser.add_argument('--args', dest='show_args', action='store_true',default=False, help='Shows args from .yaml')
    options = parser.parse_args()

    # === Read args ===
    args = read_yaml()
    if(options.show_args):
        print("[main] Args:")
        for key,val in args.items():
            print(f"         {key} : {str(val)}")

    # === Check some consistency in the doc ===
    assert(args['age_groups'] == len(args['death_rate']))
    assert(os.path.exists(args['network_config_folder']))

    ########################
    #      SIMULATION      #
    ########################
    if(not  os.path.exists(f"log/{args['sim_id']}")):
        os.mkdir(f"log/{args['sim_id']}")
    # === Run simulation ===
    if(options.sim):
        c_args = {
            "--out": f"log/{args['sim_id']}/",
            "--config": args['network_config_folder'],
            "--maxT": args['simulated_days'],
            "--c": args['seasonality'],
        }

        R0 = args['first_wave']['R0']
        R0_std = args['first_wave']['std']
        R0_num = args['first_wave']['num']
        R0_distribution = np.linspace(R0-R0_std, R0+R0_std, R0_num)

        R1 = args['second_wave']['R1']
        R1_std = args['second_wave']['std']
        R1_num = args['second_wave']['num']
        R1_distribution = np.linspace(R1-R1_std, R1+R1_std, R1_num)
        
        shift = args['second_wave']['time']
        shift_std = 0
        shift_num = 1
        shift_distribution = np.linspace(shift-shift_std, shift+shift_std, shift_num, dtype=int)

        print(R0_distribution, R1_distribution, shift_distribution)
        pool = Pool(processes=args["threads"])
        for R0,R1,shift in itertools.product(R0_distribution, R1_distribution, shift_distribution):
            pool.apply_async(run, args=[c_args, R0, R1, shift])
        pool.close()
        pool.join()
        print('[main] Simulation ended')
    else:
        print('[main] Simulations skiped')
    
    ########################
    #       LOG/SIM        #
    ########################
    pop_file = f"{args['network_config_folder']}/populations_KSH.json" # TODO ==> read only once
    county_data = pd.read_csv("log/ground_truth_county.csv")
    
    losses_R0 = []
    agg_charts = []
    param_distribution = []
    for file in os.listdir(f"log/{args['sim_id']}"):
        # === Read simulation data ===
        #df = pd.read_csv(f"log/2/R0=2.7617185266303697")
        df = pd.read_csv(f"log/{args['sim_id']}/{file}")
        R0, R1, R1_shift = file.split('_')
        R0 = float(R0.split('=')[1])
        R1 = float(R1.split('=')[1])
        R1_shift = float(R1_shift.split('=')[1])
        #print(R0, R1, R1_shift)

        # LOG: Deaths
        #deaths, I, I2 = get_inf_curve(df, args['age_groups'], args['death_rate'])
        
        # LOG: Age groups
        #aggregate_age(df, args['age_groups'], network_size)

        # LOG: County infections
        network_size, c_charts = aggregate_county(df, args['age_groups'], pop_file)

        ########################
        #       LOG/LOSS       #
        ########################
        #city_data = pd.read_csv("../hun_codes/data/HU_settlement_tempinfo.csv")

        sim_aggregated = np.sum([chart for label,chart in c_charts], axis=0)

        loss,equal_ratio, shift = get_optimal_shift(county_data, c_charts)
        print(loss, equal_ratio, shift)
        losses_R0.append((loss, R0, R1, R1_shift, shift))

        agg_charts.append(((R0, R1, R1_shift), equal_ratio*sim_aggregated))
        param_distribution.append({"R0":R0, "R1":R1, "R1_shift":R1_shift, "loss":loss, "equal_ratio":equal_ratio, "shift":shift})

    loss, R0, R1, R1_shift, shift= min(losses_R0)
    print(f"Minimal loss: {loss} [R0 = {R0}]")

    # Log for all sims
    g_truth = county_data["Összesen"].to_numpy()[154-shift:154-shift+args['simulated_days']]
    d_truth = { }
    df = pd.DataFrame(dict([("Ground truth",g_truth)]+ [(get_str(params),data) for params,data in sorted(agg_charts)]))
    df.to_csv(f"log/helper/{args['sim_id']}_agg.csv")


    #print(county_data[154:][["Budapest", "Dátum"]])
    # TODO:
    #    * Change plot to plotly
    #    * read real data
    #    * simple loss function