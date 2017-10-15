"""

Author: Davide Ferrari
August 2017

"""

import logging

from os.path import expanduser

import myLogger
import os
import operator
import xlsxwriter
import xlrd
import time
import math

from utility import Utility

import sys

sys.path.append(  # solve the relative dependencies if you clone QISKit from the Git repo and use like a global.
    "D:/PyCharm/qiskit-sdk-py")

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
def launch_exp(workbook_name, device, utility, n_qubits, num_shots=1024):
    size = 0
    home = expanduser("~")

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

    circuit = Q_program.create_circuit("envariance", [quantum_r], [classical_r])

    utility.envariance(circuit=circuit, quantum_r=quantum_r, classical_r=classical_r, n_qubits=n_qubits)

    QASM_source = Q_program.get_qasm("envariance")

    logger.info('launch_exp() - QASM:\n%s', str(QASM_source))

    result = Q_program.execute(["envariance"], backend=device, wait=2, timeout=1000, shots=num_shots, max_credits=10,
                               silent=False)

    counts = result.get_counts("envariance")

    logger.debug('launch_exp() - counts:\n%s', str(counts))

    sorted_c = sorted(counts.items(), key=operator.itemgetter(1), reverse=True)

    filename = 'Data_Envariance/' + device + '/' + device + '_' + str(num_shots) + '_' + str(
        n_qubits) + '_qubits_envariance.txt'
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    out_f = open(filename, 'w')

    # store counts in txt file and xlsx file
    out_f.write('VALUES\t\tCOUNTS\n\n')
    for i in sorted_c:
        out_f.write(i[0] + '\t' + str(i[1]) + '\n')

    out_f.close()

    wbRD = xlrd.open_workbook(workbook_name.format(home))
    sheets = wbRD.sheets()

    wb = xlsxwriter.Workbook(workbook_name.format(home))

    for sheet in sheets:  # write data from old file
        newSheet = wb.add_worksheet(sheet.name)
        for row in range(sheet.nrows):
            for col in range(sheet.ncols):
                newSheet.write(row, col, sheet.cell(row, col).value)

    sheet = str(num_shots) + '_' + str(n_qubits)
    worksheet = wb.add_worksheet(sheet)
    bold = wb.add_format({'bold': True})
    binary = wb.add_format()
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
        worksheet.write(row, col + 1, i[1])
        worksheet.write(row, col + 2, i[1] / num_shots)
        if row == 1 or row == 2:
            fidelity += math.sqrt(i[1] / (2 * num_shots))
        row += 1
    worksheet.write(row, col + 1, '=SUM(B2:B' + str(row) + ')')
    worksheet.write(1, 3, fidelity)

    # Uncomment the below section if you want to add charts to the file

    # chart = wb.add_chart({'type': 'column'})
    # categories = '=' + sheet + '!$A$2:$A$' + str(num_rows + 1)
    # values = '=' + sheet + '!$C$2:$C$' + str(num_rows + 1)
    # chart.add_series({
    #     'categories': categories,
    #     'values': values,
    #     'data_labels': {
    #         'value': False,
    #         'series_name': False,
    #         'num_format': '0.#0',
    #         'font': {'bold': True},
    #     },
    # })
    #
    # chart.set_legend({
    #     'none': True
    # })
    #
    # chart.set_title({
    #     'name': sheet + '_qubits_envariance'
    # })
    #
    # chart.set_x_axis({
    #     'num_font': {'rotation': 50},
    # })
    #
    # worksheet.insert_chart('F3', chart)

    wb.close()


shots = [
    1024,
    2048,
    8192
]

# launch_exp takes the argument device which can either be qx2, qx3, qx4, qx5, online_sim or local_sim
logger.info('Started')

directory = 'Data_Envariance/'
os.makedirs(os.path.dirname(directory), exist_ok=True)

workbook5_name = directory + 'test.xlsx'

# Comment this two lines if you've already created the file in a previous execution
workbook5 = xlsxwriter.Workbook(workbook5_name)
workbook5.close()

utility = Utility(coupling_map_qx4)
for n_shots in shots:
    launch_exp(workbook5_name, online_sim, utility, n_qubits=2, num_shots=n_shots)
    time.sleep(2)
    launch_exp(workbook5_name, online_sim, utility, n_qubits=3, num_shots=n_shots)
    time.sleep(2)
    launch_exp(workbook5_name, online_sim, utility, n_qubits=5, num_shots=n_shots)
    time.sleep(2)

utility.close()

workbook16_name = directory + 'ibmqx5_n_qubits_envariance.xlsx'

# Comment this two lines if you've already created the file in a previous execution
# workbook16 = xlsxwriter.Workbook(directory + 'ibmqx5_n_qubits_envariance.xlsx')
# workbook16.close()
#
# utility = Utility(coupling_map_qx5)
# for n_shots in shots:
#     launch_exp(workbook16_name, qx5, utility, n_qubits=2, num_shots=n_shots)
#     time.sleep(2)
#     launch_exp(workbook16_name, qx5, utility, n_qubits=3, num_shots=n_shots)
#     time.sleep(2)
#     launch_exp(workbook16_name, qx5, utility, n_qubits=5, num_shots=n_shots)
#     time.sleep(2)
#     launch_exp(workbook16_name, qx5, utility, n_qubits=7, num_shots=n_shots)
#     time.sleep(2)
#     launch_exp(workbook16_name, qx5, utility, n_qubits=9, num_shots=n_shots)
#     time.sleep(2)
#     launch_exp(workbook16_name, qx5, utility, n_qubits=12, num_shots=n_shots)
#     time.sleep(2)
#     launch_exp(workbook16_name, qx5, utility, n_qubits=14, num_shots=n_shots)
#     time.sleep(2)
#     launch_exp(workbook16_name, qx5, utility, n_qubits=16, num_shots=n_shots)
#     time.sleep(2)
#
# utility.close()

logger.info('All done.')
