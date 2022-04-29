This repo contains how we generate bus33bw and bus141 testbeds in the following paper: Wang, J., Xu, W., Gu, Y., Song, W., & Green, T. C. (2021). Multi-agent reinforcement learning for active voltage control on power distribution networks. Advances in Neural Information Processing Systems, 34, 3271-3284.

1. The PV buses are added as sgen with `controllable = False`
2. The bus33bw is generated from pandapower case file
3. The bus141 is generated from the matpower case file