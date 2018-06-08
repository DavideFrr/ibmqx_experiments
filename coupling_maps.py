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

# Module for coupling-maps

from qiskit import register, get_backend
import config


# qx2 = {
#     0: [1, 2],
#     1: [2],
#     2: [],
#     3: [2, 4],
#     4: [2],
# }
#
# qx3 = {
#     0: [1],
#     1: [2],
#     2: [3],
#     3: [14],
#     4: [3, 5],
#     5: [],
#     6: [7, 11],
#     7: [10],
#     8: [7],
#     9: [8, 10],
#     10: [],
#     11: [10],
#     12: [5, 11, 13],
#     13: [4, 14],
#     14: [],
#     15: [0, 14],
# }
#
# qx4 = {
#     0: [],
#     1: [0],
#     2: [0, 1, 4],
#     3: [2, 4],
#     4: [],
# }
#
# qx5 = {
#     0: [],
#     1: [0, 2],
#     2: [3],
#     3: [4, 14],
#     4: [],
#     5: [4],
#     6: [5, 7, 11],
#     7: [10],
#     8: [7],
#     9: [8, 10],
#     10: [],
#     11: [10],
#     12: [5, 11, 13],
#     13: [4, 14],
#     14: [],
#     15: [0, 2, 14],
# }

def qx5():
    register(config.APItoken, config.URL)
    configuration = get_backend('ibmqx5').configuration
    couplings = configuration['coupling_map']
    coupling_map = dict()
    for n in range(configuration['n_qubits']):
        coupling_map.update({n: []})
    for coupling in couplings:
        coupling_map[coupling[0]].append(coupling[1])
    return coupling_map


def qx4():
    register(config.APItoken, config.URL)
    configuration = get_backend('ibmqx4').configuration
    couplings = configuration['coupling_map']
    coupling_map = dict()
    for n in range(configuration['n_qubits']):
        coupling_map.update({n: []})
    for coupling in couplings:
        coupling_map[coupling[0]].append(coupling[1])
    return coupling_map