
from testing import MetamorphicTestingHandler
import matplotlib

matplotlib.use('module://backend_interagg')

IN_PATH = "io/airlift/inputs/"
OUT_PATH = "io/airlift/outputs/"

INPUTS = {"gen": "in_gen.log"}

OUTPUTS = {"destination": "out_dest.log",
           "expired": "out_exp.log"}

# --------------------------------------------------------------------------
# METHAMORPHIC RELATIONS
# -----------------------

def tst(inputs, outputs):
    pass

mmth = MetamorphicTestingHandler(INPUTS, OUTPUTS,
                                 visualizer=None,
                                 multival=True)
                                 # visualizer=BuildingVisualizer())

mmth.run_test_case("sim1", IN_PATH, OUT_PATH, {"test": tst})
print(len(mmth.port_values))
