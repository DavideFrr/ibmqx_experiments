"""

Author: Davide Ferrari
August 2017

"""

import logging

import myLogger
import os
import operator

from utility import Utility

import sys

sys.path.append(  # solve the relative dependencies if you clone QISKit from the Git repo and use like a global.
    "D:/PyCharm/qiskit-sdk-py")

import Qconfig
from qiskit import QuantumProgram

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
def launch_exp(execution, queries, device, utility, n_qubits, oracle='11', num_shots=1024):
    size = 0

    ordered_q = []

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
        if n_qubits <= 16:
            size = 16
    else:
        logger.critical('launch_exp() - Unknown device.')
        exit(3)

    Q_program = QuantumProgram()

    Q_program.set_api(Qconfig.APItoken, Qconfig.config["url"])  # set the APIToken and API url

    quantum_r = Q_program.create_quantum_register("qr", size)

    classical_r = Q_program.create_classical_register("cr", size)

    circuit = Q_program.create_circuit('parity', [quantum_r], [classical_r])

    utility.parity(circuit=circuit, quantum_r=quantum_r, classical_r=classical_r, n_qubits=n_qubits, oracle=oracle,
                   connected=ordered_q)

    QASM_source = Q_program.get_qasm('parity')

    logger.info('launch_exp() - QASM:\n%s', str(QASM_source))

    result = Q_program.execute(['parity'], backend=device, wait=2, timeout=5000, shots=num_shots, max_credits=5)

    counts = result.get_counts('parity')

    logger.debug('launch_exp() - counts:\n%s', str(counts))

    sorted_c = sorted(counts.items(), key=operator.itemgetter(1), reverse=True)

    filename = 'Data_Parity/' + device + '/' + oracle + '/' + 'execution' + str(
        execution) + '/' + device + '_' + str(
        num_shots) + 'queries_' + oracle + '_' + str(
        n_qubits) + '_qubits_parity.txt'
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    out_f = open(filename, 'w')

    # store counts in txt file and xlsx file
    out_f.write('VALUES\t\tCOUNTS\n\n')
    logger.debug('launch_exp() - oredred_q:\n%s', str(ordered_q))
    stop = n_qubits // 2
    for i in sorted_c:
        reverse = i[0][::-1]
        logger.log(logging.VERBOSE, 'launch_exp() - reverse in for 1st loop: %s', str(reverse))
        sorted_v = [reverse[ordered_q[0]]]
        logger.log(logging.VERBOSE, 'launch_exp() - oredred_q[0] in 1st for loop: %s', str(ordered_q[0]))
        logger.log(logging.VERBOSE, 'launch_exp() - sorted_v in 1st for loop: %s', str(sorted_v))
        for n in range(stop):
            sorted_v.append(reverse[ordered_q[n + 1]])
            logger.log(logging.VERBOSE, 'launch_exp() - ordered_q[n+1], sorted_v[n+1] in 2nd for loop: %s,%s',
                       str(ordered_q[n + 1]), str(sorted_v[n + 1]))
            if (n + stop + 1) != n_qubits:
                sorted_v.append(reverse[ordered_q[n + stop + 1]])
                logger.log(logging.VERBOSE, 'launch_exp() - ordered_q[n+stop+1], sorted_v[n+2] in 2nd for loop: %s%s',
                           str(ordered_q[n + stop + 1]), str(sorted_v[n + 2]))
        value = ''.join(str(v) for v in sorted_v)
        results.update({value: i[1]})
        out_f.write(value + '\t' + str(i[1]) + '\n')

    out_f.close()


# device is the device you want to run the experiment on
# executions is the number of different experiment you want to run
# queries is the maximum number of queries
# oracles are the strings you want to learn: '10' for '10...10', '11' for '11...11', '00' for '00...00'
device = qx5

executions = 50

queries = 50

oracles = [
    '00',
    '10',
    '11',
]

# launch_exp takes the argument device which can either be qx2, qx3, online_sim or local_sim
logger.info('Started')

utility = Utility(coupling_map_qx5)
directory = 'Data_Parity/'
os.makedirs(os.path.dirname(directory), exist_ok=True)

for execution in range(1, executions+1, 1):

    for oracle in oracles:

        # Comment the experiments you don't want to run
        for n_queries in range(5, queries+5, 5):
            launch_exp(execution, queries, device, utility, n_qubits=3, oracle=oracle, num_shots=n_queries)
            launch_exp(execution, queries, device, utility, n_qubits=5, oracle=oracle, num_shots=n_queries)
            launch_exp(execution, queries, device, utility, n_qubits=7, oracle=oracle, num_shots=n_queries)
            launch_exp(execution, queries, device, utility, n_qubits=9, oracle=oracle, num_shots=n_queries)
            launch_exp(execution, queries, device, utility, n_qubits=12, oracle=oracle, num_shots=n_queries)
            launch_exp(execution, queries, device, utility, n_qubits=14, oracle=oracle, num_shots=n_queries)
            launch_exp(execution, queries, device, utility, n_qubits=16, oracle=oracle, num_shots=n_queries)

utility.close()

logger.info('All done.')
