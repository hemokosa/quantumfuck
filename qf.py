from qulacs import QuantumCircuit, QuantumState, Observable
from qulacs.gate import Measurement, DepolarizingNoise
from qulacsvis import circuit_drawer

import numpy as np
import random
import re
import exrex

class QF:
    def __init__(self, num_qubits, regex=False, debug=True, init=None):
        """Initialize the quantum system with the given number of qubits."""
        self.state = QuantumState(num_qubits)

        if init is None:
            self.state.set_zero_state()  # Set the quantum state to |0⟩^num_qubits
        elif isinstance(init, str):
            # Initialize with a binary string representation of the quantum state
            state_vector = np.zeros(2**num_qubits)
            index = int(init, 2)
            state_vector[index] = 1.0
            self.state.load(state_vector)
        else:
            self.state.load(init)  # Load a predefined state

        self.pointer = 0  # Current qubit index (acting as a data pointer)
        self.num_qubits = num_qubits
        self.regex = regex  # Whether to generate commands from a regex pattern
        self.debug = debug  # Debug mode

        self.circuit = QuantumCircuit(num_qubits)  # Temporary circuit
        self.circuit_all = QuantumCircuit(num_qubits)  # Full execution history

        # Keep track of quantum state history and command execution history
        self.state_history = []
        self.command_history = []

    def log(self, message):
        """Print debug messages if debug mode is enabled."""
        if self.debug:
            print(message)

    def parse(self, code0):
        """Parse and execute a sequence of quantum commands."""

        # Generate a random command sequence if regex mode is enabled
        if self.regex:
            code = exrex.getone(code0)
            self.log(f"Code: {code}")
        else:
            code = code0

        loop_stack = []  # Stack to handle loop control
        i = 0  # Command index
        h = 0  # History counter

        while i < len(code):
            command = code[i]
            self.log(f"{i, h}: Command: {command}, Pointer: {self.pointer}")

            if command == '>':
                self.pointer = (self.pointer + 1) % self.num_qubits  # Move pointer right
            elif command == '<':
                self.pointer = (self.pointer - 1) % self.num_qubits  # Move pointer left
            elif command == '[':
                loop_stack.append(i)  # Mark start of loop
            elif command == ']':
                if self.measure() == 0:
                    loop_stack.pop()  # Exit loop if measurement is 0
                else:
                    i = loop_stack[-1]  # Jump back to start of loop
            elif command == ';':
                self.state.set_Haar_random_state()  # Set a random quantum state
            elif command == ',':
                self.state.set_zero_state()  # Reset to |0⟩^num_qubits
            elif command == ':':
                self.measure()  # Perform measurement
            elif command in ['.', 'M']:
                self.circuit.add_gate(Measurement(self.pointer, self.pointer))  # Add measurement gate
            elif command in ['+', 'H']:
                self.circuit.add_H_gate(self.pointer)  # Apply Hadamard gate
            elif command in ['~', 'T']:
                self.circuit.add_T_gate(self.pointer)  # Apply T gate (π/8 phase gate)
            elif command in ['@', 'C']:
                # Parse a target qubit for CNOT
                match = re.match(r"\d+", code[i+1:])
                if match:
                    target_bit = (self.pointer + int(match.group(0))) % self.num_qubits
                    i += len(match.group(0))  # Skip over parsed number
                else:
                    target_bit = (self.pointer + 1) % self.num_qubits  # Default to next qubit
                self.circuit.add_CNOT_gate(self.pointer, target_bit)  # Apply CNOT gate
            elif command in ['#', 'N']:
                self.circuit.add_gate(DepolarizingNoise(self.pointer, 0.1))  # Add noise gate (10% depolarization)
            elif command == '?':
                # Apply a Hadamard or T gate randomly
                if random.choice([True, False]):
                    self.circuit.add_H_gate(self.pointer)
                else:
                    self.circuit.add_T_gate(self.pointer)
            elif command == '!':
                self.pointer = random.randint(0, self.num_qubits-1)  # Move pointer to a random qubit
            elif command == '*':
                i = random.randint(0, len(code)-1)  # Jump to a random command
            else:
                # Invalid command, log and skip
                self.log(f"Invalid command: {command}, skipping...")
                i += 1
                continue

            # Store execution history
            self.command_history.append(command)
            if command in ['+', 'H', '~', 'T', '@', 'C', '.', 'M', '#', 'N', '?']:
                self.circuit.update_quantum_state(self.state)  # Update quantum state
                self.circuit_all.merge_circuit(self.circuit)  # Merge with full circuit
                self.circuit = QuantumCircuit(self.num_qubits)  # Reset temporary circuit
                self.state_history.append(self.state.copy())  # Store quantum state
                h += 1

            i += 1  # Move to next command

        self.log("Quantum Circuit Execution Completed")

        # Draw the quantum circuit if debug mode is enabled
        if self.debug:
            circuit_drawer(self.circuit_all)

        # Return the final quantum state, history of states, command history, and final circuit
        return self.state, self.state_history, self.command_history, self.circuit_all

    def measure(self):
        """Perform a measurement on the current qubit and return 0 or 1."""
        # Define an observable for measurement (Pauli Z operator)
        single_qubit_observable = Observable(self.num_qubits)
        single_qubit_observable.add_operator(1.0, f"Z {self.pointer}")

        # Compute expectation value ⟨Z⟩
        e = single_qubit_observable.get_expectation_value(self.state)
        prob = (1.0 - e) * 0.5  # Convert expectation value to probability

        # Simulate measurement outcome (probabilistic)
        result = 0 if prob > np.random.rand() else 1
        self.log(f"Expected Value : {prob}")
        self.log(f"Measured Result: {result}")
        return result
