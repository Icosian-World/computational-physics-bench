# Contributing to Computational-Physics-Bench

Thank you for your interest in contributing to **Computational-Physics-Bench**! This benchmark is built by the community to evaluate AI agents on real-world computational physics tasks.

## How to Contribute

We welcome contributions of new tasks, bug fixes, and improvements to the benchmark infrastructure.

### Adding a New Task

To add a new task, follow these steps:

1.  **Fork the repository** and create a new branch for your task.
2.  **Define your task** in a new directory under `tasks/physical-sciences/<field>/<task-name>`.
3.  **Include the following files**:
    *   `README.md`: Description of the task and the goal.
    *   `Dockerfile`: The environment setup for the task.
    *   `task.yaml` (or relevant metadata): Task definitions and evaluation criteria.
    *   `solution/`: An oracle or reference solution.
4.  **Test your task** using Harbor:
    ```bash
    harbor run -p tasks/physical-sciences/<field>/<task-name> -a oracle
    ```
5.  **Submit a Pull Request**.

### Code of Conduct

Please be respectful and constructive in all interactions.

## Contact

If you have any questions, join our [Discord](https://discord.gg/ZvcWupVXjz) or contact Richa Sharma at [richa@icosian.ai](mailto:richa@icosian.ai).
