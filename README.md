# Quantumf*ck: Poetic Quantum Programming Language

## Installation

```bash
!pip install qulacs qulacsvis
!pip install exrex
```

## Usage

```python
# Instantiate class
num = 5
qf = QF(num, regex=False, debug=False)

# Execute code
code = "[+!?~#!~@:]"
state, history, command, circuit = qf.parse(code)

# Output history of state vector
#for i, s in enumerate(history):
    print(f"Step {i}: {s.get_vector()}")

# visualize the circuit (optional)
circuit_drawer(circuit, "mpl")
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
