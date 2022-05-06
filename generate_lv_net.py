"""
Generate the low-voltage networks which can be further used by constructing the large network

1. The transformer can be seen as a special type of transmissin line where one side is the ext_grid and another side is a common point of the low voltage network (ext_grid).
2. Define the initial_bus as the buses that are directly connected to the ext_grid bus. 
3. Specifying the the zones by finding the shortest path from the leaf bus to the initial_bus.
4. Merge zones if they have the same initial bus.
5. The name of sgen is the zone name.
6. If there is a zone that does not have a sgen, assign a sgen at the leaf bus
"""

import numpy as np
import pandapower as pp
import simbench as sb
import random
import networkx as nx
import pandapower.topology as top
from pandapower.plotting.plotly import simple_plotly
import simbench as sb
import scipy

print(f'scipy version: {scipy.__version__}')

random.seed(1)

"""
Functions
"""

def determine_initial_bus(LV_trafo, LV_line):
    """
    TARGET:
        Return the initial bus which is the bus connected to the low-voltage side bus of the transformer
    """
    # Bus index of high voltage side of transformer
    high_bus_index = LV_trafo['hv_bus'].values.item() 

    # Bus index of low voltage side of transformer
    ext_bus_index = LV_trafo['lv_bus'].values.item()

    # Find the index of bus connected to the low voltage side of transformer (both from and to bus)
    from_bus_line_index = list(LV_line[LV_line['from_bus'] == ext_bus_index].index.values)
    to_bus_index = list(LV_line['to_bus'].iloc[from_bus_line_index].values)

    to_bus_line_index = list(LV_line[LV_line['to_bus'] == ext_bus_index].index.values)
    from_bus_index = list(LV_line['from_bus'].iloc[to_bus_line_index].values)

    # the starting point of each branches
    bus_initial = (from_bus_index+to_bus_index)
    
    return bus_initial, high_bus_index, ext_bus_index

def determine_leaf_bus(LV_bus, LV_line):
    # Drop the to_grid bus
    new_bus = LV_bus.copy(deep = True) # copy a new bus
    new_bus.drop(new_bus[new_bus['vn_kv'] == 20].index, inplace = True)

    # use nx to find the incidence matrix
    nodes = new_bus.index.values
    edges = LV_line[['from_bus','to_bus']].values
    G = nx.DiGraph()
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)
    incidence_matrix = nx.incidence_matrix(G).toarray().T # incidence matrix

    # Find the leaf bus: the bus connected to only one bus
    leaf_bus = []
    for i in range(incidence_matrix.shape[-1]):
        connected_bus_no = len(np.nonzero(incidence_matrix[:,i])[0])
        if connected_bus_no == 1:
            leaf_bus.append(i)
    
    return leaf_bus, incidence_matrix

def determine_zone(LV_net, leaf_bus, incidence_matrix):
    """
    TARGET:
        Return the zone allocation of the grid
    """
    # Determine the zones
    # Find the shortest bus from the leaf bus to the lower voltage side of transformer
    # the number of zone = the number of leaf bus
    zone = {}
    mg = top.create_nxgraph(LV_net)
    for index, value in enumerate(leaf_bus):
        zone[f'zone{index}'] = nx.shortest_path(mg, ext_bus_index, value)
        zone[f'zone{index}'] = zone[f'zone{index}'][1:] # remove the external bus

    # check if the initial bus in the zone is included in the bus_initial
    for i in zone.keys():
        assert zone[i][0] in set(bus_initial)

    # Combine zones sharing the same elements. E.g. combine the zone with the same initial point
    new_zone = {}
    for i, value in enumerate(bus_initial):
        # Find all zones start with the same initial bus value
        new_zone[f'zone{i+1}'] = [] # an empty zone
        for j in range(len(zone)):
            if zone[f'zone{j}'][0] == value:
                new_zone[f'zone{i+1}'] = list(set(new_zone[f'zone{i+1}']+zone[f'zone{j}'])) # uniqueness

    # Assign the zone to bus
    LV_bus['zone'].iloc[ext_bus_index] = 'main' # the lower voltage side of the transformer
    LV_bus['zone'].loc[high_bus_index] = 'delete' # the higher voltage side of the transformer
    for i in range(len(new_zone)):
        LV_bus['zone'].iloc[new_zone[f'zone{i+1}']] = f'zone{i+1}'
    
    # Check connectivity: all buses in a zone should be at least conneted to another in the zone
    for i in range(incidence_matrix.shape[0]):
        # read branch and bus
        bus_pair = np.nonzero(incidence_matrix[i])[0]
        bus1_zone = LV_bus['zone'].iloc[bus_pair[0]]  # zone name of the first bus
        bus2_zone = LV_bus['zone'].iloc[bus_pair[1]]  # zone name of the second bus
        
        if (bus1_zone == 'main' and bus2_zone != 'main') or (bus1_zone != 'main' and bus2_zone == 'main') or (bus1_zone == bus1_zone):
            pass
        else:
            print('wrong connection!!')
    
    return LV_bus, new_zone

