# Quantumf*ck: Poetic Quantum Programming Language

## Installation

```bash
!pip install quri-parts[qulacs]
!pip install exrex
```

## List of Quantumf*ck commands

| Command | Quantum Circuit Manipulation                                                                             |
| ------- | -------------------------------------------------------------------------------------------------------- |
| >       | Make the next qubit the target of operation (pointer +1 )                                                |
| <       | Make the previous qubit the target of operation (pointer -1)                                             |
| +, H    | Apply Hadamard gate                                                                                      |
| ~, T    | Apply$\frac{\pi}{4}$ phase shift gate                                                                    |
| -, D    | Apply$- \frac{\pi}{4}$ phase shift gate (conjugate of T gate)                                            |
| x, X    | Apply Pauli-X gate                                                                                       |
| @, C    | Apply CNOT gate (target is the next qubit or specified by following number)                              |
| :       | Estimate measurements from state vector (no actual measurement)                                          |
| ,       | Initialize state vector                                                                                  |
| ;       | State vector randomization                                                                               |
| [       | Start of loop                                                                                            |
| ]       | Conditional loop termination (exits loop if measured value is 0, otherwise returns to beginning of loop) |
| ?       | Hadamard gate or$\frac{\pi}{4}$ phase shift gate is applied randomly                                     |
| !       | Randomly move the qubit (pointer) to be manipulated                                                      |
| *       | Randomly move execution point                                                                            |

## Usage

```python
# Instantiate class
num = 5
qf = QF(num, regex=False, debug=False)

# Execute code
code = "[+!?~#!~@:]"
state, history, command, circuit = qf.parse(code)

# Output history of state vector
for i, s in enumerate(history):
    print(f"Step {i}: {s}")
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
