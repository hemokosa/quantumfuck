from quri_parts.circuit import QuantumCircuit
from quri_parts.qulacs.simulator import run_circuit
from quri_parts.circuit.utils.circuit_drawer import draw_circuit

import numpy as np
import random
import re
import exrex

class QF:
    def __init__(self, num_qubits, regex=False, debug=True, init=None):
        self.num_qubits = num_qubits

        # Initialize quantum state
        if init is None:
            # Default to |0> state
            self.state = np.zeros(2**num_qubits, dtype=complex)
            self.state[0] = 1.0
        elif isinstance(init, str):
            # Initialize based on binary string
            state_vector = np.zeros(2**num_qubits, dtype=complex)
            index = int(init, 2)
            state_vector[index] = 1.0
            self.state = state_vector
        else:
            # Initialize with a given state vector
            self.state = np.array(init, dtype=complex)

        self.pointer = 0  # Pointer for qubit selection
        self.regex = regex  # Enable regex-based command expansion
        self.debug = debug  # Enable debugging messages

        # Quantum circuit tracking
        self.circuit = QuantumCircuit(num_qubits)  # Current circuit
        self.circuit_all = QuantumCircuit(num_qubits)  # Full circuit history

        self.state_history = []  # History of quantum states
        self.command_history = []  # History of executed commands

    def log(self, message):
        # Logs a message if debugging is enabled.
        if self.debug:
            print(message)

    def set_Haar_random_state(self):
        # Generates a Haar-random quantum state.
        dim = 2**self.num_qubits
        state = np.random.randn(dim) + 1j * np.random.randn(dim)
        state = state / np.linalg.norm(state)
        self.state = state

    def set_zero_state(self):
        # Resets the state to |0>.
        self.state = np.zeros(2**self.num_qubits, dtype=complex)
        self.state[0] = 1.0

    def parse(self, code0):
        # Parses and executes a command sequence.

        # Apply regex expansion if enabled
        if self.regex:
            code = exrex.getone(code0)
            self.log(f"Code: {code}")
        else:
            code = code0

        loop_stack = []  # Stack to handle loops
        i = 0  # Command index
        h = 0  # Circuit update counter

        while i < len(code):
            command = code[i]
            self.log(f"{(i, h)}: Command: {command}, Pointer: {self.pointer}")

            if command == '>':
                # Move pointer right
                self.pointer = (self.pointer + 1) % self.num_qubits
            elif command == '<':
                # Move pointer left
                self.pointer = (self.pointer - 1) % self.num_qubits
            elif command == '[':
                # Start loop
                loop_stack.append(i)
            elif command == ']':
                # End loop; repeat if measurement result is nonzero
                if not loop_stack:
                    self.log("Error: Unmatched ']' found, skipping...")
                elif self.estimate() == 0:
                    loop_stack.pop()
                else:
                    i = loop_stack[-1]
                    continue  # Jump back to loop start
            elif command == ';':
                # Set state to Haar-random
                self.set_Haar_random_state()
            elif command == ',':
                # Reset to |0>
                self.set_zero_state()
            elif command == ':':
                # Perform state estimation
                self.estimate()
            elif command in ['+', 'H']:
                # Apply Hadamard gate
                self.circuit.add_H_gate(self.pointer)
            elif command in ['~', 'T']:
                # Apply T gate
                self.circuit.add_T_gate(self.pointer)
            elif command in ['@', 'C']:
                # Apply CNOT gate
                match = re.match(r"\d+", code[i+1:])
                if match:
                    target_bit = (self.pointer + int(match.group(0))) % self.num_qubits
                    i += len(match.group(0))
                else:
                    target_bit = (self.pointer + 1) % self.num_qubits
                self.circuit.add_CNOT_gate(self.pointer, target_bit)
            elif command == '?':
                # Apply either H or T gate randomly
                if random.choice([True, False]):
                    self.circuit.add_H_gate(self.pointer)
                else:
                    self.circuit.add_T_gate(self.pointer)
            elif command == '!':
                # Set pointer to a random qubit
                self.pointer = random.randint(0, self.num_qubits - 1)
            elif command == '*':
                # Jump to a random command index
                i = random.randint(0, len(code) - 1)
                continue
            else:
                self.log(f"Invalid command: {command}, skipping...")
                i += 1
                continue

            self.command_history.append(command)

            # If the command affects the state, update simulation
            if command in ['+', 'H', '~', 'T', '@', 'C', '?']:
                result = run_circuit(self.circuit, self.state)
                self.state = result
                # Merge current circuit into full circuit history
                self.circuit_all += self.circuit
                # Reset current circuit
                self.circuit = QuantumCircuit(self.num_qubits)
                # Save state history
                self.state_history.append(self.state)
                h += 1

            i += 1

        self.log("Quantum Circuit Execution Completed")
        draw_circuit(self.circuit_all)  # Draw the final circuit
        return self.state, self.state_history, self.command_history, self.circuit_all

    def estimate(self):
        # Estimates the probability of measuring 1 on the selected qubit.
        dim = 2**self.num_qubits
        prob = sum(np.abs(self.state[i])**2 for i in range(dim) if (i >> self.pointer) & 1)
        result = 0 if random.random() > prob else 1
        self.log(f"Measured qubit {self.pointer}: 1 with probability {prob}, result: {result}")
        return result