def determine_sgen(LV_sgen, LV_bus, new_zone):
    """
    TARGET:
        Change the name of sgen as the name of the zone
    """
    # Change the name of LV_sgen by the zone of this bus
    for i in range(LV_sgen.shape[0]):
        LV_sgen['name'].iloc[i] = LV_bus['zone'].iloc[LV_sgen['bus'].iloc[i]]

    # if there is a zone that does not bave sgen, then we just add one
    for i in range(len(new_zone)):
        if f'zone{i+1}' not in LV_sgen['name'].values:
            # If a zone does not in the name of LV_sgen
            print(f'zone{i+1} does not have sgen, so we add one at an arbitary bus')
            new_sgen_bus_index = LV_bus[LV_bus['zone'] == f'zone{i+1}'].index.values
            # Add a sgen by the previous one [-1]
            LV_sgen = LV_sgen.append(LV_sgen.iloc[-1]) 
            # The index of sgen bus at the last bus of this zone
            LV_sgen['bus'].iloc[-1] = new_sgen_bus_index[-1] 
            # Also add the name in sgen by the zone name
            LV_sgen['name'].iloc[-1] = f'zone{i+1}' 
    
    # Arrange
    LV_sgen.reset_index(inplace = True, drop = True)
    
    return LV_sgen

"""
main functions
"""

if __name__ == "__main__":

    # The list of low-voltage net in simbench
    LV_list = ['1-LV-rural1--0-sw','1-LV-rural2--0-sw','1-LV-rural3--0-sw','1-LV-semiurb4--0-sw','1-LV-semiurb5--0-sw','1-LV-urban6--0-sw']

    for LV_index in range(len(LV_list)):

        # LV net summary
        LV_net = sb.get_simbench_net(LV_list[LV_index])
        LV_bus = LV_net.bus
        LV_load = LV_net.load
        LV_line = LV_net.line
        LV_ext_grid = LV_net.ext_grid
        LV_trafo = LV_net.trafo
        LV_sgen = LV_net.sgen
        print(f'number of trafo in LV{LV_index} is {LV_trafo.shape[0]}')
        # simple_plotly(LV_net)

        bus_initial, high_bus_index, ext_bus_index = determine_initial_bus(LV_trafo, LV_line)
        leaf_bus, incidence_matrix = determine_leaf_bus(LV_bus, LV_line)
        LV_bus, new_zone = determine_zone(LV_net, leaf_bus, incidence_matrix)
        LV_sgen = determine_sgen(LV_sgen, LV_bus, new_zone)

        assert LV_bus.shape[0] == LV_bus.tail(2).index[0] + 2
        assert LV_sgen.shape[0] == LV_sgen.tail(1).index[0] +1 

        # Save and plot
        # update bus and sgen
        LV_net.bus = LV_bus.copy(deep = True)
        LV_net.sgen = LV_sgen.copy(deep = True)

        LV_bus = LV_net.bus
        LV_load = LV_net.load
        LV_line = LV_net.line
        LV_ext_grid = LV_net.ext_grid
        LV_trafo = LV_net.trafo
        LV_sgen = LV_net.sgen

        pp.to_pickle(LV_net, filename = f'lv_network/LV{LV_index}.p')
        pp.plotting.to_html(LV_net, filename = f'lv_network/LV{LV_index}.html', show_tables=(False))
