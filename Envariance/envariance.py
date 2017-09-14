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
import xlsxwriter

# The coupling-map
# coupling_map = {
#
# }

# Back-end devices
real_5 = 'ibmqx2'

real_16 = 'ibmqx3'

online_sim = 'ibmqx_qasm_simulator'


# launch envariance experiment on the given device
def launch_exp(workbook, device, utility, n_qubits, num_shots=1024):
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
    quantum_r = Q_program.get_quantum_register("qr")

    # get the Classical Register by Name
    classical_r = Q_program.get_classical_register('cr')

    # crete circuit needed for the envariance experiment
    utility.create(circuit, quantum_r, classical_r, n_qubits)

    QASM_source = Q_program.get_qasm("Circuit")

    print(QASM_source)

    circuits = ["Circuit"]  # Group of circuits to execute

    Q_program.set_api(Qconfig.APItoken, Qconfig.config["url"])  # set the APIToken and API url

    result = Q_program.execute(circuits, device, wait=2, timeout=480, shots=num_shots, max_credits=10, silent=False)

    counts = result.get_counts("Circuit")

    sorted_c = sorted(counts.items(), key=operator.itemgetter(1), reverse=True)

    out_f = open('Data_Envariance/' + device + '_' + str(num_shots) + '_' + str(n_qubits) + '_qubits_envariance.txt', 'w')

    # store counts in txt file and xlsx file
    out_f.write('VALUES\t\tCOUNTS\n\n')
    for i in sorted_c:
        out_f.write(i[0] + '\t' + str(i[1]) + '\n')

    # out_f.write('\nCOUNTS\n\n')
    # for i in sorted_c:
    #     out_f.write(str(i[1]) + '\n')

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
            fidelity += math.sqrt(int(i[1])/(2*num_shots))
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

#
# Uncomment and fill in the missing data, refer to example.py if you have doubts

# workbook = xlsxwriter.Workbook('Data_Envariance/your_file.xlsx')
# utility = Utility('coupling_map')
# launch_exp(workbook, 'back-end devie', utility, n_qubits=, num_shots=)
# utility.close()
# workbook.close()

print('\nAll done.\n')
