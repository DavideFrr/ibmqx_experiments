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

import os
from time import sleep
from devices import *
import logging
import myLogger
import operator

import sys

sys.path.append(  # solve the relative dependencies if you clone QISKit from the Git repo and use like a global.
    "../qiskit-sdk-py")

from qiskit import QuantumProgram
import Qconfig

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
        to_connect = [start]
        max = len(self.__coupling_map)
        logger.debug('create_path() - max:\n%s', str(max))
        count = max - 1
        changed = True
        visiting = 0
        while count > 0:
            logger.debug('create_path() - visiting:\n%s - %s', str(visiting), str(to_connect[visiting]))
            # for visiting in to_connect:
            if count <= 0:
                break
            for node in plain_map[to_connect[visiting]]:
                if count <= 0:
                    break
                if node not in self.__path:
                    self.__path.update({node: to_connect[visiting]})
                    count -= 1
                    logger.debug('create_path() - path:\n%s', str(self.__path))
                    if node not in to_connect:
                        to_connect.append(node)
            visiting += 1
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


# launch envariance experiment on the given device
def envariance_exec(execution, device, utility, n_qubits, num_shots=1024, directory='Data_Envariance/'):
    os.makedirs(os.path.dirname(directory), exist_ok=True)

    size = 0

    results = dict()

    if device == qx2 or device == qx4:
        if n_qubits <= 5:
            size = 5
            # device = 'ibmqx_qasm_simulator'
        else:
            logger.critical('launch_exp() - Too much qubits for %s !', device)
            exit(1)
    elif device == qx3 or device == qx5:
        if n_qubits <= 16:
            size = 16
            # device = 'ibmqx_qasm_simulator'
        else:
            logger.critical('launch_exp() - Too much qubits for %s !', device)
            exit(2)
    elif device == online_sim:
        if n_qubits <= 5:
            size = 5
        elif n_qubits <= 16:
            size = 16
    else:
        logger.critical('launch_exp() - Unknown device.')
        exit(3)

    Q_program = QuantumProgram()

    try:
        Q_program.set_api(Qconfig.APItoken, Qconfig.config["url"])  # set the APIToken and API url
    except ConnectionError:
        sleep(900)
        logger.critical('API Exception occurred, retrying\nQubits %d - Execution %d - Shots %d', n_qubits, execution,
                        num_shots)
        envariance_exec(execution, device, utility, n_qubits=n_qubits, num_shots=num_shots, directory=directory)
        return

    quantum_r = Q_program.create_quantum_register("qr", size)

    classical_r = Q_program.create_classical_register("cr", size)

    circuit = Q_program.create_circuit("envariance", [quantum_r], [classical_r])

    connected = utility.envariance(circuit=circuit, quantum_r=quantum_r, classical_r=classical_r, n_qubits=n_qubits)

    QASM_source = Q_program.get_qasm("envariance")

    logger.debug('launch_exp() - QASM:\n%s', str(QASM_source))

    while True:
        try:
            backend_status = Q_program.get_backend_status(device)
            if ('available' in backend_status and backend_status['available'] is False) \
                    or ('busy' in backend_status and backend_status['busy'] is True):
                logger.critical('%s currently offline, waiting...', device)
                while Q_program.get_backend_status(device)['available'] is False:
                    sleep(1800)
                logger.critical('%s is back online, resuming execution', device)
        except ConnectionError:
            logger.critical('Error getting backend status, retrying...')
            sleep(900)
            continue
        except ValueError:
            logger.critical('Backend is not available, waiting...')
            sleep(900)
            continue
        break

    if Q_program.get_api().get_my_credits()['remaining'] < 3:
        logger.critical('Qubits %d - Execution %d - Shots %d ---- Waiting for credits to replenish...',
                        n_qubits, execution, num_shots)
        while Q_program.get_api().get_my_credits()['remaining'] < 3:
            sleep(900)
        logger.critical('Credits replenished, resuming execution')

    try:
        result = Q_program.execute(["envariance"], backend=device, wait=2, timeout=1000, shots=num_shots, max_credits=5)
    except Exception:
        sleep(900)
        logger.critical('Exception occurred, retrying\nQubits %d - Execution %d - Shots %d', n_qubits, execution,
                        num_shots)
        envariance_exec(execution, device, utility, n_qubits=n_qubits, num_shots=num_shots, directory=directory)
        return

    try:
        counts = result.get_counts("envariance")
    except Exception:
        logger.critical('Exception occurred, retrying\nQubits %d - Execution %d - Shots %d', n_qubits, execution,
                        num_shots)
        envariance_exec(execution, device, utility, n_qubits=n_qubits, num_shots=num_shots, directory=directory)
        return

    logger.debug('launch_exp() - counts:\n%s', str(counts))

    sorted_c = sorted(counts.items(), key=operator.itemgetter(1), reverse=True)

    filename = directory + device + '/' + 'execution' + str(
        execution) + '/' + device + '_' + str(num_shots) + '_' + str(
        n_qubits) + '_qubits_envariance.txt'
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    out_f = open(filename, 'w')

    # store counts in txt file and xlsx file
    out_f.write('VALUES\t\tCOUNTS\n\n')

    stop = n_qubits // 2
    for i in sorted_c:
        reverse = i[0][::-1]
        sorted_v = []
        for n in range(n_qubits - stop):
            sorted_v.append(reverse[connected[n + stop]])
        for n in range(stop):
            sorted_v.append(reverse[connected[n]])
        value = ''.join(str(v) for v in sorted_v)
        results.update({value: i[1]})
        out_f.write(value + '\t' + str(i[1]) + '\n')

    out_f.close()


