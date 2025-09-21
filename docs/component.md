# Component Definition

This document outlines the standard structure and requirements for a component (package) within the Mail Client Workspace. 

Components represent distinct units of functionality, typically either a protocol (interface) or an implementation.

## Component Structure (`src/<component_name>/`)

Each component resides in its own directory under `src/` and follows this structure:

```
<component_name>/
├── pyproject.toml       # Build system, dependencies, metadata
├── README.md            # Component-specific documentation (this file!)
└── src/
    └── <component_name>/  # The actual Python package source
        ├── __init__.py     # Main module, exports, factory override (for impl)
        └── _impl.py        # (Implementations only) Contains the concrete class
└── tests/               # (Optional) Unit tests specific to this component
    └── test*.py
```

## `pyproject.toml` Requirements

- **`[project]` section:**
  - `name`: Must match the directory name (e.g., `message`, `message_impl`).
  - `version`: Follow semantic versioning (e.g., `0.1.0`).
  - `description`: Brief summary of the component's purpose.
  - `readme = "README.md"`
  - `requires-python = ">=3.11"`
  - `dependencies`: List *direct* external dependencies OR workspace dependencies.

- **`[build-system]` section:**
  - Use `hatchling` as the build backend.
  ```toml
  [build-system]
  requires = ["hatchling"]
  build-backend = "hatchling.build"
  ```

- **`[tool.uv.sources]` section:** (If depending on other workspace components)
  - Declare workspace dependencies.
  ```toml
  [tool.uv.sources]
  other_component = { workspace = true }
  ```

## `README.md` Requirements

Each component MUST have a `README.md` covering:

1. **Overview:** What the component is and its primary role.
2. **Scope:** What it does and does not do.
3. **Protocol/Class Definition:** Key interfaces, methods, properties, or classes provided.
4. **Usage:** How the component is intended to be used (e.g., via factory function, direct import).
5. **Dependencies:** List key dependencies (especially other workspace components).

## Implementation (`_impl.py`)

- For implementation components (e.g., `message_impl`), the main concrete class(es) should reside in `_impl.py`.
- This keeps the component's `__init__.py` clean, focusing on exports and dependency injection.

## Initialization (`__init__.py`)

- **Protocols:** Define the `Protocol` class(es) and the default `get_...()` factory function (which should `raise NotImplementedError`).
- **Implementations:**
  - Import the corresponding protocol package.
  - Import the concrete class(es) from `._impl`.
  - Define a `get_..._impl()` factory function that returns an instance of the concrete class.
  - **Crucially:** Override the protocol's factory function: `protocol_package.get_... = get_..._impl`.
  - Use `__all__` if specific classes need to be directly importable.

## Testing (`tests/`)

- Unit tests specific to the component's logic should reside here.
- Tests should primarily interact with the component's defined interface (protocol or implementation factory).
- Use mocking (`unittest.mock`) extensively to isolate the component from external dependencies or other workspace components during unit tests.
