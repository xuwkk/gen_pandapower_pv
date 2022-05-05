"""
Generate bus 322 system using the low-voltage networks

The network contains a main branch which is built by myself. However the loads are referred to the loads in one of the mid-voltage network
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pandapower as pp
import simbench as sb
import random

print(f'pandas version: {pd.__version__}')
print(f'pandapower version: {pp.__version__}')

# Random seed
random.seed(1)
np.random.seed(2)

# Empty net: create an empty network
net = pp.create_empty_network() 

# External bus: external bus at bus index 0
pp.create_bus(net, vn_kv=110, type='n',name = 'ext_grid', zone = 'main', max_vm_pu = 1.05, min_vm_pu = 0.95) 

# Main bus: the total number of MV bus
no_bus_MV = 25

# Generate the MV bus
for i in range(no_bus_MV):
    pp.create_bus(net, vn_kv=20, type='n',name = 'MV bus', zone = 'main', max_vm_pu = 1.05, min_vm_pu = 0.95)

# External grid: 110kv
pp.create_ext_grid(net, 0, vm_pu=1.00, va_degree = 0, in_service = True, name = 'ext_grid')

# Transformer: ext_grid(110kv) to MV(20kv) with high power capacity
pp.create_transformer(net,0,1, name="110kV/20kV transformer", std_type="63 MVA 110/20 kV")

# Lines: mv, randomly generate two types of line specification with random lengths
for i in range(1,no_bus_MV):
    if i%2 == 0:
        pp.create_line(net, i, i+1, length_km = 0.3+random.random(), std_type="NA2XS2Y 1x70 RM/25 12/20 kV", name = 'MV_line')
    else:
        pp.create_line(net, i, i+1, length_km = 2+2*random.random(), std_type='70-AL1/11-ST1A 20.0', name = 'MV_line')

# Using the loads in MV_net for the grid
MV_list = ['1-MV-rural--0-sw','1-MV-semiurb--0-sw','1-MV-urban--0-sw','1-MV-comm--0-sw']
MV_net = sb.get_simbench_net(MV_list[0])
pp.runpp(MV_net)
pp.plotting.to_html(MV_net, filename='MV.html', show_tables=(False))
MV_load = MV_net.load
load_index = MV_net.load[MV_net.load['bus'] == no_bus_MV].index[0]
net.load = MV_net.load.iloc[:load_index+1]
net.load['name'] = 'MV_load'
net.load['subnet'] = np.nan

# ccp: MV to LV coupling point bus index
ccp = [5,13,22] # might raise an error

# Remove the load at bus ccp
remove_load_index = []
for i in range(len(ccp)):
    remove_load_index.append(net.load[net.load['bus'] == ccp[i]].index[0])

net.load = net.load.drop(remove_load_index)
net.load.reset_index(drop = True, inplace = True) # reset index after dropping

# Randomly drop some loads
random_remove_load = random.sample(range(net.load.shape[0]), round(net.load.shape[0]/1.3))
random_remove_load.sort()
net.load = net.load.drop(random_remove_load)
net.load.reset_index(drop = True, inplace = True)
net.load

new_bus = net.bus
new_ext_grid = net.ext_grid
new_trafo = net.trafo
new_line = net.line
new_load = net.load
new_sgen = net.sgen

print(f"the total load of MV is {new_load['p_mw'].sum()}")

# Append the LV buses
print('The low-voltage nets:')
for i in range(6):
    LV_net = pp.from_pickle(f'lv_network/LV{i}.p')
    print(f'LV{i} bus No: {LV_net.bus.shape[0]}')

LV_index = [2,4,5]

# Append the low-voltage network on the main branch
for i in range(len(LV_index)):
    print(i)
    # update cumulation: we should add on the index
    cum_bus_index = net.bus.shape[0]     # cumulative bus index after MV and LVs
    cum_line_index = net.line.shape[0]   # cumulative line index after MV and LVs
    cum_sgen_index = net.sgen.shape[0]   # cumulative sgen index after MV and LVs
    cum_load_index = net.load.shape[0]
    cum_zone_index = len(set(new_bus['zone'].values)) - 1
    
    # LV summary
    LV_net = pp.from_pickle(f'lv_network/LV{LV_index[i]}.p')
    print(f'LV{i} bus No: {LV_net.bus.shape[0]}')
    
    LV_bus = LV_net.bus
    LV_load = LV_net.load
    
    LV_line = LV_net.line
    LV_ext_grid = LV_net.ext_grid
    LV_trafo = LV_net.trafo
    LV_sgen = LV_net.sgen
    
    append_bus = LV_bus.copy(deep = True)
    # reset the bus index
    append_bus.set_index(pd.Index(list(range(cum_bus_index,cum_bus_index + append_bus.shape[0]))), inplace = True) # reset the bus index
    
    append_bus['name'] = 'LV bus'
    append_bus['type'] = 'n'
    # append_bus['zone'] = f'zone{i+1}' # change properties
    append_bus['subnet'] = np.nan
    append_bus['min_vm_pu'] = 0.95
    append_bus['max_vm_pu'] = 1.05
    
    # drop the higher voltage bus
    append_bus.drop(append_bus[append_bus['vn_kv'] == 20].index, inplace = True)
    
    # change zone
    for j in range(append_bus.shape[0]):
        if append_bus['zone'].iloc[j] != 'main':
            append_bus['zone'].iloc[j] = f"zone{int(append_bus['zone'].iloc[j][-1]) + cum_zone_index}"
    
    # concate the LV bus to the net.bus
    net.bus = net.bus.append(append_bus[['name','vn_kv', 'type', 'zone', 'in_service', 'min_vm_pu', 'max_vm_pu']]) # concat the bus
    new_bus = net.bus
    
    pp.create_transformer(net,ccp[i], LV_trafo['lv_bus'].values[0] + cum_bus_index, name="20kV/0.4kV transformer", std_type="0.63 MVA 20/0.4 kV")
    new_trafo = net.trafo
    
    append_line = LV_line.copy(deep = True)
    append_line['from_bus'] = append_line['from_bus']+cum_bus_index # change connection
    append_line['to_bus'] = append_line['to_bus']+cum_bus_index
    append_line['name'] = 'LV_line'
    
    rand_ratio = 1.2+0.3*np.random.rand(append_line.shape[0],)
    append_line['length_km'] = append_line['length_km']*rand_ratio
    
    for j in range(append_line.shape[0]):
        # slightly varying the length
        
        if append_line['length_km'].iloc[j]*append_line['r_ohm_per_km'].iloc[j] < 0.001 or append_line['length_km'].iloc[j]*append_line['x_ohm_per_km'].iloc[j] < 0.001:
            km_r = append_line['length_km'].iloc[j] = 0.002/append_line['r_ohm_per_km'].iloc[j]
            km_x = append_line['length_km'].iloc[j] = 0.002/append_line['x_ohm_per_km'].iloc[j]
            append_line.at[j,'length_km'] = np.max([km_r,km_x]) # assign the length to the smaller one
    
    append_line.set_index(pd.Index(list(range(cum_line_index, cum_line_index + append_line.shape[0]))), inplace = True)
    
    net.line = net.line.append(append_line)
    new_line = net.line
    

    append_load = LV_load.copy(deep=True)
    append_load.set_index(pd.Index(list(range(cum_load_index, cum_load_index + append_load.shape[0]))), inplace = True)
    append_load['bus'] = append_load['bus']+cum_bus_index
    append_load['name'] = 'LV_load'
    net.load = net.load.append(append_load[net.load.columns])
    net.load['sn_mva'] = np.nan
    
    new_load = net.load

    append_sgen = LV_sgen.copy(deep=True)
    append_sgen.set_index(pd.Index(list(range(cum_sgen_index, cum_sgen_index + append_sgen.shape[0]))), inplace = True) # reset the sgen index
    append_sgen['bus'] = append_sgen['bus'] + cum_bus_index
    
    # change zone
    for j in range(append_sgen.shape[0]):
        append_sgen['name'].iloc[j] = f"zone{int(append_sgen['name'].iloc[j][-1]) + cum_zone_index}"
    
    net.sgen = net.sgen.append(append_sgen)
    net.sgen['sn_mva'] = np.nan
    
    new_sgen = net.sgen
    
    try:
        pp.runpp(net, max_iteration = 30)
    except:
        print(f'power flow does not converge when adding the {LV_index[i]}th LV, try diag:')
        # dia_result = pp.diagnostic(net, report_style = 'compact')
    print(f'the bus number is {net.bus.shape[0]}')
    print(f'the load number is {net.load.shape[0]}')
    print(f"the total load is {net.load['p_mw'].values.sum()}")
    

# Check connection
pp.to_pickle(net, filename = f'bus322.p')
pp.plotting.to_html(net, filename='bus322.html', show_tables=(False))

new_bus = net.bus
new_load = net.load
new_line = net.line
new_ext_grid = net.ext_grid
new_trafo = net.trafo
new_sgen = net.sgen

assert new_bus.tail(1).index[0] + 1 == new_bus.shape[0]
assert new_line.tail(1).index[0] + 1 == new_line.shape[0]
assert new_load.tail(1).index[0] + 1 == new_load.shape[0]
assert new_sgen.tail(1).index[0] + 1 == new_sgen.shape[0]
assert new_trafo.tail(1).index[0] + 1 == new_trafo.shape[0]

