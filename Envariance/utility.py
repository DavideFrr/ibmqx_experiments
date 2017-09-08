"""

Author: Davide Ferrari
August 2017

"""

import operator


class Utility(object):
    __inverse_coupling_map = dict()
    __from_all_to_all = dict()
    __connected = dict()
    __n_qubits = 0

    def __init__(self, coupling_map):
        if coupling_map:
            self.invert_graph(coupling_map, self.__inverse_coupling_map)
            # print(self.__inverse_coupling_map)
            for i in range(len(coupling_map)):
                self.__from_all_to_all.update({i: [-1]})
                self.__from_all_to_all[i][0] = dict()
                # print(self.__from_all_to_all)
        else:
            print("Null argument")
            exit(1)

    def close(self):
        self.__connected.clear()
        self.__n_qubits = 0
        self.__from_all_to_all.clear()
        self.__inverse_coupling_map.clear()

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

    # create a valid path that connect qubits used in the circuit
    def create_path(self, start, graph):
        self.__connected.update({start: -1})
        to_connect = [start] + graph[start]
        count = self.__n_qubits - 1
        for visiting in to_connect:
            if count <= 0:
                break
            for node in graph[visiting]:
                if count <= 0:
                    break
                if node not in self.__connected:
                    self.__connected.update({node: visiting})
                    if node not in to_connect:
                        to_connect.append(node)
                    count -= 1

    # place cnot gates based on the path created in create_path method
    def place_cx_(self, circuit, quantum_r):
        for qubit in self.__connected:
            if self.__connected[qubit] != -1:
                circuit.cx(quantum_r[qubit], quantum_r[self.__connected[qubit]])
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
    def create(self, circuit, quantum_r, classical_r, n_qubits, x=True):

        self.__n_qubits = n_qubits

        # for start in self.__inverse_coupling_map:
        #     for end in self.__inverse_coupling_map:
        #         if start != end:
        #             paths = self.find_all_paths(self.__inverse_coupling_map, start, end)
        #             if len(paths) != 0:
        #                 self.__from_all_to_all[start][0][end] = paths

        # for node in self.__from_all_to_all:
        #     print('\n%d\n' % node)
        #     print(self.__from_all_to_all[node])

        self.from_all_to_all()

        max_path = self.find_max(self.__from_all_to_all)
        if max_path[0] + 1 < self.__n_qubits:
            print('\nCan use only up to %s qubits' % str(max_path[0] + 1))
            exit(2)
        # print(max_path)
        self.create_path(max_path[1], self.__inverse_coupling_map)
        # print(self.__connected)
        self.place_h(circuit, max_path[1], quantum_r, x=x)
        self.place_cx_(circuit, quantum_r)
        self.place_h(circuit, max_path[1], quantum_r, initial=False)
        if x is True:
            self.place_x(circuit, quantum_r)
        self.measure(circuit, quantum_r, classical_r)
        self.__connected.clear()
        self.__n_qubits = 0

    def envariance(self, circuit, quantum_r, classicla_r, n_qubits):
        self.create(circuit, quantum_r, classicla_r, n_qubits)

    def oracle(self, circuit, quantum_r, classicla_r, n_qubits):
        self.create(circuit, quantum_r, classicla_r, n_qubits, x=False)
