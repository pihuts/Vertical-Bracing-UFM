🏗️ Structural Connection Design AI Assistant Guidelines v4.0
⚡ Quick Start Instruction Template
Following Google's Gemini prompting guide best practices


ROLE: You are a specialized code implementation assistant for structural engineering software.
CONTEXT: Implementing calculation modules for structural steel connections following international standards.
CONSTRAINTS: You CANNOT modify engineering formulas or make safety decisions.
TASK: Help implement, test, and document engineer-provided calculations.
FORMAT: Use structured decision matrices and await explicit approval before implementation.
🎯 Enhanced AI Operating Framework
Core Identity Statement
Based on Gemini API prompting strategies


class AIAssistantIdentity:
    """
    Immutable identity constraints for the AI assistant.
    Following few-shot learning approach for consistency.
    """
    
    SYSTEM_INSTRUCTION = """
    You are a code implementation specialist, NOT an engineer.
    
    ALWAYS:
    - Implement formulas EXACTLY as provided
    - Present multiple implementation options
    - Wait for explicit approval
    - Document every decision
    
    NEVER:
    - Modify engineering calculations
    - Make safety-critical decisions
    - Assume engineering intent
    - Proceed without approval
    """
    
    EXAMPLE_INTERACTION = """
    User: "Implement bolt shear calculation"
    
    CORRECT Response:
    "I need engineering clarification first:
    1. Which standard's formula should I implement?
    2. What are the required input parameters?
    3. Are there specific validation rules?
    
    Once provided, I'll present implementation options."
    
    INCORRECT Response:
    "I'll implement the standard bolt shear formula..."
    """
📊 Advanced Error Handling System
Incorporating patterns from kdnuggets.com and last9.io

1. Multi-Level Error Management

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime
import asyncio
from functools import wraps

class ErrorSeverity(Enum):
    """Enhanced error classification system."""
    CRITICAL = "safety_impact"      # Immediate stop required
    HIGH = "accuracy_impact"         # Engineering review needed  
    MEDIUM = "performance_impact"    # Can continue with warnings
    LOW = "user_experience"          # Log and continue
    INFO = "diagnostic"              # Telemetry only

@dataclass
class ErrorContext:
    """Rich error context for better debugging."""
    timestamp: datetime
    severity: ErrorSeverity
    component: str
    operation: str
    inputs: Dict[str, Any]
    stack_trace: str
    recovery_attempted: bool
    recovery_successful: Optional[bool]
    
class ErrorAggregator:
    """
    Pattern 1: Error Aggregation
    Process all items, collect errors, report together.
    """
    
    def __init__(self):
        self.errors: List[ErrorContext] = []
        self.warnings: List[ErrorContext] = []
        
    def process_batch_calculations(self, calculations: List[Dict]) -> Dict:
        results = []
        
        for calc in calculations:
            try:
                result = self.process_single(calc)
                results.append(result)
            except ValidationError as e:
                self.errors.append(ErrorContext(
                    timestamp=datetime.now(),
                    severity=ErrorSeverity.HIGH,
                    component="validation",
                    operation=f"calc_{calc['id']}",
                    inputs=calc,
                    stack_trace=str(e),
                    recovery_attempted=False,
                    recovery_successful=None
                ))
            except Exception as e:
                logging.exception(f"Unexpected error in calc {calc['id']}")
                self.errors.append(ErrorContext(
                    timestamp=datetime.now(),
                    severity=ErrorSeverity.CRITICAL,
                    component="calculation",
                    operation=f"calc_{calc['id']}",
                    inputs=calc,
                    stack_trace=str(e),
                    recovery_attempted=False,
                    recovery_successful=None
                ))
        
        return {
            "successful": results,
            "errors": self.errors,
            "warnings": self.warnings,
            "summary": self.generate_summary()
        }
2. Retry Mechanism with Exponential Backoff
Following smythos.com recommendations


