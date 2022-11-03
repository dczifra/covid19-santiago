import numpy as np
import pandas as pd


def megye():
    df = pd.read_csv("log/county.csv")
    
    df2 = pd.DataFrame({"megye":[], "inf":[], "days":[], 'id':[]})

    d_id = {m:i for i,m in enumerate(df.iloc(0)[:])}
    print(d_id)
    for i,row in df.iterrows():
        if(i%50 == 0):
            for m,val in row[1:].items():
                df2 = df2.append({"megye":m if m!="főváros" else "Budapest", "inf":int(val),
                "days":i, "id":d_id[m]}, ignore_index=True)
        
    df2["inf"]= df2["inf"].astype(int)
    df2["days"]=df2["days"].astype(int)
    df2.to_csv("log/county_.csv")

megye()