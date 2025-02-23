# Quantumf*ck: Poetic//Esoteric Quantum Programming Language

## Installation

!pip install qulacs qulacsvis
!pip install exrex

## Usage

\# クラスのインスタンス化
num = 5
qf = QF(num, regex=False, debug=False)

\# コードを実行
code = "[+!?~#!~@:]"
state, history, command, circuit = qf.parse(code)

\# 状態ベクトルの履歴を出力
#for i, s in enumerate(history):
    print(f"Step {i}: {s.get_vector()}")

\# 回路の可視化（オプション）
circuit_drawer(circuit, "mpl")


## License

This project is licensed under the MIT License - see the LICENSE file for details.