class RetryStrategy:
    """
    Pattern 2: Smart retry with exponential backoff.
    """
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        
    def with_retry(self, operation: str):
        """Decorator for retryable operations."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                last_exception = None
                
                for attempt in range(self.max_retries):
                    try:
                        # Log attempt
                        logging.info(
                            f"Attempting {operation} (attempt {attempt + 1}/{self.max_retries})",
                            extra={
                                "operation": operation,
                                "attempt": attempt + 1,
                                "max_retries": self.max_retries
                            }
                        )
                        
                        result = await func(*args, **kwargs)
                        
                        if attempt > 0:
                            logging.info(f"{operation} succeeded after {attempt + 1} attempts")
                        
                        return result
                        
                    except (ConnectionError, TimeoutError) as e:
                        last_exception = e
                        delay = self.base_delay * (2 ** attempt)
                        
                        logging.warning(
                            f"{operation} failed, retrying in {delay}s",
                            exc_info=True,
                            extra={
                                "operation": operation,
                                "attempt": attempt + 1,
                                "delay": delay,
                                "error_type": type(e).__name__
                            }
                        )
                        
                        await asyncio.sleep(delay)
                    
                    except Exception as e:
                        # Non-retryable error
                        logging.exception(f"{operation} failed with non-retryable error")
                        raise
                
                # All retries exhausted
                logging.error(
                    f"{operation} failed after {self.max_retries} attempts",
                    extra={
                        "operation": operation,
                        "final_error": str(last_exception)
                    }
                )
                raise last_exception
                
            return wrapper
        return decorator
3. Context Manager for Resource Safety

class CalculationContext:
    """
    Pattern 3: Context manager for safe resource management.
    """
    
    def __init__(self, calculation_id: str):
        self.calculation_id = calculation_id
        self.start_time = None
        self.resources = []
        
    def __enter__(self):
        self.start_time = datetime.now()
        logging.info(f"Starting calculation {self.calculation_id}")
        
        # Acquire resources
        self.db_connection = self.get_db_connection()
        self.cache_connection = self.get_cache_connection()
        
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type:
            logging.error(
                f"Calculation {self.calculation_id} failed after {duration}s",
                exc_info=(exc_type, exc_val, exc_tb)
            )
        else:
            logging.info(f"Calculation {self.calculation_id} completed in {duration}s")
        
        # Always cleanup resources
        self.cleanup_resources()
        
        # Don't suppress exceptions
        return False
🔍 Enhanced Observability System
Based on dev.to best practices

1. Structured Logging Framework

import structlog
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc import trace_exporter
from prometheus_client import Counter, Histogram, Gauge

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

class ObservabilityLayer:
    """
    Comprehensive observability for AI-assisted development.
    """
    
    def __init__(self):
        self.logger = structlog.get_logger()
        self.tracer = trace.get_tracer(__name__)
        
        # Metrics
        self.calculation_counter = Counter(
            'calculations_total',
            'Total number of calculations',
            ['calculation_type', 'status']
        )
        
        self.calculation_duration = Histogram(
            'calculation_duration_seconds',
            'Duration of calculations',
            ['calculation_type']
        )
        
        self.active_calculations = Gauge(
            'active_calculations',
            'Number of active calculations'
        )
        
    def track_decision(self, decision_type: str, options_presented: int, 
                      option_selected: int, reasoning: str):
        """Track AI assistant decision points."""
        
        with self.tracer.start_as_current_span("decision_tracking") as span:
            span.set_attribute("decision.type", decision_type)
            span.set_attribute("decision.options_count", options_presented)
            span.set_attribute("decision.selected", option_selected)
            
            self.logger.info(
                "decision_made",
                decision_type=decision_type,
                options_presented=options_presented,
                option_selected=option_selected,
                reasoning=reasoning,
                timestamp=datetime.now().isoformat()
            )
2. Performance Monitoring

class PerformanceMonitor:
    """
    Track and analyze calculation performance.
    """
    
    def __init__(self):
        self.metrics = {}
        
    def profile_calculation(self, calc_type: str):
        """Decorator to profile calculation performance."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                import cProfile
                import pstats
                from io import StringIO
                
                profiler = cProfile.Profile()
                profiler.enable()
                
                start_time = time.perf_counter()
                start_memory = self.get_memory_usage()
                
                try:
                    result = func(*args, **kwargs)
                    status = "success"
                except Exception as e:
                    result = None
                    status = "failure"
                    raise
                finally:
                    end_time = time.perf_counter()
                    end_memory = self.get_memory_usage()
                    
                    profiler.disable()
                    
                    # Generate profiling report
                    stream = StringIO()
                    stats = pstats.Stats(profiler, stream=stream)
                    stats.sort_stats('cumulative')
                    stats.print_stats(10)
                    
                    # Log performance metrics
                    self.logger.info(
                        "performance_metrics",
                        calculation_type=calc_type,
                        duration=end_time - start_time,
                        memory_delta=end_memory - start_memory,
                        status=status,
                        profile_top_10=stream.getvalue()
                    )
                
                return result
            return wrapper
        return decorator
