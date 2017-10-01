"""

Author: Davide Ferrari
August 2017

"""

import logging
import operator
import math

VERBOSE = 5
logger = logging.getLogger('utility')
logger.setLevel(logging.CRITICAL)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.propagate = False

class Utility(object):
    __coupling_map = dict()
    __inverse_coupling_map = dict()
    __plain_map = dict()
    __from_all_to_all = dict()
    __connected = dict()
    __n_qubits = 0

    def __init__(self, coupling_map):
        if coupling_map:
            self.__coupling_map = coupling_map.copy()
            logger.log(VERBOSE, 'init() - coupling_map:\n%s', str(self.__coupling_map))
            self.invert_graph(coupling_map, self.__inverse_coupling_map)
            logger.log(VERBOSE, 'init() - inverse coupling map:\n%s', str(self.__inverse_coupling_map))
            for i in range(len(coupling_map)):
                self.__from_all_to_all.update({i: [-1]})
                self.__from_all_to_all[i][0] = dict()
            logger.log(VERBOSE, 'init() - from all to all:\n%s', str(self.__from_all_to_all))
            for i in coupling_map:
                self.__plain_map.update({i: coupling_map[i]})
                for j in coupling_map:
                    if i in coupling_map[j]:
                        self.__plain_map[i] = self.__plain_map[i] + [j]
            logger.log(VERBOSE, 'init() - plain map:\n%s', str(self.__plain_map))
        else:
            logger.critical('init() - Null argument: coupling_map')
            exit(1)

    def close(self):
        self.__connected.clear()
        self.__n_qubits = 0
        self.__from_all_to_all.clear()
        self.__inverse_coupling_map.clear()
        self.__coupling_map.clear()

    # create an inverted coupling-map for further use
    @staticmethod
    def invert_graph(graph, inverse_graph=None):
        if inverse_graph is None:
            inverse_graph = {}
        for end in graph:
            for start in graph[end]:
                if start not in inverse_graph:
                    inverse_graph.update({start: [end]})
                else:
                    inverse_graph[start].append(end)
        for node in graph:
            if node not in inverse_graph:
                inverse_graph.update({node: []})

    # find the most connected qubit
    @staticmethod
    def find_max(paths):
        size = -1
        node = None
        for start in paths:
            if len(paths[start][0]) > size:
                size = len(paths[start][0])
                node = start

        ret = [size, node]
        return ret

    # find all valid paths between qubits
    def find_all_paths(self, graph, start, end, path=None):
        if path is None:
            path = []
        path = path + [start]
        if start == end:
            return [path]
        if start not in graph:
            return []
        paths = []
        for node in graph[start]:
            if node not in path:
                newpaths = self.find_all_paths(graph, node, end, path)
                for newpath in newpaths:
                    paths.append(newpath)
        return paths

    def from_all_to_all(self):
        for start in self.__inverse_coupling_map:
            for end in self.__inverse_coupling_map:
                if start != end:
                    paths = self.find_all_paths(self.__inverse_coupling_map, start, end)
                    if len(paths) != 0:
                        self.__from_all_to_all[start][0][end] = paths
        logger.log(VERBOSE, 'form_all_to_all() - from_all_to_all:\n%s', str(self.__from_all_to_all))

    # create a valid path that connect qubits used in the circuit
    def create_path(self, start, inverse_map, plain_map):
        self.__connected.update({start: -1})
        to_connect = [start] + inverse_map[start]
        count = self.__n_qubits - 1
        for visiting in to_connect:
            if count <= 0:
                break
            for node in inverse_map[visiting]:
                if count <= 0:
                    break
                if node not in self.__connected:
                    self.__connected.update({node: visiting})
                    if node not in to_connect:
                        to_connect.append(node)
                    count -= 1
        changed = True
        while changed is True and count > 0:
            changed = False
            for visiting in to_connect:
                if count <= 0:
                    break
                for node in plain_map[visiting]:
                    if count <= 0:
                        break
                    if node not in self.__connected:
                        self.__connected.update({node: visiting})
                        if node not in to_connect:
                            to_connect.append(node)
                        count -= 1
            # iterable = copy.deepcopy(self.__connected)
            # for visiting in iterable:
            #     if count <= 0:
            #         break
            #     for node in plain_map[visiting]:
            #         if count <= 0:
            #             break
            #         if node not in iterable:
            #             self.__connected.update({node: visiting})
            #             changed = True
            #             count -= 1
        logger.debug('create_path() - connected:\n%s', str(self.__connected))
        return len(self.__connected)

    def cx(self, circuit, control_qubit, target_qubit, control, target):
        if target in self.__coupling_map[control]:
            logger.debug('cx() - cnot: (%s, %s)', str(control), str(target))
            circuit.cx(control_qubit, target_qubit)
        elif control in self.__coupling_map[target]:
            logger.debug('cx() - inverse-cnot: (%s, %s)', str(control), str(target))
            circuit.barrier()
            circuit.h(control_qubit)
            circuit.h(target_qubit)
            circuit.cx(target_qubit, control_qubit)
            circuit.h(control_qubit)
            circuit.h(target_qubit)
            circuit.barrier()
        else:
            logger.critical('cx() - Cannot connect qubit %s to qubit %s', str(control), str(target))
            exit(3)

    # place cnot gates based on the path created in create_path method
    def place_cx_(self, circuit, quantum_r, oracle='11'):
        if not oracle == '00':
            logger.log(VERBOSE, 'place_cx() - oracle != 00')
            stop = math.floor(self.__n_qubits/2)
            for qubit in self.__connected:
                if self.__connected[qubit] != -1:
                    if oracle == '11':
                        logger.log(VERBOSE, 'place_cx() - oracle = 11')
                        self.cx(circuit, quantum_r[qubit], quantum_r[self.__connected[qubit]], qubit, self.__connected[qubit])
                    elif oracle == '10':
                        logger.log(VERBOSE, 'place_cx() - oracle = 10')
                        if stop > 0:
                            self.cx(circuit, quantum_r[qubit], quantum_r[self.__connected[qubit]], qubit, self.__connected[qubit])
                            stop -= 1



    # place Hadamard gates
    def place_h(self, circuit, start, quantum_r, initial=True, x=True):
        for qubit in self.__connected:
            if qubit != start:
                circuit.h(quantum_r[qubit])
            else:
                if initial is True:
                    if x is True:
                        circuit.x(quantum_r[qubit])
                else:
                    circuit.h(quantum_r[qubit])

    # place Pauli-X gates
    def place_x(self, circuit, quantum_r):
        # s_0 = math.floor(self.__n_qubits/2)
        sorted_c = sorted(self.__connected.items(), key=operator.itemgetter(0))
        logger.log(VERBOSE, 'place_x() - place_x - sorted_c:\n%s', str(sorted_c))
        s_0 = self.__n_qubits // 2
        i = 0
        for qubit in sorted_c:
            if i >= s_0:
                circuit.x(quantum_r[qubit[0]])
            else:
                circuit.iden(quantum_r[qubit[0]])
            i += 1
        i = 0
        for qubit in sorted_c:
            if i >= s_0:
                circuit.iden(quantum_r[qubit[0]])
            else:
                circuit.x(quantum_r[qubit[0]])
            i += 1

    # final measure
    def measure(self, circuit, quantum_r, classical_r):
        for qubit in self.__connected:
            circuit.measure(quantum_r[qubit], classical_r[qubit])

    # create the circuit
    def create(self, circuit, quantum_r, classical_r, n_qubits, x=True, oracle='11'):

        self.__n_qubits = n_qubits

        self.from_all_to_all()

        max_path = self.find_max(self.__from_all_to_all)
        logger.debug('create() - max_path: %s', str(max_path))
        max_qubits = self.create_path(max_path[1], inverse_map=self.__inverse_coupling_map, plain_map=self.__plain_map)
        logger.debug('create() - N qubits: %s', str(self.__n_qubits))
        logger.debug('create() - Max qubits: %s', str(max_qubits))
        if max_qubits < self.__n_qubits:
            logger.critical('create() - Can use only up to %s qubits', str(max_qubits))
            exit(2)
        self.place_h(circuit, max_path[1], quantum_r, x=x)
        self.place_cx_(circuit, quantum_r, oracle=oracle)
        self.place_h(circuit, max_path[1], quantum_r, initial=False)
        if x is True:
            self.place_x(circuit, quantum_r)
        self.measure(circuit, quantum_r, classical_r)

    def envariance(self, circuit, quantum_r, classicla_r, n_qubits):
        self.create(circuit, quantum_r, classicla_r, n_qubits)
        self.__connected.clear()
        self.__n_qubits = 0

    def parity(self, circuit, quantum_r, classicla_r, n_qubits, oracle='11', connected=[]):
        self.create(circuit, quantum_r, classicla_r, n_qubits, x=False, oracle=oracle)
        for i in self.__connected:
            connected.append(i)
        logger.debug('parity() - connected:\n%s', str(connected))
        self.__connected.clear()
        self.__n_qubits = 0
