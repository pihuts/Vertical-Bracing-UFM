# `forallpeople` Documentation

## Table of Contents
- [1. Executive Summary](#1-executive-summary)
- [2. Quick Start (5-Minute Setup)](#2-quick-start-5-minute-setup)
- [3. Core Concepts](#3-core-concepts)
- [4. API Reference with Real-World Examples](#4-api-reference-with-real-world-examples)
- [5. Common Patterns & Best Practices](#5-common-patterns--best-practices)
- [6. Pitfalls & Things to Avoid](#6-pitfalls--things-to-avoid)
- [7. Advanced Usage](#7-advanced-usage)
- [8. Troubleshooting Guide](#8-troubleshooting-guide)
- [9. Migration Guide](#9-migration-guide)
- [10. FAQ](#10-faq)

---

## 1. Executive Summary
- **Purpose**: `forallpeople` is a Python library that solves the problem of performing units-aware calculations within the International System of Units (SI) and other unit systems.
- **Key Benefits**:
    -   Simplifies calculations involving physical quantities by automatically handling unit conversions and reductions.
    -   Enhances code readability by making units an explicit part of calculations.
    -   Integrates seamlessly with popular data science libraries like `numpy` and `pandas`.
    -   Provides an intuitive experience in interactive environments like Jupyter notebooks.
    -   Reduces errors in scientific and engineering applications by enforcing dimensional consistency.
- **Production Readiness**: Stable and suitable for production use in scientific, engineering, and data analysis applications that require accurate and reliable handling of physical units.

---

## 2. Quick Start (5-Minute Setup)

### Installation
You can install `forallpeople` using `pip`:
```bash
pip install forallpeople
```

### Minimal Working Example
This example demonstrates how to calculate pressure from force and area.

```python
import forallpeople as si

# Load the default SI unit environment
si.environment('default')

# Define force and area
force = 2500 * si.N  # 2500 Newtons
area = 3 * si.m * 4 * si.m  # 12 square meters

# Calculate pressure
pressure = force / area

print(pressure)
```

### Expected Output
```
208.333 Pa
```

---

## 3. Core Concepts

### The `Physical` Object
The core of `forallpeople` is the `Physical` object. It represents a physical quantity and is composed of four components:
-   **value**: The numerical value of the quantity in SI base units.
-   **dimensions**: A vector representing the dimensions of the quantity (e.g., mass, length, time).
-   **factor**: A multiplier to convert the value to a different unit system (e.g., from meters to feet).
-   **precision**: The number of decimal places to display.

`Physical` objects are immutable, meaning any operation on them creates a new `Physical` object.

### Environments
Environments are JSON files that define the units available for calculations. `forallpeople` comes with a default environment that includes the SI base units and many derived units. You can also create your own custom environments.

### Automatic Unit Reduction and Prefixes
`forallpeople` automatically simplifies units during calculations. For example, dividing a force by an area results in a pressure. It also automatically applies SI prefixes (like kilo, mega, milli, micro) to make the output more readable.

---

## 4. API Reference with Real-World Examples

### `Physical` Class Properties

-   **`.value`**:
    -   **What it does**: Returns the numerical value of the quantity in SI base units as a `float`.
    -   **When to use it**: When you need to perform calculations with libraries that don't support `Physical` objects (e.g., `math.sqrt`).
    -   **Code example**:
        ```python
        import forallpeople as si
        import math
        si.environment('default')
        f_c = 35 * si.MPa
        # math.sqrt doesn't work directly on a Physical object
        # so we use .value
        sqrt_f_c_value = math.sqrt(f_c.value) 
        print(sqrt_f_c_value)
        ```
-   **`.dimensions`**:
    -   **What it does**: Returns a `Dimensions` object that describes the dimension of the quantity.
    -   **When to use it**: For debugging or creating custom functions that operate on specific dimensions.
-   **`.latex` and `.html`**:
    -   **What it does**: Returns a string representation of the quantity in LaTeX and HTML format, respectively.
    -   **When to use it**: For displaying quantities in reports or Jupyter notebooks.

### `Physical` Class Methods

-   **`.round(n)`**:
    -   **What it does**: Rounds the display precision of the `Physical` instance to `n` decimal places.
-   **`.sqrt(n)`**:
    -   **What it does**: Calculates the `n`-th root of the `Physical` instance.
-   **`.split()`**:
    -   **What it does**: Splits a `Physical` instance into its numerical value and its dimensional part.
    -   **When to use it**: Useful for operations in `numpy` that only accept numerical input.
-   **`.to(unit_name)`**:
    -   **What it does**: Converts the `Physical` instance to a different, dimensionally compatible unit.

---

## 5. Common Patterns & Best Practices

```python
import forallpeople as si
si.environment('default')

# ✅ GOOD: Let forallpeople handle unit conversions.
# This is clear, concise, and less error-prone.
force = 2.5 * si.kN
area = 12 * si.m**2
pressure = force / area
print(pressure) # Output: 208.333 Pa

# ❌ BAD: Manually converting units.
# This is verbose, error-prone, and defeats the purpose of the library.
force_N = 2500
area_m2 = 12
pressure_Pa = force_N / area_m2
print(pressure_Pa) # Output: 208.33333333333334
# Why this fails: While the result is numerically correct, it loses the unit information, 
# making it harder to track units through complex calculations.
```

---

## 6. Pitfalls & Things to Avoid

-   **Floor Division (`//`)**: Floor division is not implemented for `Physical` objects to avoid ambiguity. Use true division (`/`) and then `int()` if you need an integer result.
-   **Dimensionally Inconsistent Calculations**: Be careful with formulas that have "hidden dimensions". For example, in some engineering formulas, `sqrt(MPa)` results in `MPa`, not `MPa**0.5`. You need to manually account for this.
-   **Mutable Operations**: Remember that `Physical` objects are immutable. Operations that seem to modify them in-place (like `+=`) actually create a new object.

---

## 7. Advanced Usage

### Custom Environments
You can define your own units in a JSON file and load it as an environment. This is useful for domain-specific units or constants.

### Integration with `numpy`
`forallpeople` works well with `numpy` for vectorized operations on arrays of `Physical` objects.

```python
import numpy as np
import forallpeople as si
si.environment('default')

forces = np.array([1, 2, 3]) * si.kN
area = 2 * si.m**2
pressures = forces / area
print(pressures)```

---

## 8. Troubleshooting Guide

-   **Problem**: `TypeError: unsupported operand type(s) for +: 'Physical' and 'float'`
    -   **Check**: Are you trying to add a `Physical` object and a number without units?
    -   **Solution**: Multiply the number by the desired unit to convert it to a `Physical` object before adding.
-   **Problem**: `DimensionError: Dimensions are not equal`
    -   **Check**: Are you trying to add or subtract two `Physical` objects with different dimensions?
    -   **Solution**: Ensure that the dimensions of the two objects are compatible before performing the operation.

---

## 9. Migration Guide

### From `pint`
-   `forallpeople` has a more intuitive syntax for interactive use.
-   The concept of "environments" in `forallpeople` is similar to "unit registries" in `pint`.

---

## 10. FAQ

-   **"Why does `math.sqrt(35 * si.MPa)` not work as expected?"**
    -   Many functions in Python's `math` library first try to convert their arguments to a `float`. When `float()` is called on a `Physical` object, it returns the numerical value of the auto-prefixed representation (e.g., `35.0` for `35 * si.MPa`). The `sqrt` function then operates on this number, not the value in SI base units. To get the correct result, use `math.sqrt((35 * si.MPa).value)`.
-   **"What's the difference between `si.kg` and `si.g`?"**
    -   `si.kg` is a base SI unit. `si.g` is a derived unit. `forallpeople`'s auto-prefixing will automatically display values in the most appropriate prefix, so you will often see `g` or `mg` in outputs even if you only used `kg` in your inputs.