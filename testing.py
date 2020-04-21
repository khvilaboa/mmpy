
from abc import ABC, abstractmethod
import re


class StatesMonitor:
    REGEX_LINE = r"([0-9]{2}):([0-9]{2}):([0-9]{2})(?::([0-9]{3}))? ([0-9.e-]+)"

    def __init__(self, path):
        self.in_stream = open(path, "r")
        self.finished = False

        self.curr_time = None
        self.curr_state = None

        self.next_time = None
        self.next_state = None

        self.advance()

    def advance(self):
        if self.finished:
            return

        self.curr_time = self.next_time
        self.curr_state = self.next_state

        while self.curr_time == self.next_time:
            line = self.in_stream.readline()

            if line:
                self.next_time, self.next_state = StatesMonitor.parse_state(line.strip())

                if self.curr_time == self.next_time:
                    self.curr_state = self.next_state
            else:
                self.finished = True
                self.next_time = None
                self.next_state = None

    @staticmethod
    def parse_state(line):
        match = re.match(StatesMonitor.REGEX_LINE, line)

        if not match:
            return None, None

        hours, minutes, seconds, nanoseconds, state = match.groups()

        state_time = 3.6e6 * int(hours) + 6e4 * int(minutes) + 1e3 * int(seconds)
        if nanoseconds is not None:
            state_time += int(nanoseconds)
        return int(state_time), float(state)


class TestingHandler(ABC):

    def __init__(self, visualizer=None):
        self._sim_time = 0
        self.inputs = None
        self.outputs = None
        self.visualizer = visualizer

    @abstractmethod
    def get_next_event_time(self):
        pass

    @abstractmethod
    def execute_time(self, sim_time):
        pass

    @abstractmethod
    def check_relations(self, inputs, outputs):
        pass

    def show_io_values(self):
        inp_values = {k: v.curr_state for k, v in self.inputs.items()}
        print("Inputs:", inp_values)

        out_values = {k: v.curr_state for k, v in self.outputs.items()}
        print("Outputs:", out_values)

    def run(self):
        if self.inputs is None:
            raise RuntimeError("Inputs not specified.")

        sim_time = self.get_next_event_time()
        while sim_time is not None:
            print("\nExecuting simulation time %.3f" % (sim_time / 1000))
            self.execute_time(sim_time)
            self.show_io_values()
            if self.visualizer is not None:
                self.visualizer.update(self)
                self.visualizer.show()
            self.check_relations(self.inputs, self.outputs)
            sim_time = self.get_next_event_time()


class MetamorphicTestingHandler(TestingHandler):

    def __init__(self, inputs, outputs, in_path_prefix="", out_path_prefix="", relations=None, visualizer=None):
        super().__init__(visualizer)
        self.inputs = {k: StatesMonitor(in_path_prefix + v) for k, v in inputs.items()}
        self.outputs = {k: StatesMonitor(out_path_prefix + v) for k, v in outputs.items()}
        self.last_state = None
        self.relations = relations

    def get_next_event_time(self):
        try:
            return min(mon.next_time for mon in self.inputs.values() if mon.next_time is not None)
        except (ValueError, TypeError):
            return None

    def execute_time(self, sim_time):
        for in_file in self.inputs:
            mon = self.inputs[in_file]
            if mon.next_time == sim_time:
                mon.advance()

        for out_file in self.outputs:
            mon = self.outputs[out_file]
            if mon.next_time == sim_time:
                mon.advance()

    def check_relations(self, inputs, outputs):
        if self.relations is None:
            return

        for rel_name, rel_fun in self.relations.items():
            print("Checking %s relation..." % rel_name)
            rel_fun(inputs, outputs)
