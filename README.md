```text
##############################################################################################
#                                                                                            #
#   ______                                     __        __  _                               #
#  / ____/___  ____ ___  ____  __  __________ _/ /_____  / /_(_)___  ____  ____ _/ /         #
# / /   / __ \/ __ `__ \/ __ \/ / / / ___/ __ `/ __/ __ \/ / / / __ \/ __ \/ __ `/ /         #
#/ /___/ /_/ / / / / / / /_/ / /_/ (__  ) /_/ / /_/ /_/ / / / / /_/ / / / / /_/ / /          #
#\____/\____/_/ /_/ /_/ .___/\__,_/____/\__,_/\__/\____/_/_/_/\____/_/ /_/\__,_/_/           #
#                    /_/                                                                     #
#    ____  __               _              ____                 _                            #
#   / __ \/ /_  __  _______(_)__________  / __ )___  ____  ____/ /_                          #
#  / /_/ / __ \/ / / / ___/ / ___/ ___/  / __  / _ \/ __ \/ ___/ __ \                        #
# / ____/ / / / /_/ (__  ) / /__(__  )  / /_/ /  __/ / / / /__/ / / /                        #
#/_/   /_/ /_/\__, /____/_/\___/____/  /_____/\___/_/ /_/\___/_/ /_/                         #
#            /____/                                                                          #
##############################################################################################
```




## Overview
[Computational-Physics-Bench](https://github.com/Icosian-World/computational-physics-bench) is a benchmark for evaluating AI agents on complex real-world computational physics workflows in terminal environments. CP-Bench focuses specifically on computational research workflows across the physical sciences. Our goal is to catalyze a "Claude Code / Codex for Science" moment: a benchmark that drives the development of AI systems capable of reliably accelerating end-to-end scientific research.

## Quickstart

```bash
# Install Harbor
uv tool install harbor

# Export your API keys
export ANTHROPIC_API_KEY=<your_anthropic_key>   # For Claude models
export OPENAI_API_KEY=<your_openai_key>         # For OpenAI GPT models
export GEMINI_API_KEY=<your_gemini_key>         # For Google Gemini models

# Run the Oracle agent on a task
harbor run -p tasks/<task-domain>/<task-field>/<task-name> -a oracle

# Run an AI agent on a task
harbor run -p tasks/<task-domain>/<task-field>/<task-name> -a <agent> -m <provider/model>
```

> Replace the placeholders:
> - `<task-domain>`: The science domain (physical-sciences)
> - `<task-field>`: The specific field (e.g., condensed-matter, quantum-mechanics, astrophysics, etc.)
> - `<task-name>`: The task name (e.g., tight-binding-model, schrodinger-solver)
> - `<agent>`: The agent identifier (e.g., `claude-code` or `codex`)
> - `<provider/model>`: The model identifier (e.g., `anthropic/claude-opus-4-6` or `openai/gpt-5.4`)

## Benchmark Progress

Our goal is to build 100+ tasks across various fields in computational physics. The table below tracks our progress toward this goal.

| Scientific Domain | Field | Current Task Count |
|--------|-------|-------|
| [![PhysicalSciences](https://img.shields.io/badge/Physical%20Sciences-8C071A?style=for-the-badge)](tasks/physical-sciences/) | [Condensed Matter](tasks/physical-sciences/condensed-matter/) | <!--CONDENSED_MATTER_COUNT--> 0
| | [Quantum Mechanics](tasks/physical-sciences/quantum-mechanics/) | <!--QUANTUM_MECHANICS_COUNT--> 0
| | [Astrophysics](tasks/physical-sciences/astronomy/) | <!--ASTRONOMY_COUNT--> 0
| | [Fluid Dynamics](tasks/physical-sciences/fluid-dynamics/) | <!--FLUID_DYNAMICS_COUNT--> 0
| | [Statistical Mechanics](tasks/physical-sciences/statistical-mechanics/) | <!--STATISTICAL_MECHANICS_COUNT--> 0
| | [High Energy Physics](tasks/physical-sciences/high-energy-physics/) | <!--HIGH_ENERGY_PHYSICS_COUNT--> 0
| **Total** | | <!--TOTAL_COUNT--> **0**

## Contributing

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed instructions on how to contribute tasks to this benchmark.

## Contact

Have questions, feedback or need help? Here's how to reach us:

- **Project Lead:** Richa Sharma (DM `@richa` on our [Discord](https://discord.gg/ZvcWupVXjz) or email [richa@icosian.ai](mailto:richa@icosian.ai))
- **Community:** Join the `#cp-bench` channel on our [Discord](https://discord.gg/ZvcWupVXjz) for general questions
- **Harbor Docs:** [Harbor Documentation](https://harborframework.com/docs)

## Citation

If you find this work useful, please cite it. You can use the citation button on GitHub (generated from [CITATION.cff](CITATION.cff)) or cite manually using the information below.

```
@misc{computational-physics-bench,
author = {Richa Sharma},
month = feb,
title = {{Computational-Physics-Bench: Evaluating AI Agents on Computational Workflows in the Physical Sciences}},
url = {https://github.com/Icosian-World/computational-physics-bench},
year = {2026}
}
```

## License

Apache 2.0. See [LICENSE](LICENSE) for details.

## Acknowledgements

[Computational-Physics-Bench](https://github.com/Icosian-World/computational-physics-bench) is part of Frontier Physics Franchise owned by Icosian (https://icosian.world)

