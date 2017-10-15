"""

Author: Davide Ferrari
August 2017

"""

import logging
import myLogger
import operator

logger = logging.getLogger('utility')
logger.addHandler(myLogger.MyHandler())
logger.setLevel(logging.DEBUG)
logger.propagate = False


class Utility(object):
    __coupling_map = dict()
    __inverse_coupling_map = dict()
    __plain_map = dict()
    __path = dict()
    __n_qubits = 0
    __ranks = dict()
    __connected = dict()
    __most_connected = []

    def __init__(self, coupling_map):
        if coupling_map:
            self.__coupling_map = coupling_map.copy()
            logger.log(logging.DEBUG, 'init() - coupling_map:\n%s', str(self.__coupling_map))
            self.invert_graph(coupling_map, self.__inverse_coupling_map)
            logger.log(logging.DEBUG, 'init() - inverse coupling map:\n%s', str(self.__inverse_coupling_map))
            for i in coupling_map:
                self.__plain_map.update({i: coupling_map[i]})
                for j in coupling_map:
                    if i in coupling_map[j]:
                        self.__plain_map[i] = self.__plain_map[i] + [j]
            logger.log(logging.DEBUG, 'init() - plain map:\n%s', str(self.__plain_map))
            self.ranking(self.__coupling_map, self.__ranks)
            self.__most_connected = self.find_max(self.__ranks)
            self.create_path(self.__most_connected[0], inverse_map=self.__inverse_coupling_map,
                             plain_map=self.__plain_map)
        else:
            logger.critical('init() - Null argument: coupling_map')
            exit(1)

    def close(self):
        self.__ranks.clear()
        self.__inverse_coupling_map.clear()
        self.__coupling_map.clear()
        self.__path.clear()
        self.__most_connected.clear()

    def explore(self, source, visiting, visited, ranks):
        for next in self.__coupling_map[visiting]:
            if next not in visited[source]:
                visited[source].append(next)
                if next not in ranks:
                    ranks.update({next: 0})
                ranks[next] = ranks[next] + 1
                self.explore(source, next, visited, ranks)

    # TODO Try using some sort of "page-ranking like" algorithm

    def ranking(self, graph, ranks):
        visited = dict()
        for source in graph:
            visited.update({source: []})
            self.explore(source, source, visited, ranks)

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
    def find_max(ranks):
        logger.debug('ranks:\n%s', str(ranks))
        most_connected = max(ranks.items(), key=operator.itemgetter(1))[0]
        found = [most_connected, ranks[most_connected]]
        logger.debug('max: %s', str(found))
        return found

    # create a valid path that connect qubits used in the circuit
    def create_path(self, start, inverse_map, plain_map):
        self.__path.update({start: -1})
        to_connect = [start] + inverse_map[start]
        count = len(self.__coupling_map) - 1
        for visiting in to_connect:
            if count <= 0:
                break
            for node in inverse_map[visiting]:
                if count <= 0:
                    break
                if node not in self.__path:
                    self.__path.update({node: visiting})
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
                    if node not in self.__path:
                        self.__path.update({node: visiting})
                        if node not in to_connect:
                            to_connect.append(node)
                        count -= 1
        logger.debug('create_path() - path:\n%s', str(self.__path))

    def cx(self, circuit, control_qubit, target_qubit, control, target):
        if target in self.__coupling_map[control]:
            logger.log(logging.VERBOSE, 'cx() - cnot: (%s, %s)', str(control), str(target))
            circuit.cx(control_qubit, target_qubit)
        elif control in self.__coupling_map[target]:
            logger.log(logging.VERBOSE, 'cx() - inverse-cnot: (%s, %s)', str(control), str(target))
            circuit.h(control_qubit)
            circuit.h(target_qubit)
            circuit.cx(target_qubit, control_qubit)
            circuit.h(control_qubit)
            circuit.h(target_qubit)
        else:
            logger.critical('cx() - Cannot connect qubit %s to qubit %s', str(control), str(target))
            exit(3)

    # place cnot gates based on the path created in create_path method
    def place_cx_(self, circuit, quantum_r, oracle='11'):
        if not oracle == '00':
            logger.log(logging.VERBOSE, 'place_cx() - oracle != 00')
            stop = self.__n_qubits // 2
            for qubit in self.__connected:
                if self.__connected[qubit] != -1:
                    if oracle == '11':
                        logger.log(logging.VERBOSE, 'place_cx() - oracle = 11')
                        self.cx(circuit, quantum_r[qubit], quantum_r[self.__connected[qubit]], qubit,
                                self.__connected[qubit])
                    elif oracle == '10':
                        logger.log(logging.VERBOSE, 'place_cx() - oracle = 10')
                        if stop > 0:
                            self.cx(circuit, quantum_r[qubit], quantum_r[self.__connected[qubit]], qubit,
                                    self.__connected[qubit])
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
        sorted_c = sorted(self.__connected.items(), key=operator.itemgetter(0))
        logger.log(logging.VERBOSE, 'place_x() - sorted_c:\n%s', str(sorted_c))
        s_0 = self.__n_qubits // 2
        i = 0
        count = self.__n_qubits - 1
        for qubit in sorted_c:
            if count <= 0:
                break
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

        max_qubits = len(self.__path)
        logger.debug('create() - N qubits: %s', str(self.__n_qubits))
        logger.debug('create() - Max qubits: %s', str(max_qubits))
        if max_qubits < self.__n_qubits:
            logger.critical('create() - Can use only up to %s qubits', str(max_qubits))
            exit(2)

        count = self.__n_qubits
        for qubit in self.__path:
            if count <= 0:
                break
            self.__connected.update({qubit: self.__path[qubit]})
            count -= 1
        logger.debug('create() - connected:\n%s', str(self.__connected))
        self.place_h(circuit, self.__most_connected[0], quantum_r, x=x)
        self.place_cx_(circuit, quantum_r, oracle=oracle)
        self.place_h(circuit, self.__most_connected[0], quantum_r, initial=False)
        if x is True:
            self.place_x(circuit, quantum_r)
        self.measure(circuit, quantum_r, classical_r)

    def envariance(self, circuit, quantum_r, classical_r, n_qubits):
        self.create(circuit, quantum_r, classical_r, n_qubits)
        self.__n_qubits = 0
        self.__connected.clear()

    def parity(self, circuit, quantum_r, classical_r, n_qubits, oracle='11', connected=None):
        if connected is None:
            connected = []
        self.create(circuit, quantum_r, classical_r, n_qubits, x=False, oracle=oracle)
        for i in self.__connected:
            connected.append(i)
        logger.debug('parity() - connected:\n%s', str(connected))
        self.__n_qubits = 0
        self.__connected.clear()
