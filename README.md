# Bridge Env

A simple API for bridge using Double Dummy Solver to evaluate the score.

# Build Double Dummy Solver library

```
git clone --recurse-submodules https://elisten@bitbucket.org/elisten/bridge_env.git
```

For Mac users, to build dds as multi-threaded. Reinstall gcc

```brew reinstall gcc --without-multilib```


Then modify the `Makefile` and make.

```
cd Mac_patch
python dynamic_makefile.py
cd ../dds/src
make -f Makefiles/Makefile_Mac_clang_patched
cp libdds.so ../../.
```

For Linux users

```
cd dds/src
make -f Makefiles/Makefile_linux_shared
cp libdds.so ../../.
```

# Test

```python test_env.py```

# API

- `reset`: return the first player's initial state: holding(52d vector) and empty bidding history(35d vecotr). 
- `step`:  receive the bidding action and return the state, reward, terminal signal and the next player's seat.

# Variable

- `bidding_seats`: bidding particiants.
- `predeal_seats`: particiants who can be allocated explicit cards when the environment is reset.
- `nmc`: number of Monte Carlo tries.
- `score`: the maximum tricks to win substract the contract target
Refer to config.py for more details.

# Future

The code about *implicit communication through actions* will come soon.
