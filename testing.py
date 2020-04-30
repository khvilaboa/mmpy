import os
from abc import ABC, abstractmethod
import re
from collections import OrderedDict

from visualization import Visualizer


class StatesMonitor:
    REGEX_LINE = r"([0-9]{2}):([0-9]{2}):([0-9]{2})(?::([0-9]{3}))? (.+)"

    def __init__(self, path, multival=False):
        self.in_stream = open(path, "r")
        self.finished = False

        self.curr_time = None
        self.curr_state = None

        self.next_time = None
        self.next_state = None

        self.multival = multival

        self.advance()

    def advance(self):
        if self.finished:
            return

        self.curr_time = self.next_time
        self.curr_state = self.next_state

        while not self.finished and self.curr_time == self.next_time:
            line = self.in_stream.readline()

            if line:
                self.next_time, self.next_state = self.parse_state(line.strip())

                if self.curr_time == self.next_time:
                    self.curr_state = self.next_state
            else:
                self.finished = True
                self.next_time = None
                self.next_state = None

    def parse_state(self, line):
        match = re.match(StatesMonitor.REGEX_LINE, line)

        if not match:
            return None, None

        hours, minutes, seconds, nanoseconds, state = match.groups()

        state_time = 3.6e6 * int(hours) + 6e4 * int(minutes) + 1e3 * int(seconds)
        if nanoseconds is not None:
            state_time += int(nanoseconds)

        if self.multival:
            state = re.split("\s+", state)
            for i in range(len(state)):
                if state[i].isnumeric():
                    state[i] = float(state[i])
        else:
            if state.isnumeric():
                state = float(state)

        return int(state_time), state


class TestingHandler(ABC):

    def __init__(self, visualizer=None):
        self._sim_time = 0
        self.visualizer = visualizer
        self.port_values = {}

    @staticmethod
    def get_next_event_time(inputs):
        try:
            return min(mon.next_time for mon in inputs.values() if mon.next_time is not None)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def check_func_relations(inputs, outputs, relations):
        if relations is None:
            return

        for rel_name, rel_fun in relations.items():
            print("Checking %s relation..." % rel_name)
            rel_fun(inputs, outputs)

    @staticmethod
    def execute_time(sim_time: float, ports: dict):
        for port in ports:
            mon = ports[port]
            if mon.next_time == sim_time:
                mon.advance()

    @staticmethod
    def parse_file_relations(inputs, outputs, relations_fn):
        relations = []
        with open(relations_fn, "r") as rel_file:
            for line in rel_file.readlines():
                line = line.strip()
                if line != "" and not line.startswith("#"):
                    print(line)
                    relation = []
                    line_comps = line.split("->")
                    for comp in line_comps:
                        in_dep = []
                        out_dep = []
                        for port_type, name in re.findall("(in|out):([a-zA-Z0-9_-]+)", comp):
                            if port_type == "in":
                                if name not in in_dep:
                                    in_dep.append(name)
                            else:
                                if name not in out_dep:
                                    out_dep.append(name)
                        relation.append(((in_dep, out_dep), comp.strip()))

                    if len(relation) == 1:
                        relation.insert(0, None)

                    relations.append(relation)

        return relations

    @staticmethod
    def check_file_relations(inputs, outputs, relations):
        def rule_accomplished(rule):
            (in_deps, out_deps), to_eval = rule
            for in_dep in in_deps:
                to_eval = to_eval.replace("in:%s" % in_dep, str(inputs[in_dep].curr_state))

            for out_dep in out_deps:
                to_eval = to_eval.replace("out:%s" % out_dep, str(outputs[out_dep].curr_state))

            return eval(to_eval)

        for pre, post in relations:
            if pre is None or rule_accomplished(pre):
                if not rule_accomplished(post):
                    raise RuntimeError("Rule not accomplished: %s (pre: %s)" % (post[1], pre[1]))


    def _run_test_case(self, tc_id: str, inputs: dict, outputs: dict, relations: dict = None, relations_fn:str = None, show_values: bool = True):
        if inputs is None:
            raise RuntimeError("Inputs not specified.")

        if tc_id not in self.port_values:
            self.port_values[tc_id] = OrderedDict()

        if relations_fn is not None:
            file_relations = TestingHandler.parse_file_relations(inputs, outputs, relations_fn)
        else:
            file_relations = None

        sim_time = TestingHandler.get_next_event_time(inputs)
        while sim_time is not None:
            print("\nExecuting simulation time %.3f" % (sim_time / 1000))
            TestingHandler.execute_time(sim_time, inputs)
            TestingHandler.execute_time(sim_time, outputs)

            inp_values = {k: v.curr_state for k, v in inputs.items()}
            out_values = {k: v.curr_state for k, v in outputs.items()}
            self.port_values[tc_id][sim_time] = (inp_values, out_values)

            if show_values:
                print("Inputs:", inp_values)
                print("Outputs:", out_values)

            if self.visualizer is not None:
                self.visualizer.update(self)
                self.visualizer.show()

            if relations:
                TestingHandler.check_func_relations(inputs, outputs, relations)

            if file_relations:
                TestingHandler.check_file_relations(inputs, outputs, file_relations)

            sim_time = self.get_next_event_time(inputs)



class MetamorphicTestingHandler(TestingHandler):

    def __init__(self, input_filenames: dict, output_filenames: dict, visualizer: Visualizer = None, multival=False):
        super().__init__(visualizer)
        self.last_state = None
        self.input_filenames = input_filenames
        self.output_filenames = output_filenames
        self.multival = multival

    def run_test_case(self, tc_id: str, input_path: str, output_path: str, relations_fun: dict, relations_fn: str):
        inputs = {k: StatesMonitor(os.path.join(input_path, v), multival=self.multival) for k, v in self.input_filenames.items()}
        outputs = {k: StatesMonitor(os.path.join(output_path, v), multival=self.multival) for k, v in self.output_filenames.items()}

        self._run_test_case(tc_id, inputs, outputs, relations_fun, relations_fn)
