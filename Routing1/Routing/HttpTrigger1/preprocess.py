import pandas as pd
import numpy as np
from pulp import *
#import matplotlib.pyplot as plt


def distance_dict(suppliers,supply_dist_df,materials,transport,factories):

    keys=[(s,m,t,f) for s in suppliers for m in materials for t in transport for f in factories]
    main_comb=tuple(zip(tuple(zip(supply_dist_df.Supplier,supply_dist_df.OriginArea,supply_dist_df.Cost,supply_dist_df.Material)),supply_dist_df.Material,supply_dist_df.TransportType))
    main_comb=list(main_comb)
    len(keys),len(main_comb)

    #expanding the distance cost from supplier to each factory
    dist_cost=np.array(supply_dist_df[["Paris","London","SaintPetersburg","Barcelona","Berlin"]].round(2))
    dist_cost.shape

    aa=[]
    for i in range(len(dist_cost)):
        aa.append(np.tile(dist_cost[i],(8,1)))
        
    dist_cost_updated=np.array(aa).flatten()
    dist_cost_updated=dist_cost_updated.tolist()
    dist_cost_dict=dict(zip(keys,dist_cost_updated))

    ## filtering out the actual data pairs
    key1=[]
    transp_cost=[]
    for k,v in dist_cost_dict.items():
        if k[:3] in main_comb:
            key1.append(k)
            transp_cost.append(v)
    return transp_cost,key1,main_comb

def material_cost(supply_dist_df):
    # actual cost = Transportation cost* cost of each material
    material_cost=np.array([i for i in supply_dist_df.Cost])
    material_cost=material_cost.reshape(639,1)
    return material_cost

def total_cost(transp_cost,material_cost,key1):
    total_cost=(np.array(transp_cost).reshape(639,5))+ material_cost
    total_cost=total_cost.flatten().tolist()
    costs_dict=dict(zip(key1,total_cost))
    return costs_dict

def demand_data(Demand_df,factories,materials):
    ## setting up demand dict
    demand_keys=[(f,m) for f in factories for m in materials ]
    demand_values=[i for i in Demand_df.Demand]
    demand_dict=dict(zip(demand_keys,demand_values))
    return demand_dict

def sup_data(suppliers,supply_dist_df):
    ## setting up supply dict
    supp_keys=tuple(zip(suppliers,supply_dist_df.Material,supply_dist_df.TransportType))
    supp_val=[i for i in supply_dist_df.Volume]
    sup_dict=dict(zip(supp_keys,supp_val))
    return sup_dict


def contracts_data(contracts_df):
    #Setting up Contract dict
    contacts_keys=tuple(zip(contracts_df.FactoryId,contracts_df.SupplierId))
    contacts_val=[i for i in contracts_df.Contract]
    contract_dict=dict(zip(contacts_keys,contacts_val))
    return contract_dict



