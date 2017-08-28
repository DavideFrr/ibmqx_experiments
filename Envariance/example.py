"""

Author: Davide Ferrari
August 2017

"""
import sys

sys.path.append(  # solve the relative dependencies if you clone QISKit from the Git repo and use like a global.
    "D:/PyCharm/qiskit-sdk-py")

from qiskit import QuantumProgram
import Qconfig
from Envariance import Utility
import operator
import math
import time
import xlsxwriter

coupling_map_5 = {
    0: [1, 2],
    1: [2],
    2: [],
    3: [2, 4],
    4: [2],
}

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


# lunch envariance experiment on the given device
def lunch_exp(workbook, device, utility, n_qubits, num_shots=1024):
    size = 0

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
    quantum_r = Q_program.get_quantum_registers("qr")

    # get the Classical Register by Name
    classical_r = Q_program.get_classical_registers('cr')

    # crete circuit needed for the envariance experiment
    utility.create(circuit, quantum_r, classical_r, n_qubits)

    QASM_source = Q_program.get_qasm("Circuit")

    print(QASM_source)

    circuits = ["Circuit"]  # Group of circuits to execute

    Q_program.set_api(Qconfig.APItoken, Qconfig.config["url"])  # set the APIToken and API url

    Q_program.execute(circuits, device, wait=2, timeout=480, shots=num_shots, max_credits=10)

    counts = Q_program.get_counts("Circuit")

    sorted_c = sorted(counts.items(), key=operator.itemgetter(1), reverse=True)

    out_f = open(device + '_' + str(num_shots) + '_' + str(n_qubits) + '_qubits_envariance.txt', 'w')

    # store counts in txt file and xlsx file
    out_f.write('VALUES\n\n')
    for i in sorted_c:
        out_f.write(i[0] + '\n')

    out_f.write('\nCOUNTS\n\n')
    for i in sorted_c:
        out_f.write(str(i[1]) + '\n')

    out_f.close()

    num_rows = len(sorted_c)
    sheet = str(num_shots) + '_' + str(n_qubits)

    worksheet = workbook.add_worksheet(sheet)
    bold = workbook.add_format({'bold': True})
    binary = workbook.add_format()
    binary.set_num_format_index('00000')

    worksheet.write(0, 0, 'Values', bold)
    worksheet.write(0, 1, 'Counts', bold)
    worksheet.write(0, 2, 'Probability', bold)
    worksheet.write(0, 3, 'Fidelity', bold)
    row = 1
    col = 0
    fidelity = 0
    for i in sorted_c:
        worksheet.write(row, col, i[0], binary)
        worksheet.write(row, col + 1, int(i[1]))
        worksheet.write(row, col + 2, int(i[1]) / num_shots)
        if row == 1 or row == 2:
            fidelity += math.sqrt(int(i[1]) / (2 * num_shots))
        row += 1
    worksheet.write(row, col + 1, '=SUM(B2:B' + str(row) + ')')
    worksheet.write(1, 3, fidelity)

    chart = workbook.add_chart({'type': 'column'})
    categories = '=' + sheet + '!$A$2:$A$' + str(num_rows + 1)
    values = '=' + sheet + '!$C$2:$C$' + str(num_rows + 1)
    chart.add_series({
        'categories': categories,
        'values': values,
        'data_labels': {
            'value': False,
            'series_name': False,
            'num_format': '0.#0',
            'font': {'bold': True},
        },
    })

    chart.set_legend({
        'none': True
    })

    chart.set_title({
        'name': sheet + '_qubits_envariance'
    })

    chart.set_x_axis({
        'num_font': {'rotation': 50},
    })

    worksheet.insert_chart('F3', chart)


shots = [
    1024,
    2048,
    8192
]

workbook5 = xlsxwriter.Workbook('ibmqx2_n_qubits_envariance.xlsx')

utility = Utility(coupling_map_5)
for n_shots in shots:
    lunch_exp(workbook5, real_5, utility, n_qubits=2, num_shots=n_shots)
    time.sleep(2)
    lunch_exp(workbook5, real_5, utility, n_qubits=3, num_shots=n_shots)
    time.sleep(2)
    lunch_exp(workbook5, real_5, utility, n_qubits=5, num_shots=n_shots)
    time.sleep(2)

utility.close()

workbook5.close()

workbook16 = xlsxwriter.Workbook('Data/ibmqx3_n_qubits_envariance.xlsx')

utility = Utility(coupling_map_16)
for n_shots in shots:
    lunch_exp(workbook16, real_16, utility, n_qubits=2, num_shots=n_shots)
    time.sleep(2)
    lunch_exp(workbook16, real_16, utility, n_qubits=3, num_shots=n_shots)
    time.sleep(2)
    lunch_exp(workbook16, real_16, utility, n_qubits=5, num_shots=n_shots)
    time.sleep(2)
    lunch_exp(workbook16, real_16, utility, n_qubits=7, num_shots=n_shots)
    time.sleep(2)
    lunch_exp(workbook16, real_16, utility, n_qubits=9, num_shots=n_shots)
    time.sleep(2)

utility.close()

workbook16.close()

print('\nAll done.\n')
