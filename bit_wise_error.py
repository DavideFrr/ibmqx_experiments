"""

Author: Davide Ferrari
August 2017

"""

import logging

import myLogger
import os
import random

logger = logging.getLogger('new_error')
logger.addHandler(myLogger.MyHandler())
logger.setLevel(logging.INFO)
logger.propagate = False

# device is the device the experiment was run on
# executions is the number of different experiment you ran
# queries is the maximum number of queries
# n_qubits the number of qubits of the experiments
# oracles are the strings you want to learn: '10' for '10...10', '11' for '11...11', '00' for '00...00'

device = 'ibmqx5'

oracles = [
    '00',
    '10',
    '11'
]

n_qubits = 16

queries = 50

executions = 50

directory = 'Data_Parity/' + device + '/'

logger.info('Started')

for oracle in oracles:
    a = ''
    for n in range(n_qubits-1):
        if oracle == '00':
            a += '0'
        elif oracle == '11':
            a += '1'
        elif oracle == '10':
            if n % 2 == 0:
                a += '1'
            else:
                a += '0'
    writef = filename = directory + oracle + '/' + device + '_' + oracle + '_' + str(n_qubits) + '_qubits_parity_bit-wise_error_v2.txt'
    os.makedirs(os.path.dirname(writef), exist_ok=True)
    write_f = open(writef, 'a')
    write_f.write('N\t\tError\n\n')
    for n_queries in range(5, queries+5, 5):
        correct = 0
        success_rate = 0
        for execution in range(1, executions+1, 1):
            x = ''
            total = 0
            readf = directory + oracle + '/' + 'execution' + str(execution) + '/' + device + '_' + str(
                n_queries) + 'queries_' + str(oracle) + '_' + str(n_qubits) + '_qubits_parity.txt'
            os.makedirs(os.path.dirname(readf), exist_ok=True)
            read_f = open(readf, 'r')
            lines = read_f.read().splitlines()
            zeroes = [0 for i in range(n_qubits-1)]
            ones = [0 for i in range(n_qubits-1)]
            for line in range(2, len(lines), 1):
                result = lines[line].split('\t')
                k = result[0]
                counts = int(result[1])

                if k[0] != '0':
                    total += counts
                    for n in range(n_qubits-1):
                        if k[n+1] == '0':
                            zeroes[n] += counts
                        else:
                            ones[n] += counts
            for n in range(len(zeroes)):
                if zeroes[n] > ones[n]:
                    x += '0'
                elif ones[n] > zeroes[n]:
                    x += '1'
                elif zeroes[n] == ones[n]:
                    x += str(random.randint(0, 1))
                    # if a[n] == '1':
                    #     x += '1'
                    # else:
                    #     x += '0'
            if x == a:
                correct += 1
            logger.log(logging.VERBOSE, x)
            read_f.close()
        logger.debug(correct)
        success_rate += correct/executions
        write_f.write('%4d %1.20f\n' % (n_queries, 1 - success_rate))
    write_f.close()
