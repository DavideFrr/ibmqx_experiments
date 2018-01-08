# Copyright 2017 Quantum Information Science, University of Parma, Italy. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =============================================================================

__author__ = "Davide Ferrari"
__copyright__ = "Copyright 2017, Quantum Information Science, University of Parma, Italy"
__license__ = "Apache"
__version__ = "2.0"
__email__ = "davide.ferrari8@studenti.unipr.it"

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
    writef = filename = directory + device + '_' + str(n_shots) + '_' + str(n_qubits) + '_qubits_envariance_hits_base10.txt'
    os.makedirs(os.path.dirname(writef), exist_ok=True)
    write_f = open(writef, 'a')
    write_f.write('Value\t\tProbability\n\n')
    readf = directory + device + '_' + str(
        n_shots) + '_' + str(n_qubits) + '_qubits_envariance_values_base2.txt'
    os.makedirs(os.path.dirname(readf), exist_ok=True)
    read_f = open(readf, 'r')
    lines = read_f.read().splitlines()
    for line in range(2, len(lines), 1):
        result = lines[line].split('\t')
        logger.log(logging.VERBOSE, result)
        value = int(result[0][1:], 2)
        count = result[3]
        write_f.write('%5d\t\t\t%5s\n' % (value, count))
    write_f.close()
