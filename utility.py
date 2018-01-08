# Copyright 2017 Quantum Information Science, University of Parma, Italy. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =============================================================================

__author__ = "Davide Ferrari"
__copyright__ = "Copyright 2017, Quantum Information Science, University of Parma, Italy"
__license__ = "Apache"
__version__ = "2.0"
__email__ = "davide.ferrari8@studenti.unipr.it"

import logging
import myLogger
import operator

logger = logging.getLogger('utility')
logger.addHandler(myLogger.MyHandler())
logger.setLevel(logging.CRITICAL)
logger.propagate = False


class Utility(object):

    def __init__(self, coupling_map):
        self.__coupling_map = dict()
        self.__inverse_coupling_map = dict()
        self.__plain_map = dict()
        self.__path = dict()
        self.__n_qubits = 0
        self.__ranks = dict()
        self.__connected = dict()
        self.__most_connected = []
        if coupling_map:
            self.__coupling_map = coupling_map.copy()
            logger.log(logging.DEBUG, 'init() - coupling_map:\n%s', str(self.__coupling_map))
            self.invert_graph(coupling_map, self.__inverse_coupling_map)
            logger.log(logging.DEBUG, 'init() - inverse coupling map:\n%s', str(self.__inverse_coupling_map))
            for i in coupling_map:
                self.__plain_map.update({i: self.__inverse_coupling_map[i] + coupling_map[i]})
            logger.debug('init() - plain map:\n%s', str(self.__plain_map))
            self.start_explore(self.__coupling_map, self.__ranks)
            self.__most_connected = self.find_max(self.__ranks)
            self.create_path(self.__most_connected[0], plain_map=self.__plain_map)
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

    # TODO Try using some sort of centrality algorithm

    def start_explore(self, graph, ranks):
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
    def create_path(self, start, plain_map):
        self.__path.update({start: -1})
        to_connect = [start] + self.__inverse_coupling_map[start]
        count = len(self.__coupling_map) - 1
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
                            changed = True;
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
    def place_cx(self, circuit, quantum_r, oracle='11'):
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
        self.place_cx(circuit, quantum_r, oracle=oracle)
        self.place_h(circuit, self.__most_connected[0], quantum_r, initial=False)
        if x is True:
            self.place_x(circuit, quantum_r)
        self.measure(circuit, quantum_r, classical_r)

    def envariance(self, circuit, quantum_r, classical_r, n_qubits):
        self.create(circuit, quantum_r, classical_r, n_qubits)
        sorted_c = sorted(self.__connected.items(), key=operator.itemgetter(0))
        connected = list(zip(*sorted_c))[0]
        logger.debug('envariance() - connected:\n%s', str(connected))
        self.__n_qubits = 0
        self.__connected.clear()
        return connected

    def parity(self, circuit, quantum_r, classical_r, n_qubits, oracle='11'):
        self.create(circuit, quantum_r, classical_r, n_qubits, x=False, oracle=oracle)
        connected = list(self.__connected.keys())
        logger.debug('parity() - connected:\n%s', str(connected))
        self.__n_qubits = 0
        self.__connected.clear()
        return connected
