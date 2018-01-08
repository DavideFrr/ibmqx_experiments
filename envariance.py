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
from time import sleep

import myLogger
import os
import operator

from utility import Utility

import sys

sys.path.append(  # solve the relative dependencies if you clone QISKit from the Git repo and use like a global.
    "../qiskit-sdk-py")

from qiskit import QuantumProgram
import Qconfig

logger = logging.getLogger('envariance')
logger.addHandler(myLogger.MyHandler())
logger.setLevel(logging.INFO)
logger.propagate = False

coupling_map_qx2 = {
    0: [1, 2],
    1: [2],
    2: [],
    3: [2, 4],
    4: [2],
}

coupling_map_qx3 = {
    0: [1],
    1: [2],
    2: [3],
    3: [14],
    4: [3, 5],
    5: [],
    6: [7, 11],
    7: [10],
    8: [7],
    9: [8, 10],
    10: [],
    11: [10],
    12: [5, 11, 13],
    13: [4, 14],
    14: [],
    15: [0, 14],
}

coupling_map_qx4 = {
    0: [],
    1: [0],
    2: [0, 1, 4],
    3: [2, 4],
    4: [],
}

coupling_map_qx5 = {
    0: [],
    1: [0, 2],
    2: [3],
    3: [4, 14],
    4: [],
    5: [4],
    6: [5, 7, 11],
    7: [10],
    8: [7],
    9: [8, 10],
    10: [],
    11: [10],
    12: [5, 11, 13],
    13: [4, 14],
    14: [],
    15: [0, 2, 14],
}

# Back-end devices
qx2 = 'ibmqx2'

qx3 = 'ibmqx3'

qx4 = 'ibmqx4'

qx5 = 'ibmqx5'

online_sim = 'ibmqx_qasm_simulator'

local_sim = 'local_qasm_simulator'


# launch envariance experiment on the given device
def launch_exp(execution, device, utility, n_qubits, num_shots=1024, directory='Data_Envariance/'):
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
        logger.critical('API Exception occurred, retrying\nQubits %d - Execution %d - Shots %d', n_qubits, execution, num_shots)
        launch_exp(execution, device, utility, n_qubits=n_qubits, num_shots=num_shots, directory=directory)
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
        logger.critical('Exception occurred, retrying\nQubits %d - Execution %d - Shots %d', n_qubits, execution, num_shots)
        launch_exp(execution, device, utility, n_qubits=n_qubits, num_shots=num_shots, directory=directory)
        return

    try:
        counts = result.get_counts("envariance")
    except Exception:
        logger.critical('Exception occurred, retrying\nQubits %d - Execution %d - Shots %d', n_qubits, execution, num_shots)
        launch_exp(execution, device, utility, n_qubits=n_qubits, num_shots=num_shots, directory=directory)
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
        for n in range(n_qubits-stop):
            sorted_v.append(reverse[connected[n + stop]])
        for n in range(stop):
            sorted_v.append(reverse[connected[n]])
        value = ''.join(str(v) for v in sorted_v)
        results.update({value: i[1]})
        out_f.write(value + '\t' + str(i[1]) + '\n')

    out_f.close()


executions = 10

shots = [
    1024,
    2048,
    8192
]

# launch_exp takes the argument device which can either be qx2, qx3, qx4, qx5, online_sim or local_sim
logger.info('Started')

utility_qx4 = Utility(coupling_map_qx4)
for execution in range(1, executions+1, 1):
    for n_shots in shots:
        # Comment the experiments you don't want to run
        logger.info('Qubits %d - Execution %d - Shots %d', 2, execution, n_shots)
        launch_exp(execution, online_sim, utility_qx4, n_qubits=2, num_shots=n_shots)
        logger.info('Qubits %d - Execution %d - Shots %d', 3, execution, n_shots)
        launch_exp(execution, qx4, utility_qx4, n_qubits=3, num_shots=n_shots)
        logger.info('Qubits %d - Execution %d - Shots %d', 5, execution, n_shots)
        launch_exp(execution, qx4, utility_qx4, n_qubits=5, num_shots=n_shots)

utility_qx4.close()


utility_qx5 = Utility(coupling_map_qx5)
for execution in range(1, executions+1, 1):
    for n_shots in shots:
        # Comment the experiments you don't want to run
        logger.info('Qubits %d - Execution %d - Shots %d', 2, execution, n_shots)
        launch_exp(execution, qx5, utility_qx5, n_qubits=2, num_shots=n_shots)
        logger.info('Qubits %d - Execution %d - Shots %d', 3, execution, n_shots)
        launch_exp(execution, qx5, utility_qx5, n_qubits=3, num_shots=n_shots)
        logger.info('Qubits %d - Execution %d - Shots %d', 5, execution, n_shots)
        launch_exp(execution, qx5, utility_qx5, n_qubits=5, num_shots=n_shots)
        logger.info('Qubits %d - Execution %d - Shots %d', 7, execution, n_shots)
        launch_exp(execution, qx5, utility_qx5, n_qubits=7, num_shots=n_shots)
        logger.info('Qubits %d - Execution %d - Shots %d', 9, execution, n_shots)
        launch_exp(execution, qx5, utility_qx5, n_qubits=9, num_shots=n_shots)
        logger.info('Qubits %d - Execution %d - Shots %d', 12, execution, n_shots)
        launch_exp(execution, qx5, utility_qx5, n_qubits=12, num_shots=n_shots)
        logger.info('Qubits %d - Execution %d - Shots %d', 14, execution, n_shots)
        launch_exp(execution, qx5, utility_qx5, n_qubits=14, num_shots=n_shots)
        logger.info('Qubits %d - Execution %d - Shots %d', 16, execution, n_shots)
        launch_exp(execution, qx5, utility_qx5, n_qubits=16, num_shots=n_shots)

utility_qx5.close()

logger.info('All done.')
