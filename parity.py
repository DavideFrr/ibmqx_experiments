import sys

import  logging

import  os

sys.path.append(  # solve the relative dependencies if you clone QISKit from the Git repo and use like a global.
    "D:/PyCharm/qiskit-sdk-py")

from qiskit import QuantumProgram
import Qconfig
from utility import Utility
import operator
import math
import xlsxwriter
import time

VERBOSE = 5
logger = logging.getLogger('parity')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)
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
def launch_exp(workbook, device, utility, n_qubits, oracle='11', num_shots=1024):
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

    circuit = Q_program.create_circuit("parity", [quantum_r], [classical_r])

    utility.parity(circuit=circuit, quantum_r=quantum_r, classicla_r=classical_r, n_qubits=n_qubits, oracle=oracle, connected=ordered_q)

    QASM_source = Q_program.get_qasm("parity")

    logger.info('launch_exp() - QASM:\n%s', str(QASM_source))

    result = Q_program.execute(["parity"], backend=device, wait=2, timeout=480, shots=num_shots, max_credits=10, silent=False)

    counts = result.get_counts("parity")

    logger.debug('launch_exp() - counts:\n%s', str(counts))

    sorted_c = sorted(counts.items(), key=operator.itemgetter(1), reverse=True)

    filename = 'Data_Parity/' + device + '/' + device + '_' + str(num_shots) + 'queries_' + str(n_qubits) + '_qubits_parity.txt'
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    out_f = open(filename, 'w')

    # store counts in txt file and xlsx file
    out_f.write('VALUES\t\tCOUNTS\n\n')
    logger.debug('launch_exp() - oredred_q:\n%s', str(ordered_q))
    stop = math.floor((n_qubits)/2)
    for i in sorted_c:
        reverse = i[0][::-1]
        logger.log(VERBOSE, 'launch_exp() - reverse in for 1st loop: %s', str(reverse))
        sorted_v = [reverse[ordered_q[0]]]
        logger.log(VERBOSE, 'launch_exp() - oredred_q[0] in 1st for loop: %s', str(ordered_q[0]))
        logger.log(VERBOSE, 'launch_exp() - sorted_v in 1st for loop: %s', str(sorted_v))
        for n in range(stop):
            sorted_v.append(reverse[ordered_q[n+1]])
            logger.log(VERBOSE, 'launch_exp() - ordered_q[n+1], sorted_v[n+1] in 2nd for loop: %s,%s', str(ordered_q[n+1]), str(sorted_v[n+1]))
            sorted_v.append(reverse[ordered_q[n+stop+1]])
            logger.log(VERBOSE, 'launch_exp() - ordered_q[n+stop+1], sorted_v[n+2] in 2nd for loop: %s%s', str(ordered_q[n+stop+1]), str(sorted_v[n+2]))
        value = ''.join(str(v) for v in sorted_v)
        results.update({value: i[1]})
        out_f.write(value + '\t' + str(i[1]) + '\n')

    out_f.close()

    sheet = str(num_shots) + '_' + str(n_qubits)

    worksheet = workbook.add_worksheet(sheet)
    bold = workbook.add_format({'bold': True})
    binary = workbook.add_format()
    binary.set_num_format_index('00000')

    worksheet.write(0, 0, 'Values', bold)
    worksheet.write(0, 1, 'Counts', bold)
    worksheet.write(0, 2, 'Probability', bold)
    worksheet.write(0, 3, 'Error', bold)
    row = 1
    col = 0
    total = 0
    correct = 0
    zero = '0'
    one = '1'
    one_zero = '1'
    one_one_zero = '1'
    for i in range(math.floor(n_qubits/2)):
        zero += '00'
        one += '11'
        one_zero += '00'
        one_one_zero += '10'

    for i in results:
        if i[0] != '0':
            worksheet.write(row, col, i, binary)
            worksheet.write(row, col + 1, results[i])
            worksheet.write(row, col + 2, results[i] / num_shots)
            total += results[i]
            if i == one_zero and oracle == '00':
                correct = results[i]
            if i == one and oracle == '11':
                correct = results[i]
            if i == one_one_zero and oracle == '10':
                correct = results[i]
            row += 1
    error = (1 - (correct/total))*100

    worksheet.write(row, col + 1, total)
    worksheet.write(1, 3, error)


shots = 200

oracles = [
    '00',
    '10',
    '11'
]

# launch_exp takes the argument device which can either be qx2, qx3, online_sim or local_sim
# oracle is the srting you wont to learn: '10' for '10...10', '11' for '11...11', '00' for '00...00'
logger.info('Started')

utility = Utility(coupling_map_qx5)
directory = 'Data_Parity/'
os.makedirs(os.path.dirname(directory), exist_ok=True)

for oracle in oracles:
    workbook = xlsxwriter.Workbook(directory + 'ibmqx5_n_qubits_' + oracle + '_parity.xlsx')
    for n_shots in range(10, 210, 10):
        launch_exp(workbook, online_sim, utility, n_qubits=3, oracle=oracle, num_shots=n_shots)
        time.sleep(2)
        launch_exp(workbook, online_sim, utility, n_qubits=5, oracle=oracle, num_shots=n_shots)
        time.sleep(2)
        launch_exp(workbook, online_sim, utility, n_qubits=7, oracle=oracle, num_shots=n_shots)
        time.sleep(2)
        launch_exp(workbook, online_sim, utility, n_qubits=9, oracle=oracle, num_shots=n_shots)
        time.sleep(2)
        launch_exp(workbook, online_sim, utility, n_qubits=12, oracle=oracle, num_shots=n_shots)
        time.sleep(2)
        launch_exp(workbook, online_sim, utility, n_qubits=14, oracle=oracle, num_shots=n_shots)
        time.sleep(2)
        launch_exp(workbook, online_sim, utility, n_qubits=16, oracle=oracle, num_shots=n_shots)
        time.sleep(2)
    workbook.close()

utility.close()

logger.info('All done.')
