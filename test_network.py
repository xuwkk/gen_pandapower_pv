"""
Test the network by running opf
"""

import argparse
import pandapower as pp

parser = argparse.ArgumentParser()
parser.add_argument("--bus", help="specify the bus name under test")
args = parser.parse_args()

if args.bus == 'bus33bw':
    net = pp.from_pickle(f'bus33bw.p')
elif args.bus == 'bus141':
    net = pp.from_pickle(f'bus141.p')
elif args.bus == 'bus322':
    net = pp.from_pickle(f'bus322.p')

print(net)
try:
    pp.runpp(net, max_iteration = 30)
    print('Converged!')
except:
    print('Did not converge')