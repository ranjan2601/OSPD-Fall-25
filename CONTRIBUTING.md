# Contributing Guide

This guide provides an overview of the base mail client repository architecture, design patterns, and development workflows. It is intended to help new contributors understand the foundational design principles and practices that guide this codebase.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Repository Structure](#repository-structure)
3. [Testing Strategy](#testing-strategy)
4. [Development Tools](#development-tools)

## Architecture Overview

This project demonstrates a component-based architecture built around the principle of "programming integrated over time." The design combats complexity through strict separation of concerns, clear interface boundaries, and dependency injection patterns that enable flexibility and maintainability.

### Components

The repository is organized as a `uv` workspace containing two primary components:

#### 1. mail_client_api

This component defines the abstract contracts for interacting with mail systems. It contains two primary abstractions:

**Client Abstract Base Class**: Defines the interface for mail client operations with four core methods:
- `get_messages(max_results: int = 10) -> Iterator[Message]`: Retrieve an iterator of messages from the inbox
- `get_message(message_id: str) -> Message`: Retrieve a specific message by its ID
- `delete_message(message_id: str) -> bool`: Delete a message and return success status
- `mark_as_read(message_id: str) -> bool`: Mark a message as read and return success status

**Message Abstract Base Class**: Defines the interface for email message data with five properties:
- `id`: Unique identifier for the message
- `from_`: Sender's email address (using `from_` to avoid Python keyword conflict)
- `to`: Recipient's email address
- `date`: Date the message was sent
- `subject`: Subject line of the message
- `body`: Plain text content of the message

**Factory Functions**: The component provides two factory functions:
- `get_client(*, interactive: bool = False) -> Client`: Factory for obtaining a client instance
- `get_message(msg_id: str, raw_data: str) -> Message`: Factory for constructing message instances

These factory functions raise `NotImplementedError` by default and are meant to be replaced by concrete implementations through dependency injection.

#### 2. gmail_client_impl

This component provides concrete implementations of the abstract contracts defined in `mail_client_api`, specifically for Gmail:

**GmailClient**: A concrete implementation of the `Client` ABC that uses the Google Gmail API to perform mail operations. It handles:
- OAuth2 authentication with multiple fallback strategies (environment variables, token files, interactive flow)
- All CRUD operations on Gmail messages
- Error handling and logging for API interactions
- Token management and refresh

**GmailMessage**: A concrete implementation of the `Message` ABC that parses Gmail message data. It handles:
- Base64 decoding of Gmail's raw message format
- RFC 2047 encoded header decoding (for international characters in subjects)
- Multi-part MIME message parsing
- Binary content detection and error handling
- Extracting plain text from complex email structures

**Factory Implementations**: The component provides corresponding factory implementations:
- `get_client_impl(*, interactive: bool = False) -> Client`: Returns a configured `GmailClient` instance
- `get_message_impl(msg_id: str, raw_data: str) -> Message`: Returns a `GmailMessage` instance

#### Component Interactions

The components interact through a clear, layered architecture:

**Application Layer** (e.g., `main.py`): The top-level application code imports both `mail_client_api` and `gmail_client_impl`. It uses only the abstract interfaces from `mail_client_api` to interact with the mail system. The application never directly instantiates or references concrete implementation classes.

**Dependency Injection**: When `gmail_client_impl` is imported, it automatically registers its implementations by replacing the factory functions in `mail_client_api`. This happens at module import time through the `register()` function defined in the implementation package's `__init__.py`.

**Abstraction Layer** (`mail_client_api`): Defines stable contracts that application code depends on. This layer knows nothing about Gmail or any specific implementation. It only defines "what" operations are available, not "how" they work.

**Implementation Layer** (`gmail_client_impl`): Provides concrete implementations that fulfill the contracts. This layer depends on `mail_client_api` for the interface definitions and on Google's API libraries for functionality. It defines "how" the operations work using Gmail-specific APIs.

This architecture ensures that:
- Application code never directly depends on implementation details
- Implementations can be swapped without changing application code
- Each component has a single, well-defined responsibility
- Components can be "forklifted" into other projects independently
- New implementations (e.g., Outlook, IMAP) can be added without modifying existing code

### Interface Design

The interface design in this project follows several key principles that make the system maintainable and flexible.

#### Design Philosophy

The interfaces are designed to be **deep**, not **shallow**. In John Ousterhout's terminology (from "A Philosophy of Software Design"), a deep interface provides powerful functionality behind a simple interface, hiding complexity from callers.

The `Client` interface exemplifies this principle. The `get_messages()` method, while appearing simple with just one parameter, hides significant complexity including:
- OAuth2 authentication and token management
- Gmail API calls and pagination
- Raw message data retrieval and decoding
- Message object construction and validation
- Error handling for network and API failures

The caller simply gets an iterator of `Message` objects, completely abstracted from these implementation details.

#### Design Choices and Justifications

**1. Using Abstract Base Classes (ABC)**

The project uses Python's `abc.ABC` to define interfaces rather than informal "duck typing" or Protocol classes. This choice provides:

**Explicit contracts**: Methods are explicitly marked with `@abstractmethod`, making it clear what must be implemented by any concrete implementation.

**Runtime validation**: Python will raise `TypeError` if someone tries to instantiate an abstract class without implementing all abstract methods. This fails fast and prevents incomplete implementations from being used.

**IDE support**: Type checkers and IDEs can validate that implementations satisfy the contract, providing better developer experience with autocompletion and error detection.

**Documentation**: The abstract class serves as explicit documentation of the interface. New contributors can look at the ABC to understand exactly what operations are available.

**2. Return Types and Iteration**

The `get_messages()` method returns an `Iterator[Message]` rather than a `List[Message]`. This design choice provides:

**Lazy evaluation**: Messages can be fetched and processed one at a time, reducing memory usage for large inboxes.

**Flexibility**: The implementation can stream data, paginate, or generate messages on-demand without the caller needing to know.

**Abstraction of data sources**: The caller doesn't need to know if messages come from an API, database, file, or are generated dynamically.

**Performance**: For operations that don't need all messages, iteration can be stopped early without fetching unnecessary data.

**3. Factory Functions**

The project uses factory functions (`get_client()`, `get_message()`) rather than direct class instantiation. This provides:

**Decoupling**: Callers don't need to know which concrete class to instantiate. They just call the factory function.

**Flexibility**: The factory can return different implementations based on context (environment, configuration, feature flags).

**Dependency Injection**: Implementations can replace factories at runtime without changing caller code. This is the core of the pattern used in this project.

**Testing**: Factories can be easily replaced with mock implementations in tests.

**4. Boolean Return Values**

Methods like `delete_message()` and `mark_as_read()` return `bool` to indicate success rather than raising exceptions for expected failures. This design:

**Distinguishes expected failures from errors**: A "message not found" is different from a network error. The former returns False, the latter raises an exception.

**Simplifies error handling**: Callers can handle failures with simple conditionals rather than try-except blocks for every operation.

**Enables graceful degradation**: Applications can continue operating when non-critical operations fail, logging the failure but not crashing.

**Provides clear success indication**: The boolean return makes it explicit whether the operation succeeded.

#### Comparison with Protocol from the Typing Module (Extra Credit)

The project uses `abc.ABC` for interface definitions, but Python also provides `Protocol` from the `typing` module. Understanding the differences helps clarify why ABC was chosen for this architecture.

**Abstract Base Classes (ABC) - Used in This Project:**

ABC requires explicit inheritance where implementations must declare `class GmailClient(Client)`. Python enforces this with runtime validation - attempting to instantiate a class with unimplemented abstract methods raises `TypeError` immediately. This creates a nominal subtyping relationship where the inheritance hierarchy is explicit and visible.

Characteristics of ABC:
- Requires explicit opt-in through inheritance
- Validates implementations at instantiation time (runtime)
- Creates clear, documented relationships between interfaces and implementations
- Supports runtime `isinstance()` checks
- Better for defining contracts that implementations must consciously fulfill

**Protocol (Structural Subtyping):**

Protocol uses structural subtyping where any class with matching method signatures satisfies the protocol, without requiring inheritance. Type checkers like mypy verify compatibility statically, but Python performs no runtime validation.

Characteristics of Protocol:
- No inheritance required - any class with the right "shape" works
- Validates implementations only during static type checking
- Enables duck typing with type safety
- More flexible - works with existing code without refactoring
- Better for describing patterns that existing code might already satisfy

**When to Use ABC vs Protocol:**

**Use ABC (as this project does) when:**
1. You want explicit contracts that implementations must opt into
2. You need runtime validation that implementations are complete
3. You want clear inheritance relationships visible in the code
4. You're defining new interfaces that implementations should consciously fulfill
5. You want runtime `isinstance()` checks to work correctly
6. You're building a component-based architecture with explicit registration

**Use Protocol when:**
1. You're describing existing code that already has the right methods
2. You want flexibility without requiring refactoring to add inheritance
3. You're working with third-party code you can't modify
4. You prefer structural typing (Go-style interfaces)
5. You only need static type checking, not runtime validation
6. You're writing library code that should work with many existing types

**Why This Project Uses ABC:**

This project chose ABC for several important reasons:

**Explicit opt-in**: We want implementations to consciously implement the `Client` contract. The explicit inheritance makes this relationship clear.

**Runtime validation**: Instantiating an incomplete implementation should fail fast with a clear error message, not cause subtle bugs later.

**Clear relationships**: It should be immediately obvious from the code that `GmailClient` implements `Client`. This aids understanding and maintenance.

**Dependency injection alignment**: The pattern requires explicit registration through the `register()` function, which aligns well with explicit inheritance.

**Educational value**: ABC makes the architecture more explicit and easier to understand for contributors learning the codebase.

**Trade-offs:**

ABC is more rigid but provides stronger guarantees. Protocol is more flexible but relies entirely on static type checking. For a component-based architecture where we control all implementations and want clear contracts, ABC is the better choice. If we were wrapping third-party libraries or needed to work with existing classes, Protocol would be more appropriate.

### Implementation Details: How Python Features Enable the Interface Pattern

The interface pattern in this repository is implemented using Python's built-in `abc` module, which provides the infrastructure for defining abstract base classes. Understanding these Python features is essential for contributors working with or extending the abstractions.

#### Python Features and Modules Used

**1. The `abc` Module (Abstract Base Classes)**

Python's `abc` module provides the `ABC` class and `@abstractmethod` decorator. The `ABC` class uses `ABCMeta` as its metaclass, which enables special behavior for abstract methods. The `@abstractmethod` decorator marks a method as abstract, requiring subclasses to implement it.

Python enforces abstract method implementation at instantiation time. When you try to create an instance of a class with unimplemented abstract methods, Python raises `TypeError` immediately. The `raise NotImplementedError` in abstract methods is a fallback that documents intent but would never execute if the ABC mechanism is working correctly.

**2. Type Hints and Type Annotations**

Modern Python type hints (PEP 484, PEP 544) are used throughout the interfaces. Type annotations provide:
- Static type checking with mypy to catch errors before runtime
- IDE autocompletion and inline documentation
- Machine-readable documentation of interfaces
- Early detection of type mismatches
- Support for generic types like `Iterator[Message]` indicating lazy evaluation

**3. Properties with `@property` and `@abstractmethod`**

For the `Message` interface, abstract properties combine two decorators. The `@property` decorator makes the method accessible as an attribute (e.g., `message.id` instead of `message.id()`). Stacking `@abstractmethod` with `@property` requires subclasses to implement the property. The order matters: `@property` must be the innermost decorator, closest to the function definition.

The `from_` property name is used instead of `from` to avoid conflict with Python's `from` keyword.

**4. Function Objects and First-Class Functions**

The dependency injection pattern relies on Python treating functions as first-class objects. Functions are objects that can be assigned to variables. The statement `mail_client_api.get_client = get_client_impl` replaces the function object bound to the name `get_client` in the `mail_client_api` module.

This is valid Python because modules are mutable namespaces and functions are just attributes of those modules. This isn't monkey-patching - it's standard Python behavior for working with module attributes.

**5. Module-Level Execution**

Registration happens at import time through module-level code. Python executes all module-level code when a module is first imported. The `register()` call at module level in `gmail_client_impl/__init__.py` runs automatically when the module is imported. This creates the dependency injection without requiring explicit initialization code.

Subsequent imports use the cached module from `sys.modules`, so registration happens exactly once per Python interpreter session.

#### How Interfaces Are Defined

Interfaces are defined in the `mail_client_api` package using several components:

The `Client` class inherits from `ABC` making it abstract. Each method is decorated with `@abstractmethod` marking it as required in subclasses. Type hints specify parameter and return types precisely. Docstrings document the expected behavior.

The factory function `get_client()` initially raises `NotImplementedError`. This function will be replaced by implementations during their registration process.

The `__all__` list in `__init__.py` explicitly controls what gets exported from the module, keeping the public API clean and focused.

Key aspects of interface definition:
1. Inheriting from `ABC` makes the class abstract
2. `@abstractmethod` decorator marks methods as required
3. Type hints specify the contract precisely
4. Factory functions return the abstract type
5. Factories initially raise `NotImplementedError`

#### How Interfaces Are Implemented

Concrete implementations explicitly inherit from and fulfill the contract:

The `GmailClient` class explicitly declares inheritance: `class GmailClient(mail_client_api.Client)`. This establishes the contract that must be fulfilled.

All abstract methods are implemented with concrete logic using the Gmail API. The return types match the interface exactly. The implementation can have additional methods and attributes not in the interface - these are implementation details not exposed through the abstract interface.

A factory function `get_client_impl()` knows how to create and configure a `GmailClient` instance with proper authentication.

The `register()` function performs the dependency injection by replacing `mail_client_api.get_client` with `get_client_impl`.

Key aspects of implementation:
1. Explicit inheritance establishes the contract
2. All abstract methods must be implemented
3. Return types must match the interface
4. Additional methods/attributes are allowed
5. Factory replacement enables dependency injection

#### How This Leads to Implementation: The Complete Flow

The pattern creates a clear separation between "what" and "how" through four distinct phases:

**Phase 1: Definition (Interface Package)**

The `mail_client_api` package defines the abstract `Client` class using `abc.ABC`. Abstract methods specify what operations are available and their signatures. The factory function `get_client()` defines how to obtain a client (initially undefined). Type hints document expected inputs and outputs. This layer is stable and changes rarely.

**Phase 2: Implementation (Implementation Package)**

The `gmail_client_impl` package provides the concrete `GmailClient` class inheriting from `Client`. It implements how each operation works using the Gmail API. The factory function `get_client_impl()` knows how to create and configure a `GmailClient`. The registration function replaces the abstract factory with the concrete one.

**Phase 3: Connection (Dependency Injection)**

Importing `gmail_client_impl` triggers its module-level `register()` call. The `mail_client_api.get_client` function object is replaced with `get_client_impl`. Now calling `mail_client_api.get_client()` returns a `GmailClient` instance. Application code only imports and uses `mail_client_api`, never directly referencing implementation classes.

**Phase 4: Usage (Application Code)**

Application code imports both packages but only uses the abstraction. The import of `gmail_client_impl` triggers registration (even though the app doesn't call anything from it directly). Calling `mail_client_api.get_client()` returns a fully configured `GmailClient`. All interactions go through the abstract `Client` interface.

#### What This Architecture Enables

**Testability**: Tests can mock the abstract interface without touching real APIs by replacing the factory: `mail_client_api.get_client = lambda **kwargs: MockClient()`.

**Flexibility**: New implementations can be added without changing existing code. Create a new implementation package with its own `register()` function.

**Maintainability**: Changes to Gmail implementation details don't affect application logic because application code only depends on the stable interface.

**Type Safety**: Static type checkers verify that implementations match interfaces and that callers use the interface correctly.

**Incremental Development**: Interfaces can be defined before implementations exist, allowing teams to work in parallel.

**Runtime Verification**: Python's ABC mechanism prevents instantiation of incomplete implementations, catching errors early in development.

### Dependency Injection

Dependency injection is a core pattern in this project that enables loose coupling between abstractions and implementations. Instead of having application code directly instantiate concrete classes, implementations are "injected" into the abstract factory functions at runtime.

#### How Dependency Injection Works in This Project

The dependency injection happens through a simple but powerful mechanism:

**Step 1: Abstract Factory Functions (Uninitialized)**

The `mail_client_api` package defines factory functions in `client.py` that initially raise `NotImplementedError`. The function `get_client(*, interactive: bool = False) -> Client` is defined but not implemented.

**Step 2: Implementation Package Registration**

The `gmail_client_impl` package provides a concrete factory function `get_client_impl(*, interactive: bool = False)` that creates and returns a fully configured `GmailClient` instance.

It also provides a `register()` function that performs the injection. Here's exactly where the injection occurs:

```python
# In src/gmail_client_impl/src/gmail_client_impl/gmail_impl.py
def register() -> None:
    """Register the Gmail client implementation with the mail client API."""
    mail_client_api.get_client = get_client_impl  # This line performs the injection
```

This assignment replaces the unimplemented factory with the working implementation. This is the core of dependency injection: the function object in `mail_client_api` is replaced with a function that knows how to create Gmail clients.

**Step 3: Automatic Registration at Import Time**

The registration happens automatically when the implementation package is imported. In `gmail_client_impl/__init__.py`, the module-level code calls `register()` immediately after defining it. The comment "Dependency Injection happens at import time" makes this explicit.

Because this is module-level code, simply importing `gmail_client_impl` anywhere in the application triggers the registration.

**Step 4: Application Usage**

Application code in `main.py` imports both packages. The import statement `import gmail_client_impl` triggers registration (though the application never explicitly calls anything from this module). When the application calls `mail_client_api.get_client(interactive=False)`, it now gets a `GmailClient` instance, but the application code only knows about the `Client` interface.

#### What This Pattern Enables

**Multiple Implementations**: Contributors can create alternative implementations by providing their own `register()` function. For example, creating an Outlook client would involve:
1. Creating a new package `outlook_client_impl`
2. Implementing `OutlookClient(mail_client_api.Client)`
3. Providing a `register()` function that replaces the factory
4. Importing this package instead of `gmail_client_impl`

**Testing Flexibility**: Tests can inject mock implementations without modifying source code. Test code can simply assign a mock factory before running tests.

**Runtime Configuration**: The factory can make decisions based on environment variables, configuration files, or runtime conditions to select different implementations. The factory could check an environment variable and return different client types accordingly.

**Loose Coupling**: Application code never imports or references concrete implementation classes. It only knows about the abstract interface. This means implementations can change completely without affecting application code.

**Component Independence**: The `mail_client_api` package has no knowledge of Gmail or any specific implementation. It can be used in any project that needs a mail client abstraction, even projects that use different mail providers.

**Extensibility**: New contributors can add features by:
- Extending the abstract interface (if needed)
- Creating new implementations that fulfill the contract
- Registering their implementation without modifying existing code
- The application automatically uses the new implementation

This pattern is sometimes called the "Service Locator" pattern or "Factory Method" pattern. The key principle is that abstractions define what is needed, concrete implementations provide it, and the connection happens through a replaceable factory function.

## Repository Structure

Understanding the repository's organization is essential for navigating the codebase and knowing where to add new code or find existing functionality.

### Project Organization

The repository follows a strict directory structure that separates concerns and supports the component-based architecture.

The root directory contains the main entry point (`main.py`), configuration files (`pyproject.toml`, `uv.lock`, `mkdocs.yml`), and documentation (`README.md`). Secret files like `credentials.json` and `token.json` exist locally but are excluded from version control via `.gitignore`.

The `src/` directory contains all workspace member packages. Each subdirectory is an independent Python package with its own dependencies, tests, and configuration. Each component follows the "src layout" pattern with double nesting:
- Outer directory: component root
- Inner `src/` directory: location for the actual Python package
- Innermost directory: the importable package

This double-nesting prevents accidental imports of the development version during testing.

The `tests/` directory contains integration and end-to-end tests that verify interactions between components or test the full application. Unit tests live within each component's directory.

The `docs/` directory contains Markdown documentation files processed by MkDocs to generate the project documentation website. It includes API reference documentation generated from docstrings.

The `.circleci/` directory contains the CI/CD pipeline configuration that runs automated tests, linting, and type checking on every commit.

**Directory Structure Overview:**

**Root level** contains:
- `main.py`: Application entry point demonstrating usage
- `pyproject.toml`: Root project configuration
- `uv.lock`: Locked dependency versions
- `mkdocs.yml`: Documentation generation configuration
- `README.md`: Project overview and setup guide
- `.gitignore`: Excludes secrets and generated files
- `.python-version`: Specifies Python version

**src/** contains workspace packages:
- `mail_client_api/`: Interface definitions
  - `pyproject.toml`: Component configuration
  - `src/mail_client_api/`: The actual package
    - `__init__.py`: Public API exports
    - `client.py`: Client interface
    - `message.py`: Message interface
  - `tests/`: Unit tests for the API abstraction
- `gmail_client_impl/`: Gmail implementation
  - `pyproject.toml`: Component configuration with dependencies
  - `src/gmail_client_impl/`: The actual package
    - `__init__.py`: Registration and exports
    - `gmail_impl.py`: GmailClient implementation
    - `message_impl.py`: GmailMessage implementation
  - `tests/`: Unit tests for Gmail implementation

**tests/** contains integration and E2E tests:
- `integration/`: Tests verifying component interactions
- `e2e/`: End-to-end application tests

**docs/** contains documentation:
- `api/`: API reference documentation
- Architecture and testing guides
- CI/CD setup instructions

### Configuration Files

The repository uses `pyproject.toml` files at two levels with different purposes.

#### Root `pyproject.toml`

The root `pyproject.toml` serves multiple purposes:

**Workspace Definition**: The `[tool.uv.workspace]` section declares the repository as a uv workspace and lists member packages. All members are installed together in a shared virtual environment with inter-component dependencies resolved correctly.

**Development Dependencies**: The `[project.optional-dependencies]` section defines development tools (testing, linting, documentation, type checking) that apply to the entire workspace. These are installed with `uv sync --extra dev`.

**Tool Configuration (Default)**: The root file contains default configuration for development tools like ruff, mypy, and pytest. These settings apply to the entire workspace. Component-level configurations can extend or override these defaults.

**Test and Coverage Configuration**: The `[tool.pytest.ini_options]` section configures pytest for the entire workspace, including test discovery paths, markers (unit, integration, e2e, circleci, local_credentials), and coverage options. The `[tool.coverage.run]` and `[tool.coverage.report]` sections configure coverage measurement and the minimum 85% threshold.

**Type Checking Configuration**: The `[tool.mypy]` section defines strict type checking settings and where to find packages.

#### Component-Level `pyproject.toml`

Each component has its own configuration defining:

**Component Metadata**: The `[project]` section identifies the component with name, version, description, and Python version requirement.

**Component Dependencies**: Each component declares its own runtime dependencies. For example, `gmail_client_impl` depends on Google API libraries and on `mail-client-api` (an internal workspace member).

**Workspace Dependency Resolution**: The `[tool.uv.sources]` section tells uv that certain dependencies should be resolved from the workspace rather than PyPI.

**Build System**: The `[build-system]` section defines how the component should be built into a distributable package (using hatchling).

**Component-Specific Tool Configuration**: Components can override or extend root tool configuration. The `extend = "../../pyproject.toml"` directive inherits settings from the root.

#### When to Modify Which File

**Modify the root `pyproject.toml` when:**
- Adding a new workspace member
- Adding development tools (linters, formatters, test runners)
- Changing workspace-wide linting or formatting rules
- Adjusting test markers or coverage requirements
- Updating documentation tools
- Changing settings that affect the entire project

**Modify a component `pyproject.toml` when:**
- Adding dependencies specific to that component
- Changing component metadata (version, description)
- Overriding formatting rules for that component only
- Adding component-specific test dependencies
- Changing how that component is built or packaged

### Package Structure

Python packages use `__init__.py` files to define package boundaries and control exports.

#### Where `__init__.py` Files Exist

Every directory that should be treated as a Python package has an `__init__.py` file:

**In source packages:**
- `src/mail_client_api/src/mail_client_api/__init__.py`
- `src/gmail_client_impl/src/gmail_client_impl/__init__.py`

**In test directories:**
- `src/mail_client_api/tests/__init__.py`
- `src/gmail_client_impl/tests/__init__.py`
- `tests/__init__.py`
- `tests/integration/__init__.py`
- `tests/e2e/__init__.py`

#### Keeping `__init__.py` Slim

The project follows the principle of "keeping `__init__.py` slim," which means these files should contain minimal logic and primarily serve as a controlled export surface.

**Purpose of slim `__init__.py` files:**

**Define the public API**: The `__init__.py` file explicitly lists what is part of the public interface using the `__all__` list. This controls what gets imported with `from package import *`.

**Control exports**: Using `__all__` prevents internal implementation details from being accidentally exposed or depended upon by external code.

**Enable clean imports**: Users can import from the package name rather than internal modules. Instead of `from mail_client_api.client import Client`, users can do `from mail_client_api import Client`.

**Avoid side effects**: Minimal code means fewer surprises at import time. Heavy computation or I/O in `__init__.py` would run every time the package is imported, slowing down startup.

**Example Pattern for Source Packages:**

The `mail_client_api/__init__.py` contains only import statements and `__all__` definition. It imports classes and functions from internal modules and re-exports them. No functions or classes are defined in `__init__.py` itself. No complex logic or side effects occur on import.

**Example Pattern for Implementation Packages:**

The `gmail_client_impl/__init__.py` has slightly more logic but remains focused. It imports implementation classes and the registration functions. It defines a unified `register()` function that calls individual registration functions. It calls `register()` at module level to trigger dependency injection. A comment explicitly notes "Dependency Injection happens at import time" making the side effect intentional and documented.

**Convention for Test Directory `__init__.py` Files:**

Test directories include `__init__.py` files that are typically completely empty. No imports, no exports, no code.

**Why empty `__init__.py` in test directories:**

**Package recognition**: Marks the directory as a package so pytest can discover it.

**Import support**: Allows tests to import from each other if needed (though this is rare and usually indicates tests shouldn't be structured that way).

**No exports needed**: Tests are not imported by other code, so there's no public API to define.

**Simplicity**: Empty files are easier to maintain and have no side effects.

**Contributors should follow this convention:**

- Keep source package `__init__.py` files slim with only imports and exports
- Keep test directory `__init__.py` files completely empty
- Never add business logic to `__init__.py` files
- Put implementation code in dedicated modules
- Only perform dependency injection registration in implementation package `__init__.py` files
- Document any module-level side effects with clear comments

### Import Guidelines

Consistent import practices make code easier to read, maintain, and refactor.

#### Relative vs. Absolute Imports

The project uses absolute imports consistently throughout.

**Absolute imports** are used everywhere:
- When importing from the same package
- When importing workspace dependencies
- When importing external libraries

**Example patterns used in this project:**

Within `mail_client_api`, the `client.py` module imports from the same package using the full package name: `from mail_client_api.message import Message`.

In `__init__.py` files, imports use the full package path: `from mail_client_api.client import Client, get_client`.

The `gmail_client_impl` imports its dependencies absolutely: `import mail_client_api` and `from mail_client_api import message`.

**Why avoid relative imports:**

The project consistently avoids relative imports with dots (like `from . import` or `from .. import`) because:
- Absolute imports make it explicit where code comes from
- They prevent confusion about import sources
- They work consistently across different contexts (tests, main code, interactive sessions)
- They support refactoring better (moving files doesn't break imports as easily)
- They make code more readable for new contributors

#### When to Use Each Import Style

**For importing from the same package**: Use absolute imports with the full package name.

**For importing workspace dependencies**: Use absolute imports.

**For importing external libraries**: Use absolute imports.

**For importing standard library**: Use absolute imports.

#### Import Organization

Within each file, imports are organized in three groups with blank lines between:

**Group 1: Standard library imports** - Built-in Python modules like `os`, `logging`, `pathlib`.

**Group 2: Third-party imports** - External libraries from PyPI like `google.auth` or `googleapiclient`.

**Group 3: Local imports** - Workspace packages and internal modules like `mail_client_api`.

Within each group, imports are sorted alphabetically. This organization makes it immediately clear which imports are external dependencies versus internal modules.

#### Import Best Practices

**Do:**
- Use absolute imports with full package names
- Import specific items: `from module import SpecificClass`
- Organize imports by standard library, third-party, local
- Keep imports at the top of the file (after the module docstring)
- Sort imports alphabetically within each group

**Don't:**
- Use wildcard imports (`from module import *`) except in `__init__.py` with proper `__all__`
- Use relative imports with dots (`.` or `..`)
- Import entire modules when you only need one class
- Hide imports inside functions (except for circular dependency resolution)
- Mix import styles inconsistently

## Testing Strategy

The project implements a comprehensive testing strategy designed to ensure code quality while maintaining fast development feedback cycles.

### Testing Philosophy

The project's testing approach is built on modern software engineering principles that emphasize building quality in from the start.

#### Quality Ownership: A Modern Approach

This project follows the **Modern Software Engineering** philosophy:

**Quality is everyone's responsibility**, not just a QA team's job. All development team members are accountable for quality. Every contributor is expected to write tests, review tests, and maintain test quality.

**Quality concerns are addressed continuously**, not at a separate testing phase. Quality is a primary engineering concern integrated into daily development work. Tests are written alongside production code, not as an afterthought.

**Collaboration is the work style**. Rather than developers and QA being in conflict, all parties work together toward quality goals. Code reviews include test review. Design discussions consider testability.

This stands in contrast to legacy approaches where a separate Quality Assurance team addressed quality only at the QA/Testing stage, often creating an adversarial relationship between development and testing.

#### The Core Principle: Quality is the Absence of Defects

**Quality is the absence of defects, not the presence of tests.**

Tests are a tool to improve software quality, but having many tests doesn't guarantee quality. The goal is to write tests that actually prevent defects and provide confidence in the system's correctness.

This means:
- Tests must verify meaningful behaviors, not just increase coverage percentages
- Each test should prevent a specific class of defects
- Tests should provide fast feedback when something breaks
- We measure quality through both internal and external metrics

#### Internal vs External Quality

**Internal Quality** is observable by software engineers and relates to the internal structure of the system. It's empirically measured by:
- Complexity of the code
- Coupling between components
- Cohesion within components
- Test coverage percentages

**External Quality** is observable by users and relates to how the system works at runtime. It's empirically measured by:
- Defect counts (number of bugs found)
- Defect density (bugs per lines of code or per feature)
- User-facing behavior correctness
- System reliability and performance

This project uses high test coverage (85%+) as a proxy for internal quality, which research shows correlates with reduced defect density (external quality).

#### The Test Pyramid: A Guiding Structure

This project follows the **Test Pyramid** pattern, which provides a balanced testing strategy.

The pyramid has three layers:

**Bottom Layer: Unit Tests** - The widest layer representing most of the tests:
- Most reliable and least flaky
- Least resource intensive
- Fastest to execute (milliseconds)
- Easiest to maintain
- Test individual components in isolation

**Middle Layer: Integration Tests** - A narrower layer with fewer tests:
- Necessary to verify component interactions
- Test how components work together
- More complex than unit tests
- Still reasonably fast and reliable
- Test the wiring and contracts between components

**Top Layer: End-to-End Tests** - The narrowest layer with fewest tests:
- Most fragile and prone to flakiness
- Most resource intensive
- Necessary for validating complete workflows
- Affected by environment instability
- Test the entire system from user perspective

**Avoid the Test Pyramid Anti-Pattern**: Don't invert the pyramid by having mostly E2E tests. While E2E tests are easiest to get started with (you don't need to think about components or mocking), they create a fragile test suite that's slow, unreliable, and hard to maintain.

Unit tests require more upfront design work (making code testable, identifying components, creating clean interfaces), but they provide a stable foundation for quality that enables rapid development.

#### The FIRST Principles: Properties Every Unit Test Must Have

Contributors should ensure every unit test follows the **FIRST** principles:

**Fast** - Tests must run in milliseconds. Mock all external dependencies (APIs, databases, filesystems). No network calls, no disk I/O in unit tests. Fast tests enable continuous test execution during development. If tests take seconds or minutes, developers won't run them frequently.

**Isolated** - Each test is independent of all other tests. Tests can run in any order. Tests don't share state. One test's failure doesn't cascade to others. Setup and teardown are performed within each test or in fixtures that run for each test.

**Repeatable** - If nothing changed, the test result must not change. No randomness, no dependency on current time, no dependency on external state. Deterministic behavior every time. Should pass in any environment (local, CI, different machines).

**Self-Verifying** - Every test must have assertions. The test clearly passes or fails without manual inspection. Use clear assertion messages to explain what's being verified. If you don't have an assert statement, you're not testing.

**Timely** - Write tests at the right time (just-in-time). Ideally write tests before or alongside production code. Don't wait until the end to add tests. Tests written early guide better design by forcing you to think about interfaces and dependencies.

#### The Arrange-Act-Assert Pattern

All tests in this project follow the **AAA pattern** for clarity and maintainability:

**Arrange**: Configure the subject of the test into the correct state. Set up test data, create mocks, configure the system. Everything needed for the test to run.

**Act**: Invoke the behavior being tested. Call the method, trigger the event, perform the action. This should be a single line or a small block.

**Assert**: Validate that the output matches expectations. Check return values, verify state changes, confirm method calls. Use clear assertion messages.

This structure makes tests easy to read and understand, even for developers unfamiliar with the codebase. Tests with clear AAA structure serve as documentation.

#### When to Modify Tests (and When NOT To)

Understanding when tests should change is crucial for maintaining a healthy test suite:

**When refactoring code - NO!**

Your existing tests don't need to change. Refactoring means improving structure without changing behavior. If tests start failing during refactoring, you're changing behavior, not structure. Tests act as a safety net to ensure refactoring preserves behavior.

Remember: **Refactoring does not change behavior!**

**When fixing a bug - NO!**

Existing tests don't need to change. A bug means you have a missing test. The correct process is:
1. Add a new test that reproduces the bug (it should fail)
2. Fix the bug (the new test should pass)
3. Existing tests remain unchanged

If existing tests need to change, it suggests they were testing implementation details rather than behavior.

**When adding a new feature - NO!**

Your existing tests don't need to change. Add new tests for the new feature. Existing functionality should continue to work as before. Existing tests verify that old behavior is preserved.

**The only time to modify existing tests** is when you're intentionally changing the behavior of the system. If tests need to change frequently, it's a sign they're testing implementation details rather than behaviors.

#### Writing Maintainable Tests

Contributors should follow these principles to write tests that enhance rather than hinder development velocity:

**1. Test via the Public API**

Test code the way users will interact with it. Don't test private methods or internal implementation details. Public API tests are resilient to refactoring. If you rename internal methods or restructure code, public API tests don't break.

Example: Test `client.get_messages()`, not internal helper methods that format data or parse responses.

**2. Test State, Not Method Invocations**

Verify outcomes and state changes, not that specific methods were called. Interaction tests are brittle and couple tests to implementation. If you verify that internal methods were called, refactoring breaks tests even when behavior is unchanged.

Example: Assert `result is True`, not `mock.some_internal_method.assert_called()`.

Exception: When the API interaction itself is the behavior being tested (like verifying Gmail API calls are made correctly), then interaction testing is appropriate.

**3. Test Behaviors, Not Methods**

A single method might exhibit multiple behaviors. Each behavior needs an independent test. Don't write one big test per method; write focused tests per behavior.

Example: `delete_message()` has different behaviors for:
- Successful deletion (returns True)
- Message not found (returns False)
- API error (returns False)
- Network failure (raises exception)

Each behavior gets its own test with a descriptive name.

**4. Write Complete and Concise Tests**

Everything a reader needs to understand the test is in the test itself. No unnecessary details that distract from the behavior being tested. Test names clearly describe what's being tested and the expected outcome. Use descriptive variable names: `invalid_message_id` instead of `id1`.

Tests should be readable as documentation. A new contributor should be able to understand what the code does by reading the tests.

**5. Don't Put Logic in Tests**

Tests should be obviously correct without thinking. No conditionals, loops, or complex calculations in test code. If your test needs tests, it's too complex. Keep tests simple and linear.

Test code should be simpler than production code. If you're debugging test logic, the test is too complex.

**6. Write Clear Failure Messages**

Use custom assertion messages when behavior isn't obvious. Give clues about why the test failed. Good failure messages reduce debugging time. When tests fail in CI, clear messages help diagnose issues without local reproduction.

Example: `assert result is True, f"Failed to delete message {message_id}, API returned error: {error}"`

#### Test-Driven Development (TDD) and Evidence

While this project doesn't mandate TDD, contributors should be aware of the evidence supporting it:

**The TDD Cycle consists of three steps:**

1. **Red**: Write a failing test first
2. **Green**: Write minimal code to make it pass
3. **Refactor**: Improve structure without changing behavior

**Research Evidence from Industry:**

**Microsoft**: Teams using TDD saw significant improvement in defect density, though managers estimated 15-35% longer development time initially.

**IBM**: TDD projects had 0.61 times the defects of non-TDD projects (a 39% reduction), with 15-20% longer development time.

**Meta-analysis across studies**: 76% of studies show positive results on internal quality. 88% show improvement in external quality.

**Key Insight**: The debate about test-first vs. test-last is less important than small, consistent iterations with high granularity and uniformity. Write tests early and often, whether before or alongside code.

**Code Coverage Levels**: Research shows defect rates are reduced more at higher code coverage levels (80-100%). However, attaining very high coverage (90%+) is more time consuming, which is why this project sets the threshold at 85% as a balance between quality and efficiency.

### Test Organization

Tests are organized by abstraction level and location in the repository:

#### Unit Tests

Unit tests live within each component's directory: `src/*/tests/`

**Location:**
- `src/mail_client_api/tests/`: Tests for the API abstraction
- `src/gmail_client_impl/tests/`: Tests for Gmail implementation

**Characteristics:**
- Fast execution (milliseconds per test)
- No external dependencies (all mocked)
- Test individual methods or classes
- Can run independently per component
- Marked with `@pytest.mark.unit` when needed

**What they test:**
- Contract verification (that interfaces are correctly defined)
- Implementation logic (that concrete classes work correctly)
- Error handling (that edge cases are handled)
- Input validation (that parameters are checked)

#### Integration Tests

Integration tests verify that components work correctly together: `tests/integration/`

**Characteristics:**
- Medium execution speed (seconds per test)
- Test interactions between components
- May make real API calls with test credentials
- Marked with `@pytest.mark.integration`
- Test dependency injection and component wiring

**What they test:**
- Dependency injection works correctly
- Components communicate properly
- Factory functions return correct implementations
- Authentication flows work end-to-end

#### End-to-End Tests

E2E tests validate complete workflows from the user's perspective: `tests/e2e/`

**Characteristics:**
- Slowest execution (seconds to minutes)
- Test complete user workflows
- Use real systems and APIs
- Marked with `@pytest.mark.e2e`
- Verify the entire application works as expected

**What they test:**
- Complete user workflows (authenticate, fetch, modify, delete)
- Application entry points work correctly
- All components integrate properly in real scenarios

#### Convention for Test Directory `__init__.py`

All test directories contain empty `__init__.py` files with no content.

**Reasoning:**

**pytest discovery**: Marks directories as packages so pytest can find tests.

**No exports needed**: Tests aren't imported by application code, so there's no public API to define.

**Simplicity**: Empty files have no side effects or maintenance burden.

**Isolation**: Tests should be independent, not importing from each other. Empty `__init__.py` discourages inappropriate test interdependencies.

### Test Abstraction Levels

Tests operate at different levels of abstraction:

**Level 1: Contract/Interface Testing**

Tests verify that abstract contracts are correctly defined. They use mocks conforming to interfaces to demonstrate expected usage. These tests in `src/mail_client_api/tests/` document how the interface should be used.

Purpose: Demonstrate interface usage and expected behavior.

**Level 2: Implementation Testing**

Tests verify that concrete implementations correctly fulfill contracts. They mock external dependencies (Gmail API) but test real implementation logic. These tests in `src/gmail_client_impl/tests/` ensure the Gmail integration works correctly.

Purpose: Verify implementation logic with mocked external dependencies.

**Level 3: Integration Testing**

Tests verify that components work together. They test dependency injection, factory replacement, and component interactions. These tests in `tests/integration/` ensure the wiring is correct.

Purpose: Verify component wiring and interactions.

**Level 4: End-to-End Testing**

Tests verify complete user workflows. They use real systems with minimal mocking. These tests in `tests/e2e/` validate the entire application works from the user's perspective.

Purpose: Verify complete system behavior.

### Code Coverage

Code coverage is tracked and enforced to ensure tests thoroughly exercise the codebase.

#### Coverage Tool

The project uses **pytest-cov**, a pytest plugin that integrates the Coverage.py tool. It's installed as a development dependency via `uv sync --extra dev`.

#### Coverage Configuration

Coverage is configured in the root `pyproject.toml`:

**Source specification**: Measure coverage only for code in the `src/` directory.

**Omissions**: Don't measure coverage for test code itself or entry point files.

**Threshold**: Tests fail if coverage drops below 85%.

**Exclusions**: Lines matching certain patterns don't count toward coverage:
- Pragma comments: `# pragma: no cover`
- Abstract methods: `raise NotImplementedError`
- Type-checking-only imports: `if TYPE_CHECKING:`

#### Minimum Coverage Thresholds

The project enforces a **minimum of 85% code coverage** for these reasons:

**Quality assurance**: High coverage ensures most code paths are tested, reducing the likelihood of untested bugs.

**Confidence in changes**: Contributors can refactor knowing tests will catch regressions. Changes to covered code trigger test failures if behavior changes.

**Documentation**: Tests serve as executable documentation. High coverage means comprehensive docs.

**Deliberate uncovered code**: The 85% threshold allows for some untested edge cases (like rare error handling paths) while requiring justification. Code below threshold requires explanation or additional tests.

Research shows defect rates decrease more at coverage levels of 80-100%, with diminishing returns above 90%. The 85% threshold balances quality with practicality.

**What counts toward coverage:**
- All production code in `src/` directories
- Only lines that can actually be executed

**What doesn't count:**
- Test code itself
- Abstract methods that raise `NotImplementedError`
- Type-checking-only imports
- Lines marked with `# pragma: no cover`

#### Running Tests with Coverage

**Run all tests with coverage report:**
Command: `uv run pytest --cov=src --cov-report=term-missing`

This runs all tests (unit, integration, e2e) and displays a terminal report showing coverage percentages and listing uncovered lines.

**Run only unit tests with coverage:**
Command: `uv run pytest src/ --cov=src --cov-report=term-missing`

This runs only the unit tests from component directories, which should be sufficient for validating coverage during development.

**Run with coverage threshold enforcement:**
Command: `uv run pytest --cov=src --cov-report=term-missing --cov-fail-under=85`

This explicitly fails the test run if coverage is below 85%, though this is also configured in `pyproject.toml`.

**Run tests excluding those requiring local credentials:**
Command: `uv run pytest src/ tests/ -m "not local_credentials" -v`

This is the recommended command for CI/CD environments where credential files aren't available.

#### Generating Coverage Reports

**Terminal report (default):**
Command: `uv run pytest --cov=src --cov-report=term-missing`

Output shows coverage percentages and lists uncovered lines for each file. This is useful for quick checks during development.

**HTML report (detailed, browsable):**
Command: `uv run pytest --cov=src --cov-report=html`

This generates `htmlcov/index.html` which you can open in a browser to see line-by-line coverage highlighting. Red lines are uncovered, green lines are covered. This is useful for deep-dive coverage analysis.

**XML report (for CI tools):**
Command: `uv run pytest --cov=src --cov-report=xml`

This generates `coverage.xml` used by CircleCI and other CI tools for reporting and tracking coverage over time.

**Combined reports:**
Command: `uv run pytest --cov=src --cov-report=term-missing --cov-report=html --cov-report=xml`

Generates all three report types simultaneously, useful for CI pipelines that both display results and store artifacts.

## Development Tools

The project uses a modern, integrated toolchain to maintain code quality and streamline development workflows.

### Workspace Management

The project uses **uv** (a fast Python package manager) to manage a multi-component workspace.

#### What is a uv Workspace?

A uv workspace is a monorepo structure where multiple Python packages are developed together in a single repository. The workspace:
- Shares a single virtual environment (`.venv/`)
- Resolves dependencies across all components together
- Locks dependencies in a single `uv.lock` file
- Allows components to depend on each other

This is defined in the root `pyproject.toml` in the `[tool.uv.workspace]` section listing member packages.

#### Essential uv Commands

**Initial setup (one-time):**

Install uv:
- macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Windows: `irm https://astral.sh/uv/install.ps1 | iex`

Create virtual environment and install all dependencies:
Command: `uv sync --all-packages --extra dev`

This command:
- Creates a `.venv/` directory with a Python virtual environment
- Installs all workspace member packages in editable mode
- Installs all dependencies from `uv.lock`
- Installs optional development dependencies

**Activate the virtual environment:**

macOS/Linux: `source .venv/bin/activate`

Windows PowerShell: `.venv\Scripts\Activate.ps1`

Once activated, you can use `python`, `pytest`, `ruff`, etc., directly without `uv run` prefix.

**Add a new dependency to a component:**

Add to specific component: `uv add --package gmail-client-impl google-api-python-client`

Add to root dev dependencies: `uv add --dev pytest-asyncio`

**Update dependencies:**

Update all dependencies: `uv sync --upgrade`

Update specific package: `uv add --package gmail-client-impl google-api-python-client --upgrade`

**Run commands without activating venv:**

Run pytest: `uv run pytest`

Run ruff: `uv run ruff check .`

Run mypy: `uv run mypy src tests`

The `uv run` prefix automatically uses the virtual environment without requiring activation.

**Show installed packages:**

Show dependency tree: `uv tree`

Show top-level packages: `uv pip list`

**Lock dependencies:**

Command: `uv lock`

Updates `uv.lock` after manual `pyproject.toml` changes. Usually automatic when using `uv add` or `uv sync`.

#### Root vs. Component pyproject.toml Roles

**Root `pyproject.toml` is responsible for:**
- Defining the workspace and its members
- Declaring development tools (pytest, ruff, mypy, mkdocs)
- Configuring tools that apply to the whole workspace
- Defining workspace-wide settings (coverage thresholds, Python version)
- Providing shared configuration that components inherit

When you run `uv sync --extra dev` at the root, it installs all workspace members in editable mode, installs all development tools, resolves dependencies across the entire workspace, and creates a unified virtual environment.

**Component `pyproject.toml` files are responsible for:**
- Declaring the component's metadata (name, version, description)
- Listing the component's runtime dependencies
- Specifying how the component should be built/packaged
- Defining component-specific tool overrides if needed
- Declaring workspace dependencies on other components

Components declare dependencies on other workspace members using `[tool.uv.sources]` to indicate workspace resolution.

**Key difference**: The root manages the development environment and tooling; components manage their own dependencies and metadata.

### Static Analysis and Code Formatting

The project uses **Ruff** for both static analysis (linting) and code formatting, plus **MyPy** for static type checking.

#### What Tools Are Used?

**Ruff** serves two purposes:

1. **Linter**: Checks code for errors, style violations, and potential bugs. Replaces Flake8, isort, pyupgrade, and many other tools.

2. **Formatter**: Automatically formats code to a consistent style. Replaces Black.

Ruff is extremely fast (written in Rust) and provides comprehensive checking with hundreds of rules.

**MyPy** is used separately for static type checking:
- Verifies type hints are correct
- Catches type-related errors before runtime
- Enforces strict type checking as configured in `pyproject.toml`

#### Why These Tools Are Important

**Code Quality**: Static analysis catches bugs before they reach production, including unused variables (might indicate logic errors), undefined names (will cause runtime errors), and incorrect type usage.

**Consistency**: Automated formatting ensures all code follows the same style, enabling easy code reviews (no debates about formatting), easier collaboration (everyone's code looks the same), and reduced cognitive load (familiar style everywhere).

**Maintainability**: Linting enforces best practices including proper error handling, security considerations (hardcoded secrets, SQL injection risks), and documentation requirements (docstrings).

**Fast Feedback**: Running these tools locally before committing catches issues immediately, prevents CI failures, and speeds up development iteration.

#### Integration with uv

Ruff and mypy are integrated with uv as development dependencies. They're installed when you run `uv sync --extra dev`.

Both tools can be run through `uv run` or directly if the virtual environment is activated.

#### Running Static Analysis and Code Formatting

**Check code for linting issues:**
Command: `uv run ruff check .`

This runs Ruff's linter on all Python files, reporting errors and warnings.

**Automatically fix linting issues:**
Command: `uv run ruff check . --fix`

This fixes auto-fixable issues (import sorting, unused imports, simple style violations).

**Check code formatting:**
Command: `uv run ruff format --check .`

This checks if code is formatted correctly without making changes. Exits with an error code if formatting is needed.

**Apply code formatting:**
Command: `uv run ruff format .`

This automatically reformats all Python files to match the project's style.

**Run static type checking:**
Command: `uv run mypy src tests`

This runs mypy on the source and test directories, reporting type errors.

**Recommended workflow before committing:**

1. Check linting: `uv run ruff check .`
2. Fix auto-fixable issues: `uv run ruff check . --fix`
3. Format code: `uv run ruff format .`
4. Type check: `uv run mypy src tests`
5. Run tests: `uv run pytest`

#### Configuration

**Ruff configuration** is in the root `pyproject.toml`:

Settings include line length of 130 (longer than Black's default to accommodate complex code), target Python version 3.11, and comprehensive rule selection.

The `select = ["ALL"]` enables all Ruff rules by default for aggressive linting. Specific rules are disabled project-wide where they conflict or don't apply.

Per-file ignores relax rules for test files since tests don't need full type annotations and can use asserts freely.

**MyPy configuration** is also in the root `pyproject.toml`:

Settings include strict mode enabled (all strict rules on), explicit package bases (required for src layout), and mypy paths pointing to package source directories.

### Documentation Generation

The project uses **MkDocs** with the **Material theme** to generate static HTML documentation from Markdown files.

#### What Tool Is Used?

**MkDocs** is a static site generator specifically designed for project documentation. It:
- Converts Markdown files to HTML
- Provides a clean, searchable documentation site
- Supports code syntax highlighting
- Offers automatic navigation generation

**Material for MkDocs** is a modern theme providing:
- Responsive design (works on mobile)
- Dark/light mode toggle
- Built-in search functionality
- Better styling and user experience

**mkdocstrings-python** is a plugin that automatically generates API documentation from Python docstrings, extracting docstrings from classes and methods and rendering them as formatted documentation.

#### How to Use It

**View documentation locally:**
Command: `uv run mkdocs serve`

This starts a local development server at `http://127.0.0.1:8000` with live reloading. Edit Markdown files in `docs/`, and the browser automatically updates.

**Build static documentation:**
Command: `uv run mkdocs build`

This generates static HTML files in the `site/` directory that can be deployed to any web server or hosting platform.

**Configuration:**

Documentation is configured in `mkdocs.yml` at the repository root. The configuration includes:
- Site name and description
- Theme (Material) with light/dark mode
- Navigation structure mapping URLs to Markdown files
- Plugins (mkdocstrings for API docs)
- Python source paths for auto-documentation
- Markdown extensions for code highlighting

**Adding new documentation:**

1. Create a Markdown file in the `docs/` directory
2. Add it to the `nav` section in `mkdocs.yml`
3. Run `mkdocs serve` to preview
4. Commit both the Markdown file and updated `mkdocs.yml`

**Documenting API:**

MkDocs can auto-generate API docs from Python docstrings. In a Markdown file, use the special syntax with triple colons and the module path. This automatically extracts docstrings and renders them with formatting.

### CI: Continuous Integration

The project uses **CircleCI** for continuous integration and continuous delivery. The pipeline automatically tests, lints, and validates every commit.

#### CI Pipeline Jobs

The CI pipeline is defined in `.circleci/config.yml` and consists of six jobs:

**Job 1: build**

**Purpose**: Set up the environment and install all dependencies.

**What it does**:
- Checks out the repository
- Installs uv package manager
- Creates a virtual environment
- Installs all workspace packages and dev dependencies via `uv sync`
- Verifies installation by checking tool versions
- Persists the entire workspace including `.venv/` for subsequent jobs

**Job 2: lint**

**Purpose**: Check code quality and style.

**What it does**:
- Attaches the workspace from the build job
- Runs `ruff check .` to check for linting issues
- Fails if any linting errors are found

**Job 3: unit_test**

**Purpose**: Run fast, isolated unit tests with coverage.

**What it does**:
- Runs all unit tests from `src/` directories
- Measures code coverage with pytest-cov
- Runs mypy for static type checking
- Fails if coverage is below 85%
- Stores test results and coverage reports as artifacts

**Job 4: circleci_test**

**Purpose**: Run all tests except those requiring local credential files.

**What it does**:
- Runs tests from both `src/` and `tests/` directories
- Uses environment variables for authentication (no local files needed)
- Includes unit, integration, and E2E tests that work in CI
- Excludes tests marked with `@pytest.mark.local_credentials`
- Verifies the complete system works in CI environment

**Job 5: integration_test**

**Purpose**: Run integration tests with real Gmail API calls.

**What it does**:
- Runs tests marked with `@pytest.mark.integration`
- Makes real API calls to Gmail using credentials from CircleCI context
- Verifies that components work together with real external systems
- Only runs on protected branches (main, develop)

**Job 6: report_summary**

**Purpose**: Generate a summary of test results.

**What it does**:
- Collects results from all test jobs
- Summarizes test counts, failures, and coverage
- Provides a single place to see overall build health
- Useful for quick assessment of build status

#### What Triggers CI Jobs

**On all branches (feature branches, PRs):**

Workflow includes: build → lint, build → unit_test → circleci_test → report_summary

This provides fast feedback without expensive integration tests.

**On main and develop branches only:**

Workflow includes: build → lint, build → unit_test → circleci_test → integration_test → report_summary

This includes full integration tests with real API calls.

**Triggers:**
- Every `git push` to any branch
- Every commit to a pull request
- Manual re-run through CircleCI UI

#### Branch-Specific Workflows

The configuration defines two workflows:

**Workflow 1: `build_and_test`**

Runs on all branches except main and develop. Includes build, lint, unit_test, circleci_test, and report_summary. Skips integration tests to provide fast feedback on feature branches.

**Workflow 2: `full_integration`**

Runs only on main and develop branches. Includes all jobs including integration_test. Runs integration tests with real Gmail API calls. Uses CircleCI context for API credentials.

This approach ensures:
- Fast feedback on feature branches (no slow integration tests)
- Comprehensive testing on main branches (including real API calls)
- Credential security (API keys only available to protected branches)
- Cost efficiency (expensive tests only on important branches)

#### Environment Variables and Contexts

Integration tests require Gmail API credentials. These are configured in CircleCI:

**CircleCI Context**: A context named `gmail-client` contains environment variables including `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, and `GMAIL_REFRESH_TOKEN`.

The `integration_test` job specifies `context: gmail-client` to access these credentials. Tests use these environment variables for authentication, avoiding the need for local credential files in CI.

This ensures secrets are never committed to the repository and are only available to authorized CI jobs on protected branches.

---

## Getting Started

Ready to contribute? Here's how to get started:

**1. Clone the repository and set up the environment:**

```
git clone <repository-url>
cd ta-assignment
uv sync --all-packages --extra dev
source .venv/bin/activate
```

**2. Run tests to verify your setup:**

```
uv run pytest src/ tests/ -m "not local_credentials" -v
```

**3. Make changes and run checks before committing:**

```
uv run ruff format .
uv run ruff check .
uv run mypy src tests
uv run pytest
```

**4. View documentation:**

```
uv run mkdocs serve
```

**5. Push your changes and watch CI:**

CI will automatically run on your branch. Check CircleCI for test results and coverage.

For questions or issues, refer to the project README or open a GitHub issue.