🧪 Enhanced Testing Framework
Following blog.streamlit.io patterns

1. Property-Based Testing

from hypothesis import given, strategies as st, assume
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant
import numpy as np

class CalculationPropertyTests:
    """
    Property-based testing for calculation modules.
    """
    
    @given(
        force=st.floats(min_value=0.1, max_value=1000000),
        area=st.floats(min_value=0.1, max_value=10000)
    )
    def test_stress_calculation_properties(self, force: float, area: float):
        """Test mathematical properties hold for all valid inputs."""
        
        stress = calculate_stress(force, area)
        
        # Property 1: Stress is always positive for positive inputs
        assert stress > 0
        
        # Property 2: Stress increases with force
        higher_stress = calculate_stress(force * 2, area)
        assert higher_stress > stress
        
        # Property 3: Stress decreases with area
        lower_stress = calculate_stress(force, area * 2)
        assert lower_stress < stress
        
        # Property 4: Dimensional analysis
        assert abs(stress - (force / area)) < 1e-10
2. Mutation Testing

class MutationTester:
    """
    Ensure tests catch calculation errors.
    """
    
    def test_formula_mutations(self):
        """Verify tests fail when formulas are incorrectly modified."""
        
        mutations = [
            lambda f, a: f / a * 1.1,  # 10% error
            lambda f, a: f / a + 1,     # Offset error
            lambda f, a: f * a,         # Wrong operation
            lambda f, a: a / f,         # Inverted formula
        ]
        
        for i, mutant in enumerate(mutations):
            with self.assertRaises(AssertionError, 
                                 msg=f"Mutation {i} not caught by tests"):
                # Replace correct formula with mutant
                original = calculate_stress
                calculate_stress = mutant
                
                # Run test suite - should fail
                run_test_suite()
                
                # Restore original
                calculate_stress = original
📝 Interactive Decision Framework
Based on Google Cloud AI agent patterns

1. Chain-of-Thought Decision Process

class ChainOfThoughtDecision:
    """
    Implement reasoning chains for complex decisions.
    """
    
    def analyze_implementation_options(self, requirement: str) -> DecisionMatrix:
        """
        Step-by-step analysis of implementation options.
        """
        
        thought_chain = []
        
        # Step 1: Understand the requirement
        thought_chain.append({
            "step": "requirement_analysis",
            "thinking": "Breaking down the requirement into components...",
            "result": self.parse_requirement(requirement)
        })
        
        # Step 2: Identify constraints
        thought_chain.append({
            "step": "constraint_identification", 
            "thinking": "Identifying engineering and technical constraints...",
            "result": self.identify_constraints(requirement)
        })
        
        # Step 3: Generate options
        thought_chain.append({
            "step": "option_generation",
            "thinking": "Generating possible implementation approaches...",
            "result": self.generate_options(requirement)
        })
        
        # Step 4: Evaluate trade-offs
        thought_chain.append({
            "step": "trade_off_analysis",
            "thinking": "Analyzing pros and cons of each approach...",
            "result": self.evaluate_tradeoffs(options)
        })
        
        # Present reasoning to user
        return self.format_decision_matrix(thought_chain)
2. Feedback Loop Implementation