# launch parity experiment on the given device
def parity_exec(execution, device, utility, n_qubits, oracle='11', num_shots=1024, directory='Data_Parity/'):
    os.makedirs(os.path.dirname(directory), exist_ok=True)

    size = 0

    results = dict()

    if device == qx2 or device == qx4:
        if n_qubits <= 5:
            size = 5
            # device = 'ibmqx_qasm_simulator'
        else:
            logger.critical('launch_exp() - Too much qubits for %s !', device)
            exit(1)
    elif device == qx3 or device == qx5:
        if n_qubits <= 16:
            size = 16
            # device = 'ibmqx_qasm_simulator'
        else:
            logger.critical('launch_exp() - Too much qubits for %s !', device)
            exit(2)
    elif device == online_sim:
        if n_qubits <= 5:
            size = 5
        elif n_qubits <= 16:
            size = 16
    else:
        logger.critical('launch_exp() - Unknown device.')
        exit(3)

    Q_program = QuantumProgram()

    try:
        Q_program.set_api(Qconfig.APItoken, Qconfig.config["url"])  # set the APIToken and API url
    except ConnectionError:
        sleep(900)
        logger.critical('API Exception occurred, retrying\nQubits %d - Oracle %s - Execution %d - Queries %d', n_qubits,
                    oracle,
                    execution, num_shots)
        parity_exec(execution, device, utility, n_qubits=n_qubits, oracle=oracle, num_shots=num_shots, directory=directory)
        return

    quantum_r = Q_program.create_quantum_register("qr", size)

    classical_r = Q_program.create_classical_register("cr", size)

    circuit = Q_program.create_circuit('parity', [quantum_r], [classical_r])

    connected = utility.parity(circuit=circuit, quantum_r=quantum_r, classical_r=classical_r, n_qubits=n_qubits,
                               oracle=oracle)

    QASM_source = Q_program.get_qasm('parity')

    logger.debug('launch_exp() - QASM:\n%s', str(QASM_source))

    while True:
        try:
            backend_status = Q_program.get_backend_status(device)
            if ('available' in backend_status and backend_status['available'] is False) \
                    or ('busy' in backend_status and backend_status['busy'] is True):
                logger.critical('%s currently offline, waiting...', device)
                while Q_program.get_backend_status(device)['available'] is False:
                    sleep(1800)
                logger.critical('%s is back online, resuming execution', device)
        except ConnectionError:
            logger.critical('Error getting backend status, retrying...')
            sleep(900)
            continue
        except ValueError:
            logger.critical('Backend is not available, waiting...')
            sleep(900)
            continue
        break

    if Q_program.get_api().get_my_credits()['remaining'] < 3:
        logger.critical('Qubits %d - Oracle %s - Execution %d - Queries %d ---- Waiting for credits to replenish...',
                    n_qubits, oracle,
                    execution, num_shots)
        while Q_program.get_api().get_my_credits()['remaining'] < 3:
            sleep(900)
        logger.critical('Credits replenished, resuming execution')

    try:
        result = Q_program.execute(['parity'], backend=device, wait=2, timeout=1000, shots=num_shots, max_credits=5)
    except Exception:
        sleep(900)
        logger.critical('Exception occurred, retrying\nQubits %d - Oracle %s - Execution %d - Queries %d', n_qubits, oracle,
                    execution, num_shots)
        parity_exec(execution, device, utility, n_qubits=n_qubits, oracle=oracle, num_shots=num_shots, directory=directory)
        return

    try:
        counts = result.get_counts('parity')
    except Exception:
        logger.critical('Exception occurred, retrying\nQubits %d - Oracle %s - Execution %d - Queries %d', n_qubits, oracle,
                    execution, num_shots)
        parity_exec(execution, device, utility, n_qubits=n_qubits, oracle=oracle, num_shots=num_shots, directory=directory)
        return

    logger.debug('launch_exp() - counts:\n%s', str(counts))

    sorted_c = sorted(counts.items(), key=operator.itemgetter(1), reverse=True)

    filename = directory + device + '/' + oracle + '/' + 'execution' + str(
        execution) + '/' + device + '_' + str(
        num_shots) + 'queries_' + oracle + '_' + str(
        n_qubits) + '_qubits_parity.txt'
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    out_f = open(filename, 'w')

    # store counts in txt file and xlsx file
    out_f.write('VALUES\t\tCOUNTS\n\n')
    logger.debug('launch_exp() - oredred_q:\n%s', str(connected))
    stop = n_qubits // 2
    for i in sorted_c:
        reverse = i[0][::-1]
        logger.log(logging.VERBOSE, 'launch_exp() - reverse in for 1st loop: %s', str(reverse))
        sorted_v = [reverse[connected[0]]]
        logger.log(logging.VERBOSE, 'launch_exp() - connected[0] in 1st for loop: %s', str(connected[0]))
        logger.log(logging.VERBOSE, 'launch_exp() - sorted_v in 1st for loop: %s', str(sorted_v))
        for n in range(stop):
            sorted_v.append(reverse[connected[n + 1]])
            logger.log(logging.VERBOSE, 'launch_exp() - connected[n+1], sorted_v[n+1] in 2nd for loop: %s,%s',
                       str(connected[n + 1]), str(sorted_v[n + 1]))
            if (n + stop + 1) != n_qubits:
                sorted_v.append(reverse[connected[n + stop + 1]])
                logger.log(logging.VERBOSE, 'launch_exp() - connected[n+stop+1], sorted_v[n+2] in 2nd for loop: %s%s',
                           str(connected[n + stop + 1]), str(sorted_v[n + 2]))
        value = ''.join(str(v) for v in sorted_v)
        results.update({value: i[1]})
        out_f.write(value + '\t' + str(i[1]) + '\n')

    out_f.close()
