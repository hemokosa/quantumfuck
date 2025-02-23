from qulacs import QuantumCircuit, QuantumState, Observable
from qulacs.gate import Measurement, DepolarizingNoise

import numpy as np
import random
import re
import exrex

class QF:
    def __init__(self, num_qubits, regex=False, debug=True, init=None):
        self.state = QuantumState(num_qubits)
        if init is None:
            self.state.set_zero_state()
        elif isinstance(init, str):
            # バイナリ表現の場合の初期化
            state_vector = np.zeros(2**num_qubits)
            index = int(init, 2)
            state_vector[index] = 1.0
            self.state.load(state_vector)
        else:
            self.state.load(init)

        self.pointer = 0
        self.num_qubits = num_qubits
        self.regex = regex
        self.debug = debug

        self.circuit = QuantumCircuit(num_qubits)
        self.circuit_all = QuantumCircuit(num_qubits)

        # 履歴を保持
        self.state_history = []
        self.command_history = []

    def log(self, message):
        if self.debug:
            print(message)

    def parse(self, code0):

        # 正規表現に一致するランダムなコードを生成
        if self.regex:
            code = exrex.getone(code0)
            self.log(f"Code: {code}")
        else:
            code = code0

        loop_stack = []
        i = 0
        h = 0
        while i < len(code):
            command = code[i]
            self.log(f"{i, h}: Command: {command}, Pointer: {self.pointer}")
            if command == '>':
                self.pointer = (self.pointer + 1) % self.num_qubits
            elif command == '<':
                self.pointer = (self.pointer - 1) % self.num_qubits
            elif command == '[':
                loop_stack.append(i)
            elif command == ']':
                if self.measure() == 0:
                    loop_stack.pop()
                else:
                    i = loop_stack[-1]
            elif command == ';':
                self.state.set_Haar_random_state()
            elif command == ',':
                self.state.set_zero_state()
            elif command == ':':
                self.measure()
            elif command in ['.', 'M']:
                self.circuit.add_gate(Measurement(self.pointer, self.pointer))
            elif command in ['+', 'H']:
                self.circuit.add_H_gate(self.pointer)
            elif command in ['~', 'T']:
                self.circuit.add_T_gate(self.pointer)
            elif command in ['@', 'C']:
                match = re.match(r"\d+", code[i+1:])
                if match:
                    target_bit = (self.pointer + int(match.group(0))) % self.num_qubits
                    i += len(match.group(0))
                else:
                    target_bit = (self.pointer + 1) % self.num_qubits
                self.circuit.add_CNOT_gate(self.pointer, target_bit)
            elif command in ['#', 'N']:
                prob = 0.1
                self.circuit.add_gate(DepolarizingNoise(self.pointer, prob))
            elif command == '?':
                if random.choice([True, False]):
                    self.circuit.add_H_gate(self.pointer)
                else:
                    self.circuit.add_T_gate(self.pointer)
            elif command == '!':
                self.pointer = random.randint(0, self.num_qubits-1)
            elif command == '*':
                i = random.randint(0, len(code)-1)
            else:
                # 無効なコマンド
                self.log(f"Invalid command: {command}, skipping...")
                i += 1
                continue

            # 状態を記録
            self.command_history.append(command)
            if command in ['+', 'H', '~', 'T', '@', 'C', '.', 'M', '#', 'N', '?']:
                self.circuit.update_quantum_state(self.state)
                self.circuit_all.merge_circuit(self.circuit)
                self.circuit = QuantumCircuit(self.num_qubits)
                self.state_history.append(self.state.copy())  # 状態をコピーして記録
                h += 1

            i += 1

        self.log("Quantum Circuit Execution Completed")
        if self.debug:
            circuit_drawer(self.circuit_all)

        # state: 最終的な量子状態
        # state_history: 実行中の量子状態の履歴
        # command_history: 実行されたコマンドの履歴
        # circuit_all: 最終的な回路
        return self.state, self.state_history, self.command_history, self.circuit_all

    def measure(self):
        # Observable による期待値計算
        single_qubit_observable = Observable(self.num_qubits)
        single_qubit_observable.add_operator(1.0, f"Z {self.pointer}")
        e = single_qubit_observable.get_expectation_value(self.state)
        prob = (1.0 - e) * 0.5
        result = 0 if prob > np.random.rand() else 1
        self.log(f"Expected Value : {prob}")
        self.log(f"Measured Result: {result}")
        return result
