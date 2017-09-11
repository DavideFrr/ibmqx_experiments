"""

Author: Davide Ferrari
August 2017

This is to test the auto re-mapping functionality of QISKit
"""

import sys

sys.path.append(  # solve the relative dependencies if you clone QISKit from the Git repo and use like a global.
    "D:/PyCharm/qiskit-sdk-py")

from qiskit import QuantumProgram
import Qconfig
import operator

coupling_map_16 = {
    0: [1],
    1: [2], 2: [3],
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

Q_SPECS = {
    "circuits": [{
        "name": "Circuit",
        "quantum_registers": [{
            "name": "qr",
            "size": 16
        }],
        "classical_registers": [{
            "name": "cr",
            "size": 16
        }]}],
}

Q_program = QuantumProgram(specs=Q_SPECS)

# Get the components.

# get the circuit by Name
circuit = Q_program.get_circuit("Circuit")

# get the Quantum Register by Name
quantum_r = Q_program.get_quantum_register("qr")

# get the Classical Register by Name
classical_r = Q_program.get_classical_register('cr')

size = 3

for i in range(size):
    if i != 0:
        circuit.h(quantum_r[i])
    else:
        circuit.x(quantum_r[i])

for i in range(size):
    if i != 0:
        circuit.cx(quantum_r[i], quantum_r[0])

for i in range(size):
    circuit.h(quantum_r[i])

# for i in range(9):
#     if i < 5:
#         circuit.x(quantum_r[i])
#     else:
#         circuit.iden(quantum_r[i])
#
# for i in range(9):
#     if i < 5:
#         circuit.iden(quantum_r[i])
#     else:
#         circuit.x(quantum_r[i])

for i in range(size):
    circuit.measure(quantum_r[i], classical_r[i])

QASM_source = Q_program.get_qasm("Circuit")

print(QASM_source)

circuits = ["Circuit"]  # Group of circuits to execute

Q_program.set_api(Qconfig.APItoken, Qconfig.config["url"])  # set the APIToken and API url

result = Q_program.execute(circuits, 'ibmqx_qasm_simulator', wait=2, timeout=480, shots=1024, max_credits=10, coupling_map=coupling_map_16, silent=False)

counts = result.get_counts("Circuit")

print(counts)

sorted_c = sorted(counts.items(), key=operator.itemgetter(1), reverse=True)

out_f = open('re-mapper_ibmqx3' + '_' + str(8192) + '_' + str(size) + '_qubits_envariance.txt', 'w')

# store counts in txt file and xlsx file
out_f.write('VALUES\t\tCOUNTS\n\n')
for i in sorted_c:
    out_f.write(i[0] + '\t' + str(i[1]) + '\n')

# out_f.write('\nCOUNTS\n\n')
# for i in sorted_c:
#     out_f.write(str(i[1]) + '\n')

out_f.close()
