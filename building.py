from testing import MetamorphicTestingHandler
from visualization import Visualizer

import matplotlib
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

# matplotlib.use('module://backend_interagg')
matplotlib.use('TkAgg')

IN_PATH = "io/building/ubuntu_sim/inputs/"
OUT_PATH = "io/building/ubuntu_sim/outputs/"

THRESHOLD_TEMP = 0.94
THRESHOLD_LIGHT = 0.3

INPUTS = {"in_ir1": "A1_IR_1.txt",
          "in_ir2": "A3_IR_2.txt",
          "in_temp": "A4_TEMP_SENSOR.txt",
          "in_light": "A5_LIGHT_SENSOR.txt",
          "in_fire_sw": "D12_FIRE_SWITCH.txt"}

OUTPUTS = {"out_e1l1": "D2_E1L1.txt",
           "out_e1l2": "D3_E1L2.txt",
           "out_e2l1": "D4_E2L1.txt",
           "out_e2l2": "D5_E2L2.txt",
           "out_r1l1": "D6_R1L1.txt",
           "out_r1l2": "D7_R1L2.txt",
           "out_r2l1": "D8_R2L1.txt",
           "out_r2l2": "D11_R2L2.txt",
           "out_alarm": "D13_ALARM.txt"}


class BuildingVisualizer(Visualizer):
    BOXES = {"in_ir1": ((14, 72), (64, 122)),
             "in_ir2": ((14, 144), (64, 195)),
             "in_light": ((14, 211), (64, 261)),
             "in_temp": ((14, 305), (64, 355)),
             "in_fire_sw": ((14, 393), (64, 442)),
             "out_r1l1": ((441, 41), (494, 90)),
             "out_r1l2": ((441, 92), (494, 142)),
             "out_r2l1": ((441, 160), (494, 210)),
             "out_r2l2": ((441, 212), (494, 261)),
             "out_e1l1": ((441, 268), (494, 318)),
             "out_e1l2": ((441, 320), (494, 369)),
             "out_e2l1": ((441, 382), (494, 432)),
             "out_e2l2": ((441, 434), (494, 483)),
             "out_alarm": ((254, 250), (254, 287))
             }
    IMAGE_PATH = "img/building_top.png"

    def __init__(self):
        self.img = np.array(Image.open(BuildingVisualizer.IMAGE_PATH), dtype=np.uint8)
        self.fig, self.ax = plt.subplots(1)
        self.ax.imshow(self.img)
        plt.ion()
        plt.show()

    def update(self, wr):
        for port in wr.inputs:
            if port in BuildingVisualizer.BOXES:
                tl, br = BuildingVisualizer.BOXES[port]
                if port == "in_temp":
                    color = 'b' if wr.inputs[port].curr_state <= THRESHOLD_TEMP else 'r'
                elif port == "in_light":
                    color = 'b' if wr.inputs[port].curr_state <= THRESHOLD_LIGHT else 'r'
                else:
                    color = 'r' if wr.inputs[port].curr_state == 1 else 'b'
                rect = patches.Rectangle(tl, br[0] - tl[0], br[1] - tl[1], linewidth=2, edgecolor=color,
                                         facecolor='none')
                self.ax.add_patch(rect)

        for port in wr.outputs:
            if port in BuildingVisualizer.BOXES:
                tl, br = BuildingVisualizer.BOXES[port]
                color = 'r' if wr.outputs[port].curr_state == 1 else 'b'
                width = 2 if port != "out_alarm" else 1
                rect = patches.Rectangle(tl, br[0] - tl[0], br[1] - tl[1], linewidth=width, edgecolor=color,
                                         facecolor='none')
                self.ax.add_patch(rect)

    def show(self):
        plt.draw()
        plt.pause(0.5)


# --------------------------------------------------------------------------
# METHAMORPHIC RELATIONS
# -----------------------

# Alarm must be activated when some of the red emergency LEDs is turned on
def alarm_when_some_red_led(inputs, outputs):
    if outputs["out_e1l1"].curr_state == 1 or outputs["out_e2l1"].curr_state == 1:
        assert outputs["out_alarm"].curr_state == 1


# If a red emergency LED is activated in a EC one LED has to be activated in the other EC (wither red or green)
def emergency_controllers_red_dependency(inputs, outputs):
    if outputs["out_e1l1"].curr_state == 1:
        assert (outputs["out_e2l1"].curr_state == 1 and outputs["out_e2l2"].curr_state == 0) or \
                (outputs["out_e2l1"].curr_state == 0 and outputs["out_e2l2"].curr_state == 1)

    if outputs["out_e2l1"].curr_state == 1:
        assert (outputs["out_e1l1"].curr_state == 1 and outputs["out_e1l2"].curr_state == 0) or \
               (outputs["out_e1l1"].curr_state == 0 and outputs["out_e1l2"].curr_state == 1)


# Green emergency LEDs are only turned on when the contrary red LEDs are activated
def emergency_controllers_red_green_dependency(inputs, outputs):
    if outputs["out_e1l2"].curr_state == 1:
        assert outputs["out_e2l1"].curr_state == 1

    if outputs["out_e2l2"].curr_state == 1:
        assert outputs["out_e1l1"].curr_state == 1


# The outputs of an Emergency LED Controller can not be activated simultaneously
def exclusive_emergency_controller_outputs(inputs, outputs):
    assert outputs["out_e1l1"].curr_state == 0 or outputs["out_e1l2"].curr_state == 0
    assert outputs["out_e2l1"].curr_state == 0 or outputs["out_e2l2"].curr_state == 0


# When alarm is not fired the lights has some dependencies with the IR sensors:
#    - The output of the first light in a room has to be the same than the IR input related with the same room.
#    - The second light of a room can not be turned on if the first light is not turned on.
def lights_ir_dependencies_without_alarm(inputs, outputs):
    if outputs["out_alarm"].curr_state == 0:
        assert outputs["out_r1l1"].curr_state == inputs["in_ir1"].curr_state
        assert outputs["out_r2l1"].curr_state == inputs["in_ir2"].curr_state

        if outputs["out_r1l2"].curr_state == 1:
            assert outputs["out_r1l1"].curr_state == 1

        if outputs["out_r2l2"].curr_state == 1:
            assert outputs["out_r2l1"].curr_state == 1


# All the lights have to be turned on when an alarm is raised
def lights_on_when_alarm_activated(inputs, outputs):
    if outputs["out_alarm"].curr_state == 1:
        assert outputs["out_r1l1"].curr_state == 1
        assert outputs["out_r1l2"].curr_state == 1
        assert outputs["out_r2l1"].curr_state == 1
        assert outputs["out_r2l2"].curr_state == 1


mm_relations = {
    "alarm_when_some_red_led": alarm_when_some_red_led,
    "emergency_controllers_red_dependency": emergency_controllers_red_dependency,
    "emergency_controllers_red_green_dependency": emergency_controllers_red_green_dependency,
    "exclusive_emergency_controller_outputs": exclusive_emergency_controller_outputs,
    "lights_ir_dependencies_without_alarm": lights_ir_dependencies_without_alarm,
    "lights_on_when_alarm_activated": lights_on_when_alarm_activated,
}

mmth = MetamorphicTestingHandler(INPUTS, OUTPUTS,
                                 visualizer=None)
                                 # visualizer=BuildingVisualizer())

mmth.run_test_case("sim1", IN_PATH, OUT_PATH, mm_relations)
print(len(mmth.port_values))