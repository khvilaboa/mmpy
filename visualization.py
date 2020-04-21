
from abc import ABC, abstractmethod
import matplotlib
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
from PIL import Image

matplotlib.use('TkAgg')


class Visualizer(ABC):

    @abstractmethod
    def update(self, wr):
        pass

    @abstractmethod
    def show(self):
        pass




