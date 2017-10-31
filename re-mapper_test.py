"""

Author: Davide Ferrari
August 2017

This is to test the auto re-mapping functionality of QISKit on ibmqx3
"""

import logging
import myLogger
import sys

sys.path.append(  # solve the relative dependencies if you clone QISKit from the Git repo and use like a global.
    "D:/PyCharm/qiskit-sdk-py")

from qiskit import QuantumProgram
import Qconfig
import operator

logger = logging.getLogger('envariance')
logger.addHandler(myLogger.MyHandler())
logger.setLevel(logging.INFO)
logger.propagate = False

# Back-end devices
qx2 = 'ibmqx2'

qx3 = 'ibmqx3'

qx4 = 'ibmqx4'

qx5 = 'ibmqx5'

online_sim = 'ibmqx_qasm_simulator'

local_sim = 'local_qasm_simulator'

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

size = 0

device = qx5

# Number of qubits to be used
n_qubits = 16

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

s_0 = n_qubits // 2

Q_program = QuantumProgram()

Q_program.set_api(Qconfig.APItoken, Qconfig.config["url"])  # set the APIToken and API url

quantum_r = Q_program.create_quantum_register("qr", size)

classical_r = Q_program.create_classical_register("cr", size)

circuit = Q_program.create_circuit("re-mapper", [quantum_r], [classical_r])

for i in range(0, n_qubits):
    if i != s_0:
        circuit.h(quantum_r[i])
    else:
        circuit.x(quantum_r[i])

for i in range(0, n_qubits):
    if i != s_0:
        circuit.cx(quantum_r[i], quantum_r[s_0])

for i in range(0, n_qubits):
    circuit.h(quantum_r[i])

# for i in range(n_qubits):
#     if i < s_0:
#         circuit.iden(quantum_r[i])
#     else:
#         circuit.x(quantum_r[i])
#
# for i in range(n_qubits):
#     if i < s_0:
#         circuit.x(quantum_r[i])
#     else:
#         circuit.iden(quantum_r[i])

for i in range(0, n_qubits):
    circuit.measure(quantum_r[i], classical_r[i])

QASM_source = Q_program.get_qasm("re-mapper")

logger.info('launch_exp() - QASM:\n%s', str(QASM_source))

result = Q_program.execute(["re-mapper"], backend=device, wait=2, timeout=5000, shots=8192, max_credits=10, coupling_map=coupling_map_qx5)

QASM_source = Q_program.get_qasm("re-mapper")

print(result.get_ran_qasm('re-mapper'))

print(result)

counts = result.get_counts("re-mapper")

logger.debug('launch_exp() - counts:\n%s', str(counts))

sorted_c = sorted(counts.items(), key=operator.itemgetter(1), reverse=True)

out_f = open('re-mapper_' + device + '_' + str(8192) + '_' + str(n_qubits) + '_qubits_envariance.txt', 'w')

# store counts in txt file and xlsx file
out_f.write('VALUES\t\tCOUNTS\n\n')
for i in sorted_c:
    out_f.write(i[0] + '\t' + str(i[1]) + '\n')

out_f.close()
