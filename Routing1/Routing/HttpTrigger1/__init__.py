import logging
import azure.functions as func
import tempfile
from azure.storage.blob import BlobServiceClient
import pandas as pd
import os
from pulp import LpProblem,LpVariable,LpMinimize,lpSum
from .preprocess import distance_dict,material_cost,total_cost,demand_data,sup_data,contracts_data
from .helper_fun import get_model_variables, get_variable_info, mapping, rental_vehicles

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    """name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:"""

    optimization()
    return func.HttpResponse(
            "This HTTP triggered function executed successfully. All the maps and output files are place in the Conotainers.",
            status_code=200
        )

def optimization():
    """to read data from container"""
    #try:
    # load raw data from rawdatastore
    tempFilePath = tempfile.mkdtemp()
    local_path = tempFilePath

    # local_file_name = 'Data_ex.xlsx'
    container_name= "rawdatastore/Cost-Optimization"
    local_file_name = "Data_ex.xlsx"

    #connection string
    connect_str =os.getenv("connect_str")

    # Create the BlobServiceClient object which will be used to create a container client
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)

    blob_client = blob_service_client.get_blob_client(container=container_name, blob=local_file_name)

    download_file_path = os.path.join(local_path,local_file_name)
    print("\nDownloading blob to \n\t" + download_file_path)

    with open(download_file_path, "wb") as download_file:
        download_file.write(blob_client.download_blob().readall())

    #reading all data from blob
    Supply_df=pd.read_excel(download_file_path,"Supply")
    Demand_df=pd.read_excel(download_file_path,"Demand")
    dist_costdf=pd.read_excel(download_file_path,"cost_TA")
    supply_dist_df = pd.merge(Supply_df, dist_costdf, on=["TransportType","OriginArea"], how='inner')
    contracts_df=pd.read_excel(download_file_path,"Contracts")
    transport_fac_df=pd.read_excel(download_file_path,"TransportAcceptance")

    factories=["Paris","London","SaintPetersburg","Barcelona","Berlin"]
    suppliers=tuple(zip(supply_dist_df.Supplier,supply_dist_df.OriginArea,supply_dist_df.Cost,supply_dist_df.Material))
    materials=["Material1","Material2","Material3","Material4"]
    transport=["Auto","Train"]
    Auto_dict=dict(zip(transport_fac_df.Factory,transport_fac_df.Auto))
    Train_dict=dict(zip(transport_fac_df.Factory,transport_fac_df.Train))

    # calling the preprocessed data
    transport_cost, keys,main_comb=distance_dict(suppliers,supply_dist_df,materials,transport,factories)
    material_cost1=material_cost(supply_dist_df)
    costs_dict=total_cost(transport_cost,material_cost1,keys)
    demand_dict=demand_data(Demand_df,factories,materials)
    supp_dict=sup_data(suppliers,supply_dist_df)
    contract_dict= contracts_data(contracts_df)

    #creating the model
    model=LpProblem("shipping",LpMinimize)

    #Variables
    var=LpVariable.dicts("shipment",keys,0,None,"Integer")
    trains_used=lpSum(var[s,m,t,f]*.01428 for s in suppliers for m in materials for t in transport  for f in factories if (s,m,t,f) in keys and t=="Train" and f=="London")

    #Objective function
    rental_charges=1500
    model+=lpSum(var[s,m,t,f]*costs_dict[s,m,t,f] for s in suppliers for m in materials for t in transport for f in factories if (s,m,t,f) in keys)+ rental_charges * rental_vehicles(trains_used)

    #Constraint for Demand
    for f in factories:
        for m in materials:
                model+=lpSum([var[s,m,t,f] for s in suppliers for t in transport if (s,m,t) in main_comb])>=demand_dict[(f,m)] 

    #constraint for Supply
    supp_keys=[i for i in supp_dict.keys()]
    for i in supp_keys:
        s,m,t=(i)
        model+=lpSum([var[(s,m,t,f)] for f in factories if (s,m,t) in main_comb])<=supp_dict[i] 

    #constraint for Factory Capacity
    factory_capacity_df=pd.read_excel(download_file_path,"Factories")
    factory_capacity_dict=dict(zip(factory_capacity_df.Factory,factory_capacity_df.MaxCapacity))
    for f in factories:
        model+=lpSum(var[(s,m,t,f)] for s in suppliers for m in materials for t in transport if (s,m,t) in main_comb)<=factory_capacity_dict[f]

    #Constraint for contracts
    for f in factories:
        for s in suppliers:
            for m in materials:
                for t in transport:
                    if (s,m,t) in main_comb:
                        if contract_dict[(f,s[0])]==0:
                            model+=(var[s,m,t,f])==contract_dict[(f,s[0])]


    #constarint for Trains
    t="Train"
    for f in factories:
        model+=lpSum((0.01428*var[s,m,t,f]) for s in suppliers for m in materials if (s,m,t,f) in keys)<=Train_dict[f]
    
    #constarint for Autos
    t="Auto"
    for f in factories:
        model+=lpSum((0.03330*var[s,m,t,f]) for s in suppliers for m in materials if (s,m,t,f) in keys)<=Auto_dict[f]

    #solving the model using pulp's default solver CBC
    model.solve()

    print(model.objective.value())
    logging.info(model.objective.value())

    #storing the data in csv
    variable_key,variable_val=get_model_variables(model)
    sup,loc,mat,tran,fac,variable_val=get_variable_info(variable_key,variable_val)
    output_df=pd.DataFrame({"Supplier":sup,"OriginArea":loc,"Material":mat,"TransportType":tran,"Factory":fac,"Quantity":variable_val})
    output_df=output_df.append([{'Supplier':" ",'OriginArea':" ","Material":" ","TransportType":" ","Factory":" ","Quantity":" "}], ignore_index=True)
    output_df=output_df.append([{'Supplier':f"Overall Cost optimized={model.objective.value()}",'OriginArea':" ","Material":" ","TransportType":" ","Factory":" ","Quantity":" "}], ignore_index=True)
    container_name = "publishdatastore/Cost-optimization"
    local_file_name = "scm_output.csv"
    upload_file_to_azure(output_df, container_name, local_file_name)
    logging.info("Successfully published")
    
    #creating dataframes for each factory
    logging.info("creating maps")
    origin_df=pd.read_excel(download_file_path,"OriginArea")
    origin_df1=origin_df[["OriginArea","Lat","Lon"]]
    s_df=output_df.merge(origin_df1, on=["OriginArea"],how='left')
    s_df["Region"]=tuple(zip(s_df.Lat,s_df.Lon))
    s1_df=s_df[s_df.Quantity!=0]
    berlin_df=s1_df[(s1_df.Factory=="Berlin")]
    saint_df=s1_df[(s1_df.Factory=="SaintPetersburg")]
    paris_df=s1_df[(s1_df.Factory=="Paris")]
    Barcelona_df=s1_df[(s1_df.Factory=="Barcelona")]
    London_df=s1_df[(s1_df.Factory=="London")]

    f_df=pd.read_excel(download_file_path)
    f_df['region']=tuple(zip(f_df.Lat,f_df.Lon))
    f_dict=dict(zip(f_df.Factory,f_df.region))


    #creating maps for each factory
    berlin_map=mapping("Berlin",berlin_df,f_dict["Berlin"])
    paris_map=mapping("Paris",paris_df,f_dict["Paris"])
    saint_petersburg_map=mapping("SaintPetersburg",saint_df,f_dict["SaintPetersburg"])
    barcelona_map=mapping("Barcelona",Barcelona_df,f_dict["Barcelona"])
    london_map=mapping("London",London_df,f_dict["London"])

    #uploading the maps 
    upload_file_to_azure(berlin_map,container_name,"Berlin_map.html")
    upload_file_to_azure(paris_map,container_name,"Paris_map.html")
    upload_file_to_azure(saint_petersburg_map,container_name,"SaintPetersburg_map.html")
    upload_file_to_azure(barcelona_map,container_name,"Barcelona_map.html")
    upload_file_to_azure(london_map,container_name,"London_map.html")

    return 1
    
    """except Exception:
            print("<<<<<<<< Exception >>>>>>>", Exception)
            logging.info(Exception)
            logging.debug(Exception)
            return 0"""

def upload_file_to_azure(inputtype, container_name, local_file_name):
    #to upload the file to container

    tempFilePath = tempfile.mkdtemp()
    connect_str =os.getenv("connect_str")

    # Create the BlobServiceClient object which will be used to create a container client
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)    

    logging.info('Going to write in temp folder')
    if type(inputtype)==pd.core.frame.DataFrame:
        inputtype.to_csv(tempFilePath + "/" + local_file_name, index=False)
    else:
        inputtype.save(tempFilePath + "/" + local_file_name)

    blob_client = blob_service_client.get_blob_client(container=container_name, blob=local_file_name)

    logging.info("\nUploading to Azure Storage as blob:\n\t" + local_file_name)

    # Upload the created file
    upload_file_path = tempFilePath + "/" + local_file_name

    with open(upload_file_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)

    print("<<<< Files uploaded! >>>>")
    logging.info("<<<< Files uploaded! >>>>")
    logging.debug("<<<< Files uploaded! >>>>")