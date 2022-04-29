"""
Modify bus141 from pandapower
test on pandapower version: 2.9.0
"""

import pandapower as pp
from pandapower import networks, plotting
import networkx as nx
import pandapower.topology as top
import numpy as np

print(f'pandapower version: {pp.__version__}')

# load default case
net = pp.converter.from_mpc('case141.mat', f_hz=50, casename_mpc_file='case141', validate_conversion=False)
net.ext_grid['max_p_mw'] = 100 # add some limits in case we want to run opf, dont need it for pf
net.ext_grid['min_p_mw'] = -100
net.ext_grid['max_q_mvar'] = 100
net.ext_grid['min_q_mvar'] = -100

# control zones
zone_index = {1: list(range(1,7)) + list(range(32,35)),
            2: list(range(36,44)) + list(range(72,74)),
            3: list(range(77,81)) + [75],
            4: list(range(44,52)) + list(range(82,86)),
            5: list(range(53,58))+list(range(69,72)) + [59,60] + list(range(62,67)),
            6: list(range(87,99))+list(range(100,105)) + list(range(106,109)),
            7: list(range(7,15))+list(range(111,115)),
            8: list(range(117,129)) + [130,131,133],
            9: list(range(15,32)) + [134,135,139]
            }

PV_bus_index = {1: [35,110],
                2: [52,74],
                3: [81],
                4: [76,86],
                5: [58,61,67,68],
                6: [99,105,109],
                7: [115,116],
                8: [129,132],
                9: [136,137,138,140]
                }

# entire zone index
for i in range(len(zone_index)):
    net.bus.loc[zone_index[i+1], 'zone'] = f'zone{i+1}'
    net.bus.loc[PV_bus_index[i+1], 'zone'] = f'zone{i+1}'

main_index = net.bus[net.bus['zone'] == 1].index.values
net.bus.loc[main_index, 'zone'] = 'main'

# change bus voltage constrains
net.bus.loc[1:,'max_vm_pu'] = 1.05
net.bus.loc[1:,'min_vm_pu'] = 0.95

bus = net.bus
line = net.line
# check connectivity: the buses in a zone should at least connected to a bus in the same zone
mg = top.create_nxgraph(net)
incidence_matrix = nx.incidence_matrix(mg).toarray().T # incidence matrix

for i in range(incidence_matrix.shape[0]):
    # read branch and bus
    bus_pair = np.nonzero(incidence_matrix[i])[0]
    flag = 0
    bus1_zone = net.bus['zone'].iloc[bus_pair[0]]
    bus2_zoen = net.bus['zone'].iloc[bus_pair[1]]
    
    if (bus1_zone == 'main' and bus1_zone != 'main') or (bus1_zone != 'main' and bus1_zone == 'main') or (bus1_zone == bus1_zone):
        pass
    else:
        print('wrong connection!!')
        
# set the sgen at the PV_bus_index
# we define new PVs in bus141 system
for i in range(1,len(PV_bus_index)+1):
    # the p_mw and q_mvar is tempotal
    for j in range(len(PV_bus_index[i])):
        pp.create_sgen(net, bus = PV_bus_index[i][j], p_mw = 0.5, q_mvar = 0.05, name = f'zone{i}',
                    type = 'PV', scaling = 1, controllable = False, in_service = True)
        
sgen = net.sgen
load = net.load
ext_grid = net.ext_grid

# save net
pp.to_pickle(net, "bus141.p")  # relative path
plotting.to_html(net,filename='bus141.html', show_tables=(False))
# %%
