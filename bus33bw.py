"""
Modify bus33bw from pandapower
test on pandapower version: 2.9.0
"""

import pandapower as pp
from pandapower import networks, plotting

print(f'pandapower version: {pp.__version__}')

# Load default network
net = networks.case33bw()
net.ext_grid['max_p_mw'] = 100 # add some limits in case we want to run opf, dont need it for pf
net.ext_grid['min_p_mw'] = -100
net.ext_grid['max_q_mvar'] = 100
net.ext_grid['min_q_mvar'] = -100

# Remove the lines of loop
net.line.drop([32,33,34,35,36], inplace = True)

'''
Add static generator bus and sgen
they will merge with the terminal bus during runpp
In Volt/Var, the reactive power should be updated by the control policy.
The active power is fed by the predefined PV power input.
'''
# terminal bus: in this case, we add PV at the terminal bus
PV_bus_index = [12,17,21,24,28,32]


# we define new PVs in bus33bw system
for i in range(len(PV_bus_index)):
    # the p_mw and q_mvar is tempotal
    pp.create_sgen(net, bus=PV_bus_index[i], p_mw = 0.5, q_mvar=0.05, name = 'undefined',
                type='PV', scaling = 1, controllable=False, in_service=True)

# change bus voltage constrains
net.bus.loc[1:,'max_vm_pu'] = 1.05
net.bus.loc[1:,'min_vm_pu'] = 0.95

# area: change control zone
main_bus_index = [0,1,2,3,4,5]
zone1_index = list(range(6, 18))
zone2_index = list(range(18,22))
zone3_index = list(range(22,25))
zone4_index = list(range(25,33))

net.bus.loc[main_bus_index,'zone'] = 'main'
net.bus.loc[zone1_index,'zone'] = 'zone1'
net.bus.loc[zone2_index,'zone'] = 'zone2'
net.bus.loc[zone3_index,'zone'] = 'zone3'
net.bus.loc[zone4_index,'zone'] = 'zone4'

# sort
net.bus.sort_index(inplace = True)
net.line.sort_index(inplace = True)
net.load.sort_index(inplace = True)

# rename the sgen
for i in range(net.sgen.shape[0]):
    sgen_bus_index = net.sgen['bus'].iloc[i]
    net.sgen['name'].iloc[i] = net.bus['zone'].iloc[sgen_bus_index]
    # print(net.sgen['name'])

net.sgen.sort_index(inplace = True)

net.bus['type'] = 'n'

bus = net.bus
line = net.line
load = net.load
sgen = net.sgen
ext_grid = net.ext_grid

# save net
pp.to_pickle(net, "bus33bw.p") 
plotting.to_html(net,filename='bus33bw.html', show_tables=(False))


