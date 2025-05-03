# General

* We're building Anki addon
* We're at MVP stage and need to get working vertical slice

# Development
* Dependency Inversion principles are paramount - hidden dependecies MUST be avoided as much as feasible
## Python Development
* Use modern Python >=3.13 features:
    * use e.g. `list[str]` instead of `typing.List[str]`
    * use `None | int` instead of `Optional[int]`
* Project is using `uv` package for package management in Python
* When "typing" module is needed:
    * use `import typing as t`
    * use stuff from it like `t.Protocol`
* Input types for function arguments must be of least-restrictive types (e.g., `t.Sequence` instead of `list`) to maximize caller's flexibility while maintaining necessary invariants.
* Absolute import MUST be used for all imports
* For testing we use `pytest`
    * Standlone functions and fixtures MUST be used instead of unittest-style test classes
* Excessive comments and docstrings are discouraged:
    * MUST USE `typing` for arguments instead of describing the said arguments in docstrings
    * Docstrings MUST be short and to the point
    * Docstrings SHOULD be used only for public functions
    * Simple functions SHOULD NOT have docstrings at all
* Project relies on asyncio (and qt stuff is also integrated with it), so there is no problem of thread-synchronization.

# How LLM should behave
* Be concise, but not too concise