# Readme

This repo contains how we generate bus33bw and bus141 testbeds in the following [paper](https://proceedings.neurips.cc/paper/2021/hash/1a6727711b84fd1efbb87fc565199d13-Abstract.html): Wang, J., Xu, W., Gu, Y., Song, W., & Green, T. C. (2021). Multi-agent reinforcement learning for active voltage control on power distribution networks. Advances in Neural Information Processing Systems, 34, 3271-3284.

1. The PV buses are added as sgen with `controllable = False`
2. The bus33bw is generated from pandapower case file
3. The bus141 is generated from the matpower case file

For the bus322 system, firstly run generate_lv_net.py to generate 6 low-voltage networks which are further built into a large (bus322) network.

To test the network, you can run `python test_network.py --bus 'bus322'`, etc.

## Package
1. scipy == 1.8.0
2. pandas == 1.1.0
3. pandapower == 2.9.0