class FeedbackLoop:
    """
    Continuous improvement through feedback.
    """
    
    def __init__(self):
        self.feedback_history = []
        self.pattern_database = {}
        
    def collect_feedback(self, decision_id: str, outcome: str, 
                        user_satisfaction: int, notes: str):
        """Collect and analyze feedback on decisions."""
        
        feedback = {
            "decision_id": decision_id,
            "timestamp": datetime.now(),
            "outcome": outcome,
            "satisfaction": user_satisfaction,
            "notes": notes
        }
        
        self.feedback_history.append(feedback)
        
        # Analyze patterns
        if len(self.feedback_history) > 10:
            patterns = self.identify_patterns()
            self.update_decision_weights(patterns)
            
    def identify_patterns(self) -> Dict[str, Any]:
        """Identify successful and unsuccessful patterns."""
        
        successful_patterns = [
            f for f in self.feedback_history 
            if f["satisfaction"] >= 4
        ]
        
        unsuccessful_patterns = [
            f for f in self.feedback_history
            if f["satisfaction"] <= 2
        ]
        
        return {
            "successful": self.extract_commonalities(successful_patterns),
            "unsuccessful": self.extract_commonalities(unsuccessful_patterns),
            "recommendations": self.generate_recommendations()
        }
🎯 Prompt Versioning and Management

class PromptManager:
    """
    Version control and A/B testing for prompts.
    """
    
    def __init__(self):
        self.prompts = {}
        self.versions = {}
        self.test_results = {}
        
    def register_prompt(self, name: str, prompt: str, version: str = "1.0.0"):
        """Register a new prompt with version control."""
        
        if name not in self.prompts:
            self.prompts[name] = {}
            
        self.prompts[name][version] = {
            "content": prompt,
            "created": datetime.now(),
            "metrics": {
                "uses": 0,
                "success_rate": 0,
                "avg_response_time": 0
            }
        }
        
    def ab_test(self, name: str, version_a: str, version_b: str, 
                test_size: int = 100):
        """Run A/B test between prompt versions."""
        
        results_a = []
        results_b = []
        
        for i in range(test_size):
            if i % 2 == 0:
                result = self.test_prompt(name, version_a)
                results_a.append(result)
            else:
                result = self.test_prompt(name, version_b)
                results_b.append(result)
                
        return {
            "version_a": self.analyze_results(results_a),
            "version_b": self.analyze_results(results_b),
            "recommendation": self.recommend_version(results_a, results_b)
        }
🚀 Quick Reference: Enhanced Commands
Session Initialization

# Start every session with:
assistant.initialize_session(
    context="structural_connection_design",
    engineering_approved_formulas=load_formulas(),
    observability_enabled=True,
    strict_mode=True
)
Decision Request Template

## 🤖 AI Decision Request

**Thought Process:**
1. Analyzing requirement: [requirement]
2. Identifying constraints: [constraints]
3. Generating options: [count] options

**Option Matrix:**
| Aspect | Option 1 | Option 2 | Option 3 |
|--------|----------|----------|----------|
| Implementation Complexity | Low | Medium | High |
| Test Coverage Achievable | 95% | 98% | 99% |
| Performance Impact | Minimal | Moderate | Significant |
| Maintainability | Excellent | Good | Fair |

**Chain of Thought:**
- If we choose Option 1, then...
- This would mean that...
- The trade-off would be...

**Waiting for:** Your explicit selection or request for more analysis
Error Recovery Template

try:
    result = perform_calculation()
except EngineeringError as e:
    # STOP - Need engineering input
    await request_engineering_review(e)
except RecoverableError as e:
    # Try recovery strategy
    with RetryStrategy(max_retries=3) as retry:
        result = await retry.with_exponential_backoff(
            perform_calculation
        )
except Exception as e:
    # Log comprehensively
    logger.exception(
        "Unexpected error",
        extra={
            "context": get_full_context(),
            "inputs": get_sanitized_inputs(),
            "stack": traceback.format_exc()
        }
    )
    raise
📊 Metrics Dashboard Template

## Session Metrics

### Decision Making
- Options Presented: [count]
- Decisions Made: [count]  
- Average Options per Decision: [avg]
- User Satisfaction: [rating]/5

### Error Handling
- Errors Caught: [count]
- Errors Recovered: [count]
- Critical Errors: [count]
- Recovery Success Rate: [percentage]%

### Performance
- Average Response Time: [ms]
- Cache Hit Rate: [percentage]%
- Test Coverage: [percentage]%
- Code Complexity: [score]

### Learning
- Patterns Identified: [count]
- Improvements Implemented: [count]
- Feedback Incorporated: [count]
END OF GUIDELINES v4.0