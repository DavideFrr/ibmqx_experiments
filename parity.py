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

from utility import *
from backends import *
import coupling_maps

logger = logging.getLogger('parity')
logger.addHandler(myLogger.MyHandler())
logger.setLevel(logging.INFO)
logger.propagate = False


# device is the device you want to run the experiment on
# executions is the number of different experiment you want to run
# n_shots is the maximum number of n_shots
# oracles are the strings you want to learn: '10' for '10...10', '11' for '11...11', '00' for '00...00'
device = qx5

executions = 200

queries = [
    5,
    10,
    15,
    20,
    25,
    30,
    35,
    40,
    45,
    50,
    75,
    100,
    200,
    500,
]

oracles = [
    '00',
    '10',
    '11',
]

# launch_exp takes the argument device from devices module
logger.info('Started')

utility_qx5 = Utility(coupling_maps.qx5)

for execution in range(1, executions + 1, 1):

    for oracle in oracles:

        # Comment the experiments you don't want to run
        for n_queries in queries:
            logger.info('Qubits %d - Oracle %s - Execution %d - Queries %d', 3, oracle, execution, n_queries)
            parity_exec(execution, device, utility_qx5, n_qubits=3, oracle=oracle, num_shots=n_queries)
            logger.info('Qubits %d - Oracle %s - Execution %d - Queries %d', 9, oracle, execution, n_queries)
            parity_exec(execution, device, utility_qx5, n_qubits=9, oracle=oracle, num_shots=n_queries)
            logger.info('Qubits %d - Oracle %s - Execution %d - Queries %d', 16, oracle, execution, n_queries)
            parity_exec(execution, device, utility_qx5, n_qubits=16, oracle=oracle, num_shots=n_queries)

utility_qx5.close()

logger.info('All done.')
