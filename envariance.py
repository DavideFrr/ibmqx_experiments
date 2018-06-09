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

logger = logging.getLogger('envariance')
logger.addHandler(myLogger.MyHandler())
logger.setLevel(logging.INFO)
logger.propagate = False

executions = 10

shots = [
    1024,
    2048,
    8192
]

# launch_exp takes the argument device from devices module
logger.info('Started')

utility_qx4 = Utility(coupling_maps.qx4())
for execution in range(1, executions+1, 1):
    for n_shots in shots:
        # Comment the experiments you don't want to run
        logger.info('Qubits %d - Execution %d - Shots %d', 2, execution, n_shots)
        envariance_exec(execution, qx4, utility_qx4, n_qubits=2, num_shots=8192)
        logger.info('Qubits %d - Execution %d - Shots %d', 3, execution, n_shots)
        envariance_exec(execution, qx4, utility_qx4, n_qubits=3, num_shots=n_shots)
        logger.info('Qubits %d - Execution %d - Shots %d', 5, execution, n_shots)
        envariance_exec(execution, qx4, utility_qx4, n_qubits=5, num_shots=n_shots)

utility_qx4.close()

utility_qx5 = Utility(coupling_maps.qx5())
for execution in range(1, executions+1, 1):
    for n_shots in shots:
        # Comment the experiments you don't want to run
        logger.info('Qubits %d - Execution %d - Shots %d', 2, execution, n_shots)
        envariance_exec(execution, qx5, utility_qx5, n_qubits=2, num_shots=n_shots)
        logger.info('Qubits %d - Execution %d - Shots %d', 3, execution, n_shots)
        envariance_exec(execution, qx5, utility_qx5, n_qubits=3, num_shots=n_shots)
        logger.info('Qubits %d - Execution %d - Shots %d', 5, execution, n_shots)
        envariance_exec(execution, qx5, utility_qx5, n_qubits=5, num_shots=n_shots)
        logger.info('Qubits %d - Execution %d - Shots %d', 7, execution, n_shots)
        envariance_exec(execution, qx5, utility_qx5, n_qubits=7, num_shots=n_shots)
        logger.info('Qubits %d - Execution %d - Shots %d', 9, execution, n_shots)
        envariance_exec(execution, qx5, utility_qx5, n_qubits=9, num_shots=n_shots)
        logger.info('Qubits %d - Execution %d - Shots %d', 12, execution, n_shots)
        envariance_exec(execution, qx5, utility_qx5, n_qubits=12, num_shots=n_shots)
        logger.info('Qubits %d - Execution %d - Shots %d', 14, execution, n_shots)
        envariance_exec(execution, qx5, utility_qx5, n_qubits=14, num_shots=n_shots)
        logger.info('Qubits %d - Execution %d - Shots %d', 16, execution, n_shots)
        envariance_exec(execution, qx5, utility_qx5, n_qubits=16, num_shots=n_shots)

utility_qx5.close()

logger.info('All done.')
