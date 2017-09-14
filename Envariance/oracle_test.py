import sys

sys.path.append(  # solve the relative dependencies if you clone QISKit from the Git repo and use like a global.
    "D:/PyCharm/qiskit-sdk-py")

from qiskit import QuantumProgram
import Qconfig
from Envariance import Utility
import operator
import math
import xlsxwriter
import time

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

# Back-end devices
real_5 = 'ibmqx2'

real_16 = 'ibmqx3'

online_sim = 'ibmqx_qasm_simulator'

local_sim = 'local_qasm_simulator'


# launch envariance experiment on the given device
def launch_exp(workbook, device, utility, n_qubits, k='11', num_shots=1024):
    size = 0

    ordered_q = []

    results = dict()

    if device == real_5:
        if n_qubits <= 5:
            size = 5
            # device = 'ibmqx_qasm_simulator'
        else:
            print('Too much qubits for' + device + '!')
            exit(1)
    elif device == real_16:
        if n_qubits <= 16:
            size = 16
            # device = 'ibmqx_qasm_simulator'
        else:
            print('Too much qubits for' + device + '!')
            exit(2)
    elif device == online_sim:
        if n_qubits <= 5:
            size = 5
        if n_qubits <= 16:
            size = 16
    else:
        print('Unknown device.')
        exit(3)

    Q_SPECS = {
        "circuits": [{
            "name": "Circuit",
            "quantum_registers": [{
                "name": "qr",
                "size": size
            }],
            "classical_registers": [{
                "name": "cr",
                "size": size
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

    # create circuit needed for the envariance experiment
    utility.oracle(circuit, quantum_r, classical_r, n_qubits, k=k, connected=ordered_q)

    QASM_source = Q_program.get_qasm("Circuit")

    print(QASM_source)

    circuits = ["Circuit"]  # Group of circuits to execute

    Q_program.set_api(Qconfig.APItoken, Qconfig.config["url"])  # set the APIToken and API url

    result = Q_program.execute(circuits, device, wait=2, timeout=480, shots=num_shots, max_credits=10, silent=False)

    counts = result.get_counts("Circuit")

    sorted_c = sorted(counts.items(), key=operator.itemgetter(1), reverse=True)

    out_f = open('Data_Oracle/' + device + '_' + str(num_shots) + 'queries_' + str(n_qubits) + 'qubits_' + k + '_oracle.txt', 'w')

    # store counts in txt file and xlsx file
    out_f.write('VALUES\t\tCOUNTS\n\n')
    # print(ordered_q)
    stop = math.floor((n_qubits)/2)
    for i in sorted_c:
        reverse = i[0][::-1]
        # print(reverse)
        sorted_v = [reverse[ordered_q[0]]]
        # print(ordered_q[0])
        # print(sorted_v)
        for n in range(stop):
            sorted_v.append(reverse[ordered_q[n+1]])
            # print(str(ordered_q[n+1]) + sorted_v[n+1] + '\n')
            sorted_v.append(reverse[ordered_q[n+stop+1]])
            # print(str(ordered_q[n+stop+1]) + sorted_v[n+2] + '\n')
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
        if i != zero:
            worksheet.write(row, col, i, binary)
            worksheet.write(row, col + 1, results[i])
            worksheet.write(row, col + 2, results[i] / num_shots)
            total += results[i]
            if i == one_zero and k == '00':
                correct = results[i]
            if i == one and k == '11':
                correct = results[i]
            if i == one_one_zero and k == '10':
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

# launch_exp takes the argument device which can either be real_5, real_16, online_sim or local_sim
# k is the srting you wont to learn: '10' for '10...10', '11' for '11...11', '00' for '00...00'

utility = Utility(coupling_map_16)
for k in oracles:
    workbook = xlsxwriter.Workbook('Data_Oracle/ibmqx3_n_qubits_' + k + '_oracle.xlsx')
    for n_shots in range(10, 210, 10):
        launch_exp(workbook, online_sim, utility, n_qubits=7, k=k, num_shots=n_shots)
        time.sleep(2)
        launch_exp(workbook, online_sim, utility, n_qubits=9, k=k, num_shots=n_shots)
        time.sleep(2)
    workbook.close()

utility.close()

print('\nAll done.\n')
