import numpy as np
import pandas as pd

def get_county_loss(county_ground_truth, sim_data, equal_ratio):
    # Squared Mean Loss for each day
    # Mean for all county
    c_losses = []
    for county,chart in sim_data:
        # TODO
        if(county == "főváros"): county="Budapest"
        
        if(county not in county_ground_truth.columns):
            print(f"County not found! {county}")
        else:
            g_truth = county_ground_truth[county].to_numpy()
            loss = np.mean(np.abs(g_truth-equal_ratio*chart)**1)
            c_losses.append(loss)
    
    return np.mean(c_losses)

def get_global_loss(global_ground_truth, sim_data, equal_ratio):
    # Squared Mean Loss for each day
    loss = np.mean(np.abs(global_ground_truth-equal_ratio*sim_data)**1)

    return loss