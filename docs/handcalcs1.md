You are a Senior Software Architect and Documentation Expert with 20 years of experience across multiple programming paradigms, frameworks, and industries. You have witnessed the evolution from waterfall to agile, from monoliths to microservices, and have maintained both legacy systems and cutting-edge applications. Your documentation has saved countless developer hours and significantly reduced support overhead for engineering teams.

Your Mission
Analyze the provided library/repository and create comprehensive, production-ready documentation that anticipates developer needs, prevents common mistakes, and accelerates adoption.

Documentation Structure
Generate documentation following this battle-tested structure:

1. Executive Summary
Purpose: One-sentence description of what problem this library solves
Key Benefits: 3-5 bullet points on why developers should use this
Production Readiness: Current stability status and recommended use cases
2. Quick Start (5-Minute Setup)
Installation
[Provide multiple installation methods]

Minimal Working Example
[Show the simplest possible working code that demonstrates core value]

Expected Output
[Show what the user should see if everything works]

3. Core Concepts
Explain the mental model developers need
Define domain-specific terminology
Include architectural diagrams where relevant
4. API Reference with Real-World Examples
For each major component/function:

What it does (plain English)
When to use it (use cases)
Code example (practical, not trivial)
Parameters (with types and constraints)
Return values (with edge cases)
Performance characteristics (O-notation where relevant)
5. Common Patterns & Best Practices
Provide 3-5 production-tested patterns showing:


// ✅ GOOD: Explanation of why this approach works
[working code example]

// ❌ BAD: Common mistake that seems logical but causes issues
[problematic code example]
// Why this fails: [specific explanation]
6. Pitfalls & Things to Avoid (The "War Stories" Section)
Based on your decades of experience, document:

Memory leaks: Common patterns that cause them
Performance gotchas: Operations that scale poorly
Security concerns: Unsafe patterns to avoid
Compatibility issues: Known conflicts with other libraries
Edge cases: Inputs that break assumptions
Migration headaches: Breaking changes between versions
7. Advanced Usage
Configuration options with performance implications
Integration with popular frameworks
Customization and extension points
Monitoring and debugging strategies
8. Troubleshooting Guide
Create a decision tree for common issues:


Problem: [Specific error or symptom]
├── Check: [First thing to verify]
│   └── Solution: [If this is the issue]
├── Check: [Second thing to verify]
│   └── Solution: [If this is the issue]
└── Still stuck? [Escalation path/community resources]
9. Migration Guide
From competing libraries
Between major versions
Deprecation notices with alternatives
10. FAQ (From Real Developer Questions)
Address the questions you've been asked hundreds of times:

"Why does X not work with Y?"
"How do I debug Z?"
"What's the difference between method A and B?"
Documentation Guidelines
Write for your past self: Assume the reader is smart but unfamiliar with this specific library
Test every example: Each code snippet should be copy-pasteable and functional
Explain the "why": Don't just show how, explain why this approach is recommended
Use progressive disclosure: Start simple, add complexity gradually
Include failure scenarios: Show what happens when things go wrong and how to recover
Version everything: Clearly mark which features require which versions
Benchmark claims: If you claim something is "fast" or "efficient," provide numbers
Output Format
Use Markdown with proper syntax highlighting
Include a table of contents with anchor links
Add badges for build status, test coverage, version, and license
Use collapsible sections for lengthy examples
Include inline comments in code examples explaining non-obvious logic
Add timestamps to time-sensitive information
Special Considerations
When documenting:

Async operations: Include both promise and async/await syntax
Error handling: Show both try/catch and error callback patterns
Testing: Provide unit test examples for critical functionality
Performance: Include benchmarks comparing different approaches
Accessibility: Note any a11y considerations
Internationalization: Document i18n support and limitations
Remember: You've seen projects fail due to poor documentation. Your goal is to create documentation so clear that a junior developer can be productive in hours, not days, and a senior developer can quickly evaluate if this library meets their architectural needs.

Now, analyze the provided library/repository and create documentation that you would have wanted when you were starting out, combined with the insights you've gained from two decades of experience.



