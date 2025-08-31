# `handcalcs` Documentation

**Version**: 1.9.0  
**License**: Apache-2.0  
**Build Status**: Passing  
**Test Coverage**: 95%  

A comprehensive guide to `handcalcs`, a Python library for converting Python calculations into beautifully rendered LaTeX, as if written by hand.

---

## Table of Contents
1.  [Executive Summary](#1-executive-summary)
2.  [Quick Start (5-Minute Setup)](#2-quick-start-5-minute-setup)
3.  [Core Concepts](#3-core-concepts)
4.  [API Reference with Real-World Examples](#4-api-reference-with-real-world-examples)
5.  [Common Patterns & Best Practices](#5-common-patterns--best-practices)
6.  [Pitfalls & Things to Avoid](#6-pitfalls--things-to-avoid-the-war-stories-section)
7.  [Advanced Usage](#7-advanced-usage)
8.  [Troubleshooting Guide](#8-troubleshooting-guide)
9.  [Migration Guide](#9-migration-guide)
10. [FAQ](#10-faq-from-real-developer-questions)

---

### 1. Executive Summary

-   **Purpose**: `handcalcs` is a Python library that automatically renders Python calculations into LaTeX, formatted to mimic calculations written by hand.
-   **Key Benefits**:
    -   **Clarity and Verifiability**: Shows the symbolic formula, numeric substitution, and final result, making calculations transparent and easy to check.
    -   **Jupyter Integration**: Works seamlessly as a cell magic within Jupyter Notebook and Jupyter Lab.
    -   **Professional Reports**: Enables exporting notebooks to clean, professional-looking PDFs without showing the code cells.
    -   **Expressive Syntax**: Automatically handles subscripts, Greek letters, mathematical functions, and comments.
    -   **Flexible**: Can be used as a function decorator (`@handcalc()`) in non-Jupyter environments like Streamlit.
-   **Production Readiness**: Stable (v1.9.0) and widely adopted. Recommended for engineering reports, academic assignments, scientific documentation, and any scenario where calculation transparency is critical.

### 2. Quick Start (5-Minute Setup)

#### Installation

Install the core library via pip:
```bash
pip install handcalcs
```

To enable the optional "no-input" exporters for Jupyter, which hide code cells in exported documents:
```bash
pip install "handcalcs[exporters]"
```
> **Note**: As of v1.9.0, these exporters are maintained separately at [nb-hideinputs](https://github.com/connorferster/nb-hideinputs).

#### Minimal Working Example

In a Jupyter Notebook cell:

```python
# 1. First, import the renderers
import handcalcs.render
from math import sqrt

# 2. Then, use the %%render magic in a new cell
%%render

# Your Python code goes here
a = 2
b = 3
c = sqrt(a**2 + b**2)
```

#### Expected Output

The cell will display the following beautifully rendered LaTeX:

$$
\begin{aligned}
a &= 2 \;
\\[10pt]
b &= 3 \;
\\[10pt]
c &= \sqrt{ a^{2} + b^{2} } = \sqrt{ 2^{2} + 3^{2} } = 3.606 \;
\end{aligned}
$$

### 3. Core Concepts

The mental model behind `handcalcs` is simple: **write Python, see math**.

It parses your Python code line by line and converts it into a LaTeX representation that follows the classic "formula -> substitution -> result" pattern. This bridges the gap between executable code and traditional mathematical notation, giving you the best of both worlds: the power and reproducibility of code, and the clarity of a handwritten calculation.

-   **Cell Magic (`%%render`)**: The primary way to use `handcalcs` in Jupyter. It transforms the entire cell's Python code into a rendered output.
-   **Decorator (`@handcalc()`)**: A wrapper for Python functions that enables `handcalcs` to render the operations within the function. This is useful for programmatic rendering and integration with web apps.
-   **Symbolic Representation**: Variable names are treated as symbols. `_` creates subscripts (e.g., `F_x` becomes $F_x$), and names of Greek letters are converted to their symbols (e.g., `alpha` becomes $\alpha$).

### 4. API Reference with Real-World Examples

#### `%%render` Cell Magic

-   **What it does**: Renders all the Python code in a Jupyter cell as LaTeX.
-   **When to use it**: The most common and direct way to use `handcalcs` for documenting calculations in a notebook.
-   **Code Example**:
    ```python
    %%render

    # Calculating the area of a circle
    from math import pi
    r = 15 # cm
    Area_circle = pi * r**2
    ```
    **Output**:
    $$
    \begin{aligned}
    r &= 15\ \textrm{cm} \;
    \\[10pt]
    \mathrm{Area}_{circle} &= \pi \cdot r^{2} = 3.142 \cdot 15^{2} = 706.858 \;
    \end{aligned}
    $$
-   **Parameters**: Accepts optional "override tags" (e.g., `%%render #long`, `%%render #params 2`) to control formatting and precision. See [Advanced Usage](#7-advanced-usage) for more.

#### `@handcalc()` Decorator

-   **What it does**: A decorator that wraps a Python function, capturing the calculations within and returning a tuple of `(latex_string, locals_dictionary)`.
-   **When to use it**: For programmatic use, generating LaTeX strings dynamically, or integrating `handcalcs` into other applications like Streamlit or Flask.
-   **Code Example**:
    ```python
    from handcalcs.decorator import handcalc
    from math import sin, radians

    @handcalc(jupyter_display=True)
    def calculate_projectile_range(v, theta):
        g = 9.81 # m/s^2
        theta_rad = radians(theta)
        R = (v**2 * sin(2 * theta_rad)) / g

    # Run the function to display the rendered output
    calculate_projectile_range(v=100, theta=45)
    ```
-   **Parameters**:
    -   `override: str`: Accepts override tags like `'params'`, `'long'`, etc.
    -   `precision: int`: Sets the decimal precision for the output.
    -   `jupyter_display: bool`: If `True`, directly displays the rendered LaTeX in a Jupyter environment.
-   **Return Values**: By default, returns a tuple `(latex_code: str, locals: dict)`. If `jupyter_display=True`, it displays the output and returns only the `locals` dictionary.

### 5. Common Patterns & Best Practices

#### ✅ GOOD: Separate Inputs, Calculations, and Summaries

Organize your notebook into logical blocks. This improves readability and reduces the risk of errors when re-running cells.

```python
# Cell 1: Define Inputs
%%render #params
# Structural Beam Properties
L = 12 # m, length of the beam
w = 1.5 # kN/m, distributed load

# Cell 2: Perform Calculation
%%render
# Calculate maximum bending moment
M_max = (w * L**2) / 8

# Cell 3: Summarize Results
print(f"The maximum bending moment is {M_max:.2f} kNm.")
```
**Why this works**: Each cell has a single responsibility. If the inputs change, you only need to re-run the notebook from the top, and the flow is logical and easy to verify.

#### ❌ BAD: Re-using Variable Names Across Unrelated Calculations

`handcalcs` uses the notebook's global namespace. Re-using a common variable name like `x` or `temp` for different purposes can cause incorrect numeric substitutions if you run cells out of order.

```python
# Cell 1: First Calculation
%%render
x = 10
y = 2 * x # y is 20
```

```python
# Cell 2: A completely different calculation later in the notebook
%%render
F = 120 # N
x = 0.5 # m, lever arm
T = F * x # T is 60 Nm
```

**Why this fails**: If you go back and re-run Cell 1 *after* running Cell 2, `x` is now `0.5` in the notebook's memory. The calculation for `y` will incorrectly use `x=0.5`, resulting in `y=1.0`, but the rendered output will still show the code for `y = 2 * x`. This creates a silent error that is hard to debug. **Always use descriptive variable names.**

### 6. Pitfalls & Things to Avoid (The "War Stories" Section)

-   **Namespace Pollution**: As described above, running cells out of order with re-used variable names is the most common source of errors. **Recommendation**: Restart the kernel and run all cells from the top to ensure correctness.
-   **Overly Complex Single Lines**: `handcalcs` processes code line-by-line. Complex, multi-step logic on a single line (e.g., using semicolons) can render but may be hard to read. It's better to break it down.
-   **Unsupported Python**: `handcalcs` only renders a subset of Python. Multi-line statements like `for` loops, `if/else` blocks (though simple conditionals are supported), and function definitions will not render. Perform iterations in a non-rendered cell and display the final result in a `handcalcs` cell.
-   **Mutable Objects**: Be cautious when rendering calculations that involve mutable objects like lists. `handcalcs` may display the object's state at the time of rendering, which can be confusing if it changes later.

### 7. Advanced Usage

#### Configuration and Customization

-   **Override Tags**: Control cell rendering by adding a comment tag after `%%render`.
    -   `#params`: Renders variable assignments in columns, hiding calculations.
    -   `#long`: Forces every calculation to the multi-line format.
    -   `#short`: Forces every calculation to the single-line format.
    -   `#symbolic`: Shows the symbolic formula and result, skipping numeric substitution.
    -   `#sympy`: For use with `sympy` objects to handle substitution.
-   **Precision**: Control the number of decimal places by adding an integer: `%%render 4`.
-   **Global Config**: Set options for the entire session.
    ```python
    import handcalcs.render
    # Example: Change the decimal separator to a comma for European-style docs
    handcalcs.set_option("decimal_separator", ",")
    handcalcs.set_option("display_precision", 4)
    ```
-   **Custom Symbols**: Define custom LaTeX representations for your variables.
    ```python
    handcalcs.set_option("custom_symbols", {"V_dot": "\\dot{V}", "N_star": "N^{*}"})
    ```

#### Integration with Other Libraries

-   **Units Packages**: `handcalcs` works well with `pint` and `forallpeople` to handle calculations with units.
-   **Scipy**: Can render numeric integrations performed with `scipy.integrate.quad`.

### 8. Troubleshooting Guide

```
Problem: My code doesn't render and I see a Python error.
├── Check: Is the code valid Python syntax? handcalcs requires valid Python to work.
│   └── Solution: Fix the Python syntax error in the cell.
├── Check: Are you using an unsupported statement (e.g., a for loop)?
│   └── Solution: Perform the complex logic in a regular Python cell and use a %%render cell to display only the final, renderable calculation.

Problem: The rendered output shows the wrong numbers in the substitution.
├── Check: Have you used the same variable name elsewhere in the notebook (e.g., `x`)?
│   └── Solution: Use more descriptive variable names (e.g., `beam_length`).
├── Check: Did you run the cells out of order?
│   └── Solution: Click "Kernel" -> "Restart & Run All" to ensure a clean execution order.

Problem: I get a "NameError: name '%%render' is not defined".
├── Check: Did you run `import handcalcs.render` first?
│   └── Solution: Ensure the import cell is executed before any %%render cell.

Still stuck?
└── Check the official GitHub Issues for similar problems or open a new one: https://github.com/connorferster/handcalcs/issues
```

### 9. Migration Guide

#### From `nbconvert` Templates (pre-v1.9.0)

-   **Change**: In versions before 1.9.0, `handcalcs` installed custom `nbconvert` templates directly. Now, it uses a dedicated package for the "no-input" export feature.
-   **Action**: If you have an older installation, simply run `pip install --upgrade "handcalcs[exporters]"`. This will install the new, separate exporter package and ensure the "Save and Export as -> PDF_NoInput" options work correctly. No code changes are required.

### 10. FAQ (From Real Developer Questions)

-   **"Why does my calculation with a list or dictionary not render correctly?"**
    `handcalcs` has limited support for collection types. It cannot render `list` or `dict` literals. If you need to pass a sequence to a function like `sum()`, use a `tuple`, as it is rendered correctly: `sum((1, 2, 3))`. 1D `numpy` arrays are also supported.

-   **"How do I debug a complex calculation?"**
    Don't debug in a `%%render` cell. Write and debug your logic in a standard Python cell using `print()` statements. Once you have confirmed the logic is correct and produces the right values, move the final calculation steps to a `%%render` cell for documentation.

-   **"What's the difference between `%%render` and `%%tex`?"**
    -   `%%render` executes the Python code and displays the fully rendered output (formula, substitution, result) in Jupyter.
    -   `%%tex` does **not** execute the code. It only converts the Python code text into a raw LaTeX string. This is useful if you want to copy-paste the LaTeX into a separate document.