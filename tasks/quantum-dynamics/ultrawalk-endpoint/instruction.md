# Ultrawalk Endpoint

A one-dimensional discrete-time quantum walk evolves on the integer line with a two-component wavefunction. At each time step, a site-dependent unitary coin is applied, followed by a conditional shift.

Build a simulator and analysis pipeline to estimate epsilon_star separating localized and transporting behavior.

## Required Outputs in /workspace/output/

1. simulator.py - with simulate() function
2. analysis.py - with estimate_inv_dw() and estimate_epsilon_star()
3. epsilon_star.json
4. transport_table.csv
5. notes.md

See /workspace/data/problem.md for full details.
