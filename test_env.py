from BridgeEnv import BridgeEnv
import time
import random
# random.seed(0)
start = time.time()

env = BridgeEnv(nmc=10, debug=False)
state = env.reset()


#
for i in range(34): # action 34 lead to termination immediately, pass is not allowed
    env.step(i)
    env.step(35)
    print("======================= GREAT SPLIT LINE %i ===============================" % i)
    env.reset(reshuffle=True)
env.step(34)
print(time.time() - start)


# for i in range(5):
#     env.step(i)
#
# # 35 PASS
# env.step(35)
