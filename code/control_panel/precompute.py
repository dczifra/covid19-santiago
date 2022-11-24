import pandas as pd

# TODO:
#    * rename Összesen -> SUM

def generate_county_curves(filename):
    county_data = pd.read_csv(filename).fillna(method='ffill')
    county_data=county_data.rename(lambda l: l if l!="Budapest" else "főváros")[county_data.columns[1:]].diff(axis=0).dropna()
    county_data[county_data<0]=0
    county_data = county_data.rolling(7).mean().dropna()

    county_data.to_csv("log/ground_truth_county.csv")


if __name__ == "__main__":
    home = "../.."
    generate_county_curves(f"{home}/code/hun_codes/data/halalozas_megyenkent.csv")
