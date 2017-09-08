import sys

sys.path.append(  # solve the relative dependencies if you clone QISKit from the Git repo and use like a global.
    "D:/PyCharm/qiskit-sdk-py")

from qiskit import QuantumProgram
import Qconfig
from Envariance import Utility
import operator
import math
import xlsxwriter

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

real_5 = 'ibmqx2'

real_16 = 'ibmqx3'

online_sim = 'ibmqx_qasm_simulator'

local_sim = 'local_qasm_simulator'

n_qubits = 5

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
quantum_r = Q_program.get_quantum_registers("qr")

# get the Classical Register by Name
classical_r = Q_program.get_classical_registers('cr')

utility = Utility(coupling_map_16)

# create circuit needed for the envariance experiment
# utility.envariance(circuit, quantum_r, classical_r, n_qubits)

utility.oracle(circuit, quantum_r, classical_r, n_qubits)

QASM_source = Q_program.get_qasm("Circuit")

print(QASM_source)

circuits = ["Circuit"]  # Group of circuits to execute

Q_program.set_api(Qconfig.APItoken, Qconfig.config["url"])  # set the APIToken and API url

Q_program.execute(circuits, online_sim, wait=2, timeout=480, shots=1024, max_credits=10)

counts = Q_program.get_counts("Circuit")

print(counts)

utility.close()
