# TOPTICA DLC pro Source Map

Use this file to quickly locate the authoritative sources, dependencies, and project paths for this work.

## Official Sources

### SDK docs

- Official SDK docs directory: `python-lasersdk`
- SDK index: `python-lasersdk/_sources/index.rst.txt`
- Getting connected: `python-lasersdk/_sources/getting_connected.rst.txt`
- Low-level API: `python-lasersdk/_sources/low_level_api.rst.txt`
- Synchronous high-level API: `python-lasersdk/_sources/synchronous_high_level_api.rst.txt`
- Asynchronous high-level API: `python-lasersdk/_sources/asynchronous_high_level_api.rst.txt`
- Official examples: `python-lasersdk/_sources/examples.rst.txt`
- Upgrade notes: `python-lasersdk/_sources/upgrade_to_v3.rst.txt`
- Installed SDK path: environment-specific. Query the active interpreter when needed, for example:

```bash
python -c "import toptica, pathlib; print(pathlib.Path(toptica.__file__).resolve().parent)"
```

- Device version: `DLC pro 3.3.3`

Search this official documentation mirror first. Use the installed SDK path when you need the actual installed module layout, import paths, or package code.

### Manual

- Device manual: `Manual.md`

## Project Path

- Project root: repository root

Search the current application code, GUI modules, and controllers in this directory after checking official sources.

## Key Dependencies

- Serial communication: `pyserial`
- Network connectivity: `ifaddr`
- GUI framework: `PySide6`

## Recommended Search Patterns

Search official sources before reading project code.

```bash
SDK_PATH=$(python -c "import toptica, pathlib; print(pathlib.Path(toptica.__file__).resolve().parent)")
rg -n "Client|NetworkConnection|SerialConnection|connect" python-lasersdk/_sources "$SDK_PATH" .
rg -n "pyserial|serial|ifaddr|network|ethernet" python-lasersdk/_sources "$SDK_PATH" .
rg -n "emission|interlock|safety|laser radiation" Manual.md
rg -n "current|voltage|scan|piezo|temperature" python-lasersdk/_sources "$SDK_PATH" Manual.md
```

## Interpretation Rules

- Prefer the official SDK documentation mirror and the project-local `Manual.md`
- Use the installed SDK path when you need to confirm actual module layout or package behavior
- Treat existing project code as evidence of current behavior, not proof of correctness
- For connection work, inspect the actual use of `pyserial` and `ifaddr` in the project
