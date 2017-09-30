"""

Author: Davide Ferrari
August 2017

"""
import sys

sys.path.append(  # solve the relative dependencies if you clone QISKit from the Git repo and use like a global.
    "D:/PyCharm/qiskit-sdk-py")

from qiskit import QuantumProgram
import Qconfig
import operator
import math
from utility import Utility

coupling_map_5 = {
    0: [],
    1: [0],
    2: [0, 1, 4],
    3: [2, 4],
    4: [],
}

coupling_map_16 = {
    0: [],
    1: [2],
    2: [3, 15],
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
    15: [0, 14],
}

# # Number of qubits to be used
n_qubits = 5

Q_program = QuantumProgram()

Q_program.set_api(Qconfig.APItoken, Qconfig.config["url"])  # set the APIToken and API url

quantum_r = Q_program.create_quantum_register("qr", n_qubits)

classical_r = Q_program.create_classical_register("cr", n_qubits)

circuit = Q_program.create_circuit("envariance", [quantum_r], [classical_r])

utility = Utility(coupling_map_5)

utility.envariance(circuit=circuit, quantum_r=quantum_r, classicla_r=classical_r, n_qubits=n_qubits)

QASM_source = Q_program.get_qasm("envariance")

print(QASM_source)

result = Q_program.execute(["envariance"], backend='ibmqx4', wait=2, timeout=480, shots=1024, max_credits=10, silent=False)

counts = result.get_counts("envariance")

print(counts)

sorted_c = sorted(counts.items(), key=operator.itemgetter(1), reverse=True)

out_f = open('inverse-cnot_ibmqx4_' + str(1024) + '_' + str(n_qubits) + '.txt', 'w')

# store counts in txt file and xlsx file
out_f.write('VALUES\t\tCOUNTS\n\n')

# store counts in txt file
for i in sorted_c:
    out_f.write(i[0] + '\t' + str(i[1]) + '\n')

out_f.close()


# print(ordered_q)
# stop = math.floor((n_qubits)/2)
#
# ordered_q = []
# results = dict()
#
# for i in sorted_c:
#     reverse = i[0][::-1]
#     # print(reverse)
#     sorted_v = [reverse[ordered_q[0]]]
#     # print(ordered_q[0])
#     # print(sorted_v)
#     for n in range(stop):
#         sorted_v.append(reverse[ordered_q[n+1]])
#         # print(str(ordered_q[n+1]) + sorted_v[n+1] + '\n')
#         sorted_v.append(reverse[ordered_q[n+stop+1]])
#         # print(str(ordered_q[n+stop+1]) + sorted_v[n+2] + '\n')
#     value = ''.join(str(v) for v in sorted_v)
#     results.update({value: i[1]})
#     out_f.write(value + '\t' + str(i[1]) + '\n')
#
# out_f.close()
