import folium
from folium.plugins import MarkerCluster
import re

def get_model_variables(model):
    variable_key=[]
    variable_val=[]
    for variable in model.variables():
        variable_key.append(variable.name)
        variable_val.append(variable.varValue)
        #print ("{} = {}".format(variable.name, variable.varValue))
    return variable_key,variable_val

def get_variable_info(variable_key,variable_val):
    sup,loc,mat,tran,fac=[],[],[],[],[]

    for v in variable_key:
        rv=re.sub(r"[^a-zA-Z0-9]"," ",str(v))
        rrv=rv.split()
        
        if rrv[2] in ["A","Novi","The"]:
            sup.append(rrv[1])
            loc.append(rrv[2]+" "+rrv[3])
            mat.append(rrv[6])
            tran.append(rrv[-2])
            fac.append(rrv[-1])
        elif rrv[2] in ["Stoke","Kingston"]:
            sup.append(rrv[1])
            loc.append(rrv[2]+" "+rrv[3]+" "+rrv[4])
            mat.append(rrv[-3])
            tran.append(rrv[-2])
            fac.append(rrv[-1])
        else:
            sup.append(rrv[1])
            loc.append(rrv[2])
            mat.append(rrv[5])
            tran.append(rrv[-2])
            fac.append(rrv[-1])

    return sup,loc,mat,tran,fac,variable_val

def mapping(factory,factory_df,fact_location):
    map2 = folium.Map(location=[65,26], zoom_start=4)
    marker_cluster = MarkerCluster().add_to(map2)

    icon=folium.Icon(color='red', icon='building', icon_color="white", prefix='fa')
    folium.Marker(location=(fact_location),
                  popup = factory,
                  icon=icon,
                  tooltip=factory).add_to(map2)
    
    locationlist=factory_df[["Lat","Lon"]].values.tolist()

    for point in range(0, len(locationlist)):
        folium.Marker(locationlist[point], popup='ID:'+factory_df['Supplier'].iloc[point]+" "+factory_df['OriginArea'].iloc[point]+'-'+factory_df['TransportType'].iloc[point]+'\n'+factory_df['Material'].iloc[point]+':'+" "+str(factory_df['Quantity'].iloc[point]), icon=folium.Icon(color="blue", icon_color='black', icon="home", angle=0, prefix='fa')).add_to(marker_cluster)
        f1=folium.FeatureGroup()
        folium.vector_layers.PolyLine([locationlist[point],fact_location],popup="Path to "+str(factory) ,tooltip="path",color='red',weight=1.5).add_to(f1)
        f1.add_to(map2)
    return map2


def rental_vehicles(var1):
    if var1>=122:
        rent_trains=var1-122
        return rent_trains
    else:
        return 0