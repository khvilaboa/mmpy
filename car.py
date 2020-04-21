from testing import MetamorphicTestingHandler
from visualization import Visualizer

import matplotlib
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

# matplotlib.use('module://backend_interagg')
matplotlib.use('TkAgg')

IN_PATH = "io/car/original/inputs/"
OUT_PATH = "io/car/original/outputs/"

INPUTS = {"ir_right": "A0_RightIR_In.txt",
          "ir_center": "A2_CenterIR_In.txt",
          "ir_left": "D4_LeftIR_In.txt"}

OUTPUTS = {"right_motor1": "D8_RightMotor1_Out.txt",
           "right_motor2": "D11_RightMotor2_Out.txt",
           "left_motor1": "D12_LeftMotor1_Out.txt",
           "left_motor2": "D13_LeftMotor2_Out.txt"}


class CarVisualizer(Visualizer):
    BOXES = {"ir_right": ((1, 55), (80, 95)),
             "ir_center": ((1, 125), (80, 165)),
             "ir_left": ((1, 195), (80, 235)),
             "right_motor1": ((440, 23), (520, 63)),
             "right_motor2": ((440, 87), (520, 127)),
             "left_motor1": ((440, 157), (520, 197)),
             "left_motor2": ((440, 227), (520, 267))
             }
    IMAGE_PATH = "img/seed_bot_driver_top.png"

    def __init__(self):
        self.img = np.array(Image.open(CarVisualizer.IMAGE_PATH), dtype=np.uint8)
        self.fig, self.ax = plt.subplots(1)
        self.ax.imshow(self.img)
        plt.ion()
        plt.show()

    def update(self, wr):
        for port in wr.inputs:
            if port in CarVisualizer.BOXES:
                tl, br = CarVisualizer.BOXES[port]

                if wr.inputs[port].curr_state == 0:
                    color = "blue"
                elif 0 < wr.inputs[port].curr_state < 1:
                    color = "purple"
                else:
                    color = "red"

                rect = patches.Rectangle(tl, br[0] - tl[0], br[1] - tl[1], linewidth=2, edgecolor=color,
                                         facecolor='none')
                self.ax.add_patch(rect)

        for port in wr.outputs:
            if port in CarVisualizer.BOXES:
                tl, br = CarVisualizer.BOXES[port]
                if wr.outputs[port].curr_state == 0:
                    color = "blue"
                elif 0 < wr.outputs[port].curr_state < 1:
                    color = "purple"
                else:
                    color = "red"
                rect = patches.Rectangle(tl, br[0] - tl[0], br[1] - tl[1], linewidth=2, edgecolor=color,
                                         facecolor='none')
                self.ax.add_patch(rect)

    def show(self):
        plt.draw()
        plt.pause(8)


# --------------------------------------------------------------------------
# METHAMORPHIC RELATIONS
# -----------------------

# A rear motor cannot be active if the corresponding front motor is not
def rear_inactive_when_front_inactive(inputs, outputs):
    if outputs["right_motor2"].curr_state > 0:
        assert outputs["right_motor1"].curr_state > 0

    if outputs["left_motor2"].curr_state > 0:
        assert outputs["left_motor1"].curr_state > 0


# If R1 or L1 are 0, the car must be stopped (all motors off)
def car_stopped_when_r1_off_or_l1_off(inputs, outputs):
    if outputs["right_motor1"].curr_state == 0 or outputs["left_motor1"].curr_state == 0:
        assert outputs["right_motor1"].curr_state == 0
        assert outputs["right_motor2"].curr_state == 0
        assert outputs["left_motor1"].curr_state == 0
        assert outputs["left_motor2"].curr_state == 0


# If both motors at one side are 1, the car is turning. This means that in the other side the front motor
# is active (but with lower speed) and the rear motor is off.
def only_front_motor_when_both_motors_in_oposite_side(inputs, outputs):
    if outputs["right_motor1"].curr_state > 0 and outputs["right_motor2"].curr_state > 0:
        assert 0 < outputs["left_motor1"].curr_state < outputs["right_motor1"].curr_state
        assert outputs["left_motor2"].curr_state == 0

    if outputs["left_motor1"].curr_state > 0 and outputs["left_motor2"].curr_state > 0:
        assert 0 < outputs["right_motor1"].curr_state < outputs["left_motor1"].curr_state
        assert outputs["right_motor2"].curr_state == 0


# R2 and L2 are only used to turn. Hence, they cannot be activated at the same time.
def not_r2_and_l2_at_the_same_time(inputs, outputs):
    assert not(outputs["right_motor2"].curr_state > 0 and outputs["left_motor2"].curr_state > 0)


mm_relations = {
    "rear_inactive_when_front_inactive": rear_inactive_when_front_inactive,
    "car_stopped_when_r1_off_or_l1_off": car_stopped_when_r1_off_or_l1_off,
    "not_r2_and_l2_at_the_same_time": not_r2_and_l2_at_the_same_time,
    "only_front_motor_when_both_motors_in_oposite_side": only_front_motor_when_both_motors_in_oposite_side
}

mmth = MetamorphicTestingHandler(INPUTS, OUTPUTS,
                                 in_path_prefix=IN_PATH,
                                 out_path_prefix=OUT_PATH,
                                 relations=mm_relations,
                                 visualizer=CarVisualizer())
mmth.run()
