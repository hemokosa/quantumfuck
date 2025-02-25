from qulacs import QuantumCircuit, QuantumState, Observable
from qulacs.gate import Measurement, DepolarizingNoise
from qulacsvis import circuit_drawer

import numpy as np
import random
import re
import exrex

class QF:
    def __init__(self, num_qubits, regex=False, debug=True, init=None):
        # Initialize a quantum state with the given number of qubits.
        self.state = QuantumState(num_qubits)
        if init is None:
            # If no initial state is provided, set the state to |0...0⟩.
            self.state.set_zero_state()
        elif isinstance(init, str):
            # If the initial state is provided as a binary string,
            # initialize the state vector accordingly.
            state_vector = np.zeros(2**num_qubits)
            index = int(init, 2)
            state_vector[index] = 1.0
            self.state.load(state_vector)
        else:
            # Otherwise, load the provided state.
            self.state.load(init)

        self.pointer = 0  # Acts as a pointer to the current qubit.
        self.num_qubits = num_qubits
        self.regex = regex  # If True, generate a random command sequence using a regex.
        self.debug = debug  # If True, enable debug logging.

        # Create a temporary circuit and a circuit to store the entire history.
        self.circuit = QuantumCircuit(num_qubits)
        self.circuit_all = QuantumCircuit(num_qubits)

        # Initialize lists to keep track of state and command histories.
        self.state_history = []
        self.command_history = []

    def log(self, message):
        # Print debug messages if debug mode is enabled.
        if self.debug:
            print(message)

    def parse(self, code0):
        """
        Parse and execute a sequence of quantum commands.
        The commands control pointer movement, quantum gate application,
        measurement, and state manipulation.
        """

        # If regex mode is enabled, generate a random command sequence matching the regex.
        if self.regex:
            code = exrex.getone(code0)
            self.log(f"Code: {code}")
        else:
            code = code0

        loop_stack = []  # Stack to handle loops (for '[' and ']')
        i = 0  # Index for the current command in the code string.
        h = 0  # Counter for recording state history.

        while i < len(code):
            command = code[i]
            self.log(f"{i, h}: Command: {command}, Pointer: {self.pointer}")

            if command == '>':
                # Move pointer to the right (wrap around using modulo).
                self.pointer = (self.pointer + 1) % self.num_qubits
            elif command == '<':
                # Move pointer to the left (wrap around using modulo).
                self.pointer = (self.pointer - 1) % self.num_qubits
            elif command == '[':
                # Mark the beginning of a loop by pushing the index onto the stack.
                loop_stack.append(i)
            elif command == ']':
                # At the end of a loop, perform a measurement.
                # If measurement returns 0, exit the loop; otherwise, repeat.
                if self.measure() == 0:
                    loop_stack.pop()
                else:
                    i = loop_stack[-1]
            elif command == ';':
                # Set the quantum state to a random Haar state.
                self.state.set_Haar_random_state()
            elif command == ',':
                # Reset the quantum state to the zero state.
                self.state.set_zero_state()
            elif command == ':':
                # Perform a measurement on the current qubit.
                self.measure()
            elif command in ['.', 'M']:
                # Add a measurement gate on the current qubit.
                self.circuit.add_gate(Measurement(self.pointer, self.pointer))
            elif command in ['+', 'H']:
                # Add a Hadamard gate on the current qubit.
                self.circuit.add_H_gate(self.pointer)
            elif command in ['~', 'T']:
                # Add a T gate (π/8 phase gate) on the current qubit.
                self.circuit.add_T_gate(self.pointer)
            elif command in ['@', 'C']:
                # Add a CNOT gate.
                # The target qubit is determined by parsing a number after the command.
                match = re.match(r"\d+", code[i+1:])
                if match:
                    target_bit = (self.pointer + int(match.group(0))) % self.num_qubits
                    i += len(match.group(0))  # Skip the number in the command string.
                else:
                    target_bit = (self.pointer + 1) % self.num_qubits
                self.circuit.add_CNOT_gate(self.pointer, target_bit)
            elif command in ['#', 'N']:
                # Add a depolarizing noise gate with a fixed probability (0.1).
                prob = 0.1
                self.circuit.add_gate(DepolarizingNoise(self.pointer, prob))
            elif command == '?':
                # Randomly choose to apply either a Hadamard or a T gate.
                if random.choice([True, False]):
                    self.circuit.add_H_gate(self.pointer)
                else:
                    self.circuit.add_T_gate(self.pointer)
            elif command == '!':
                # Set the pointer to a random qubit index.
                self.pointer = random.randint(0, self.num_qubits - 1)
            elif command == '*':
                # Jump to a random command in the code.
                i = random.randint(0, len(code) - 1)
            else:
                # If the command is unrecognized, log a message and skip it.
                self.log(f"Invalid command: {command}, skipping...")
                i += 1
                continue

            # Record the executed command.
            self.command_history.append(command)

            # For commands that modify the quantum state via gates,
            # update the circuit and record the state history.
            if command in ['+', 'H', '~', 'T', '@', 'C', '.', 'M', '#', 'N', '?']:
                self.circuit.update_quantum_state(self.state)
                self.circuit_all.merge_circuit(self.circuit)
                self.circuit = QuantumCircuit(self.num_qubits)
                self.state_history.append(self.state.copy())  # Save a copy of the current state.
                h += 1

            i += 1  # Move to the next command.

        self.log("Quantum Circuit Execution Completed")
        if self.debug:
            # Visualize the entire quantum circuit if debug mode is enabled.
            circuit_drawer(self.circuit_all)

        # Return the final quantum state, state history, command history, and complete circuit.
        return self.state, self.state_history, self.command_history, self.circuit_all

    def measure(self):
        """
        Perform a measurement on the current qubit.
        This function creates an observable corresponding to the Pauli-Z operator on the current qubit,
        calculates the expectation value, converts it to a probability, and then simulates a measurement outcome.
        """
        # Create an observable for a single qubit using the Pauli-Z operator.
        single_qubit_observable = Observable(self.num_qubits)
        single_qubit_observable.add_operator(1.0, f"Z {self.pointer}")
        
        # Calculate the expectation value ⟨Z⟩ of the current state.
        e = single_qubit_observable.get_expectation_value(self.state)
        # Convert the expectation value to a probability for measuring 0.
        prob = (1.0 - e) * 0.5
        # Simulate the measurement: return 0 with probability 'prob', otherwise return 1.
        result = 0 if prob > np.random.rand() else 1
        self.log(f"Expected Value : {prob}")
        self.log(f"Measured Result: {result}")
        return result
        
