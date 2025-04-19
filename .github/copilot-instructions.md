# General

* We're building Anki addon
* We're at MVP stage and need to get working vertical slice

# Development
* Dependency Inversion principles are paramount - hidden dependecies MUST be avoided as much as feasible
## Python Development
* Use modern Python >=3.13 features:
    * use e.g. `list[str]` instead of `typing.List[str]`
    * use `None | int` instead of `Optional[int]`
* automation scripts must be run using `./dodo.py <args>`
* project is using `uv` package for package management in Python
* when "typing" module is needed:
    * use `import typing as t`
    * use stuff from it like `t.Protocol`
* Input types for function arguments must be of least-restrictive types (e.g., `t.Sequence` instead of `list`) to maximize caller's flexibility while maintaining necessary invariants.
* Absolute import MUST be used for all imports
* for testing we use `pytest`; standlone functions and fixtures are preferred over classes

# How LLM should behave
* Be concise, but not too concise