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

import myLogger
import os
import math

logger = logging.getLogger('fidelity')
logger.addHandler(myLogger.MyHandler())
logger.setLevel(logging.INFO)
logger.propagate = False

device = 'ibmqx5'

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
    writef = filename = directory + device + '_' + str(n_shots) + '_' + str(n_qubits) + '_qubits_envariance_fidelity.txt'
    os.makedirs(os.path.dirname(writef), exist_ok=True)
    write_f = open(writef, 'a')
    write_f.write('Exec\t\tFidelity\n\n')
    for execution in range(1, executions + 1, 1):
        fidelity = 0
        readf = directory + '/' + 'execution' + str(execution) + '/' + device + '_' + str(
            n_shots) + '_' + str(n_qubits) + '_qubits_envariance.txt'
        os.makedirs(os.path.dirname(readf), exist_ok=True)
        read_f = open(readf, 'r')
        lines = read_f.read().splitlines()
        zeroes = ''
        ones = ''
        for i in range(n_qubits):
            zeroes += '0'
            ones += '1'
        for line in range(2, len(lines), 1):
            result = lines[line].split('\t')
            value = result[0]
            counts = int(result[1])
            if value == ones or value == zeroes:
                fidelity += math.sqrt(counts/(2 * n_shots))
        read_f.close()
        logger.debug(fidelity)
        write_f.write('%2d %1.20f\n' % (execution, fidelity))
write_f.close()
