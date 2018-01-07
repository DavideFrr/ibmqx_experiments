"""

Author: Davide Ferrari
August 2017

"""

import logging
import operator

import myLogger
import os
import math

logger = logging.getLogger('fidelity')
logger.addHandler(myLogger.MyHandler())
logger.setLevel(logging.INFO)
logger.propagate = False

device = 'ibmqx4'

qubits = [
    2,
    3,
    5,
    7,
    9,
    12,
    14,
    16
]

n_shots = 8192

executions = 10

directory = 'Data_Envariance/' + device + '/'

logger.info('Started')

for n_qubits in qubits:
    writef = filename = directory + device + '_' + str(n_shots) + '_' + str(n_qubits) + '_qubits_envariance_values_base2.txt'
    os.makedirs(os.path.dirname(writef), exist_ok=True)
    write_f = open(writef, 'a')
    write_f.write('Value\t\t\t\t\t\tProbability\t\tEx1\t\tEx2\t\tEx3\t\tEx4\t\tEx5\t\tEx6\t\tEx7\t\tEx8\t\tEx9\t\tEx10\n\n')
    values = dict()
    for execution in range(1, executions + 1, 1):
        readf = directory + '/' + 'execution' + str(execution) + '/' + device + '_' + str(
            n_shots) + '_' + str(n_qubits) + '_qubits_envariance.txt'
        os.makedirs(os.path.dirname(readf), exist_ok=True)
        read_f = open(readf, 'r')
        lines = read_f.read().splitlines()
        for line in range(2, len(lines), 1):
            result = lines[line].split('\t')
            value = result[0]
            counts = int(result[1])
            if value not in values:
                values.update({value: [0]})
            values[value][0] += (counts/n_shots)
            logger.debug('Values[%s]: %s' % (str(value), str(values[value])))
            values[value].append(counts/n_shots)
            logger.debug('Values[%s]: %s' % (str(value), str(values[value])))
        read_f.close()
    for value in values:
        values[value][0] /= executions
    # logger.info('Values: %s' % str(values))
    values = sorted(values.items(), key=operator.itemgetter(1), reverse=True)
    for value in values:
        write_f.write('%16s\t\t' % str(value[0]))
        for counts in range(len(value[1])):
            write_f.write('\t%1.4f' % value[1][counts])
            if counts == 0:
               write_f.write('\t\t')
        write_f.write('\n')
    write_f.close()