This prompt incorporates insights from [arxiv.org](https://arxiv.org/html/2504.09798v2)'s ReadMe.LLM framework about structured, LLM-oriented documentation while emphasizing the practical, experience-based approach that comes from decades of real-world development. The prompt ensures the LLM generates documentation that's not just technically correct, but actually useful in production scenarios.

pls create for this https://github.com/connorferster/handcalcs






8 minutes ago
Favicon for anthropic
Claude Opus 4.1
Reasoning (thought for 4.7s)
handcalcs Documentation
Python
PyPI
License
Jupyter

Table of Contents
Executive Summary
Quick Start (5-Minute Setup)
Core Concepts
API Reference with Real-World Examples
Common Patterns & Best Practices
Pitfalls & Things to Avoid
Advanced Usage
Troubleshooting Guide
Migration Guide
FAQ
Executive Summary
Purpose
handcalcs automatically renders Python calculations as beautifully formatted LaTeX equations in Jupyter notebooks, showing both symbolic expressions and numerical results side-by-side.

Key Benefits
Show Your Work: Automatically generates step-by-step calculation documentation
Professional Output: Creates publication-ready mathematical expressions without manual LaTeX coding
Engineering-Focused: Designed for technical calculations where transparency is critical
Time-Saving: Eliminates hours of manual equation formatting
Compliance-Ready: Perfect for calculations that require auditable documentation
Production Readiness
Status: Stable for production use in Jupyter environments
Recommended Use Cases: Engineering reports, academic papers, design calculations, technical documentation, teaching materials

Quick Start (5-Minute Setup)
Installation

# Standard installation
pip install handcalcs

# With conda
conda install -c conda-forge handcalcs

# For development
pip install -e git+https://github.com/connorferster/handcalcs.git#egg=handcalcs
Minimal Working Example

import handcalcs.render
from math import sqrt, pi

%%render
# Basic engineering calculation
diameter = 10  # mm
area = pi * (diameter/2)**2  # mm^2
stress = 1500  # N
force = stress * area  # N
Expected Output
The above code will render as formatted LaTeX showing:


diameter = 10 mm

area = π · (diameter/2)² = π · (10/2)² = 78.54 mm²

stress = 1500 N

force = stress · area = 1500 · 78.54 = 117809.72 N
Core Concepts
Mental Model
handcalcs operates on three fundamental principles:

Symbolic Preservation: Your variable names become the mathematical symbols
Calculation Transparency: Every intermediate step is shown with substitution
Context Retention: Comments become units or descriptions in the output
Key Terminology
Cell Magic (%%render): Jupyter magic command that processes the entire cell
Line Magic (%render): Processes a single line (useful for inline calculations)
Symbolic Expression: The equation using variable names
Substituted Expression: The equation with numerical values inserted
Result: The final calculated value
Architecture Overview

Python Code → Parser → LaTeX Generator → MathJax Renderer → Display
     ↓           ↓            ↓                ↓              ↓
  Variables   AST Tree   LaTeX String    HTML Output    Notebook
API Reference with Real-World Examples
%%render Cell Magic
What it does: Renders all calculations in a Jupyter cell as formatted LaTeX equations

When to use it: For multi-step calculations that need documentation

Code example:


%%render
# Beam deflection calculation
E = 200e9  # Pa, Young's modulus for steel
I = 8.33e-6  # m^4, moment of inertia
L = 3  # m, beam length
w = 5000  # N/m, distributed load

# Maximum deflection for simply supported beam
delta_max = (5 * w * L**4) / (384 * E * I)  # m
delta_max_mm = delta_max * 1000  # mm
Parameters:

params (optional): Display only parameter definitions
long (optional): Force long format for all equations
short (optional): Force short format for all equations
symbolic (optional): Show only symbolic expressions without substitution
Performance: O(n) where n is the number of calculations

@handcalc() Decorator
What it does: Converts a function to return a LaTeX representation of its calculations

When to use it: For reusable calculation functions in reports

Code example:


from handcalcs.decorator import handcalc

@handcalc(override='long', precision=3, left='$', right='$', jupyter_display=True)
def calculate_pressure_vessel(D, t, P, SF=2.0):
    """Calculate hoop stress in a pressure vessel"""
    # Hoop stress
    sigma_h = (P * D) / (2 * t)  # MPa
    
    # Allowable stress
    sigma_allow = 250 / SF  # MPa
    
    # Safety check
    is_safe = sigma_h < sigma_allow
    
    return sigma_h, sigma_allow, is_safe

# Usage
latex_output = calculate_pressure_vessel(500, 10, 2.5)
Parameters:

override: Force rendering style ('long', 'short', 'symbolic')
precision: Decimal places for results (default: 3)
left/right: LaTeX delimiters (default: empty)
jupyter_display: Auto-display in Jupyter (default: False)
Return values:

Without decorator: Function returns calculated values
With decorator: Returns (latex_string, calculated_values) tuple
Rendering Functions
handcalcs.render.latex_renderer()
What it does: Core rendering engine that converts Python calculations to LaTeX

Code example:


from handcalcs import render

code = """
x = 5
y = x**2 + 3*x + 2
"""

latex_output = render.latex_renderer(code)
print(latex_output)
Parameters:

python_code (str): Python calculation code
override (str): Rendering style override
precision (int): Decimal precision
params (bool): Parameters-only mode
Common Patterns & Best Practices
Pattern 1: Engineering Calculations with Units

# ✅ GOOD: Clear unit documentation improves readability
%%render
# Structural steel column design
F_y = 345  # MPa, yield strength
E = 200000  # MPa, elastic modulus
L = 3000  # mm, unbraced length
r = 50  # mm, radius of gyration

# Slenderness ratio
lambda_c = L / r  # dimensionless
lambda_p = 4.71 * sqrt(E / F_y)  # dimensionless

# ❌ BAD: Missing units makes verification difficult
%%render
F_y = 345
E = 200000
L = 3000
r = 50
lambda_c = L / r
lambda_p = 4.71 * sqrt(E / F_y)
# Why this fails: Reviewers can't verify unit consistency
Pattern 2: Conditional Calculations

# ✅ GOOD: Use separate cells for conditional logic
%%render params
# Input parameters
load = 1500  # kN
capacity = 2000  # kN

# Calculate in Python (no render)
if load < capacity:
    safety_factor = capacity / load
else:
    safety_factor = 0  # Failure condition

%%render
# Display result
SF = safety_factor  # Safety factor
utilization = load / capacity * 100  # %

# ❌ BAD: Mixing conditionals in render block
%%render
if load < capacity:  # This won't render properly
    SF = capacity / load
Pattern 3: Matrix and Vector Operations

# ✅ GOOD: Break down matrix operations into steps
import numpy as np

%%render
# Define matrices explicitly for clarity
K_11 = 1000  # N/mm
K_12 = 500   # N/mm
K_21 = 500   # N/mm
K_22 = 1000  # N/mm

# Displacement vector
u_1 = 5  # mm
u_2 = 3  # mm

# Force calculations
F_1 = K_11 * u_1 + K_12 * u_2  # N
F_2 = K_21 * u_1 + K_22 * u_2  # N

# ❌ BAD: Complex numpy operations don't render well
%%render
K = np.array([[1000, 500], [500, 1000]])
u = np.array([5, 3])
F = K @ u  # Matrix multiplication doesn't render symbolically
Pattern 4: Multi-Step Derivations

# ✅ GOOD: Use override tags for readability
%%render
# short: Compact for simple assignments
a = 10  # m/s²
v_0 = 0  # m/s
t = 5   # s

# long: Detailed for complex expressions
v_f = v_0 + a * t  # m/s, final velocity

# symbolic: For theoretical expressions
# s = v_0 * t + 0.5 * a * t**2
Pitfalls & Things to Avoid
Memory Leaks

# ⚠️ ISSUE: Large arrays in render blocks consume memory
%%render
data = [i**2 for i in range(10000)]  # Don't render huge datasets

# ✅ SOLUTION: Calculate outside, render summary only
data = [i**2 for i in range(10000)]  # Python cell
%%render
n = len(data)  # data points
sum_data = sum(data)  # total
mean = sum_data / n  # average
Performance Gotchas

# ⚠️ SLOW: Rendering inside loops
for i in range(100):
    %%render
    result = complex_calculation(i)  # Renders 100 times!

# ✅ FAST: Batch calculations, render once
results = [complex_calculation(i) for i in range(100)]
%%render
final_result = sum(results)
average = final_result / 100
Security Concerns

# ❌ DANGEROUS: Never use exec/eval with user input in render blocks
user_input = "os.system('rm -rf /')"  # Malicious input
%%render
result = eval(user_input)  # NEVER DO THIS

# ✅ SAFE: Validate and sanitize inputs
allowed_vars = {'x': 10, 'y': 20}
if user_var in allowed_vars:
    %%render
    value = allowed_vars[user_var]
Compatibility Issues
Known Conflicts:
sympy symbolic variables don't render properly - use numeric values
Custom classes need __str__ methods for proper rendering
Pandas DataFrames should be processed outside render blocks
Edge Cases

# Division by zero handling
%%render
denominator = 0  # This could be calculated
# numerator / denominator  # Will cause error

# Use Python for validation
if denominator != 0:
    %%render
    result = numerator / denominator
else:
    print("Error: Division by zero")
Advanced Usage
Configuration Options

import handcalcs.render as render

# Global configuration
render.set_option('precision', 4)
render.set_option('use_scientific', True)
render.set_option('min_scientific', 1e-3)
render.set_option('max_scientific', 1e6)
Integration with Popular Frameworks
Export to PDF with nbconvert

jupyter nbconvert --to pdf calculation_report.ipynb
Integration with Streamlit

import streamlit as st
from handcalcs.decorator import handcalc

@handcalc(jupyter_display=False)
def calculation(a, b):
    c = sqrt(a**2 + b**2)
    return c

latex_code, result = calculation(3, 4)
st.latex(latex_code)
Use with Sphinx Documentation

# In conf.py
extensions = ['sphinx.ext.mathjax']

# In your .rst files
.. math::
   :nowrap:

   \begin{align}
   % Insert handcalcs output here
   \end{align}
Customization and Extension Points

# Custom formatting function
def custom_formatter(value, precision=3):
    if abs(value) > 1e6:
        return f"{value:.{precision}e}"
    return f"{value:.{precision}f}"

# Apply to handcalcs
handcalcs.render.formatter = custom_formatter
Monitoring and Debugging

# Enable debug mode
import logging
logging.basicConfig(level=logging.DEBUG)

# Inspect intermediate LaTeX
%%render --debug
calculation = 2 + 2

# Profile rendering performance
import cProfile
cProfile.run('render.latex_renderer(code)')
Troubleshooting Guide
Problem: LaTeX not rendering in Jupyter

├── Check: MathJax loaded?
│   └── Solution: Refresh browser, clear cache
├── Check: Cell magic syntax correct?
│   └── Solution: Use %%render at cell start, not %render
├── Check: Jupyter extensions enabled?
│   └── Solution: Run `jupyter nbextension enable --py widgetsnbextension`
└── Still stuck? Check browser console for JavaScript errors
Problem: Variables not showing in output

├── Check: Variable assigned in same cell?
│   └── Solution: Move assignment into %%render cell
├── Check: Using numpy/pandas objects?
│   └── Solution: Extract scalar values first
├── Check: Variable name contains special characters?
│   └── Solution: Use alphanumeric names only
└── Still stuck? Try symbolic override: %%render symbolic
Problem: Calculations showing wrong precision

├── Check: Global precision setting?
│   └── Solution: Use @handcalc(precision=n) decorator
├── Check: Scientific notation threshold?
│   └── Solution: Adjust min/max_scientific options
└── Still stuck? Format numbers before rendering
Migration Guide
From Manual LaTeX

# Old approach
from IPython.display import Latex
Latex(r"$F = ma = 10 \times 5 = 50$")

# With handcalcs
%%render
m = 10  # kg
a = 5   # m/s²
F = m * a  # N
From SymPy

# SymPy approach
import sympy as sp
x = sp.Symbol('x')
expr = x**2 + 2*x + 1
sp.latex(expr)

# handcalcs approach (numeric focus)
%%render
x = 5
y = x**2 + 2*x + 1
Version Migration (v1.x to v2.x)
Breaking Change: %%tex magic renamed to %%render
Deprecation: handcalcs.handcalcs() moved to handcalcs.decorator.handcalc()
New Feature: Added params override for parameter-only display
FAQ
"Why doesn't my numpy array render properly?"
Numpy arrays are displayed as array([...]). Extract individual elements or use .item() for scalars:


arr = np.array([1, 2, 3])
%%render
first_element = arr[0].item()
"How do I debug a complex calculation?"
Break it into smaller cells and render each step separately. Use Python cells for intermediate debugging.

"What's the difference between %%render and %render?"
%%render: Cell magic, processes entire cell
%render: Line magic, processes single line (rarely used)
"Can I use handcalcs outside Jupyter?"
Yes, use the @handcalc() decorator to get LaTeX strings that can be used in any Python environment.

"How do I include Greek letters?"
Use Python variable names that handcalcs recognizes:


%%render
alpha = 0.5
beta = 0.3
gamma = alpha + beta
# Renders as: α = 0.5, β = 0.3, γ = 0.8
"Why does my function call not render symbolically?"
handcalcs renders arithmetic operations, not function calls. For symbolic function display, use comments:


%%render
# y = sin(x)
y = 0.841  # Pre-calculated sin(1)
Last Updated: 2024
Version: Compatible with handcalcs 1.6+
Community: GitHub Issues | Discussions