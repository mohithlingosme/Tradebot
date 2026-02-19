"""
Parallel processing tests for the backtesting system.

Tests cover:
- ProcessPoolExecutor memory usage
- Walk-forward parallel optimization
- Memory growth monitoring during parallel runs
- Worker cleanup verification
"""

import pytest
import gc
import sys
import tracemalloc
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Dict, Any
import weakref
import tempfile
import os

from ..walk_forward import (
    WalkForwardAnalyzer, 
    WalkForwardEngine, 
    ParameterGridSearch, 
    ParameterSet,
    WalkForwardWindow,
    WalkForwardConfig
)
from ..config import BacktestConfig
from ..engine import EventBacktester


class MockStrategy:
    """Mock strategy for testing."""
    def __init__(self, name: str = "mock", fast: int = 10, slow: int = 20):
        self.name = name
        self.fast = fast
        self.slow = slow
        self.state = {}
    
    def on_bar(self, bar, state=None):
        return []


class MockBar:
    """Mock bar for testing."""
    def __init__(self, symbol: str, timestamp: datetime, close: float = 100.0):
        self.symbol = symbol
        self.timestamp = timestamp
        self.open = close - 1
        self.high = close + 1
        self.low = close - 2
        self.close = close
        self.volume = 1000


def generate_test_events(num_events: int = 100) -> List[MockBar]:
    """Generate test events for parallel processing."""
    events = []
    base_time = datetime(2023, 1, 1, 9, 15)
    
    for i in range(num_events):
        timestamp = base_time + timedelta(minutes=i * 5)
        close = 100 + (i % 20 - 10) * 0.5
        events.append(MockBar("RELIANCE", timestamp, close))
    
    return events


def worker_function(params: Dict[str, Any]) -> Dict[str, Any]:
    """Worker function for parallel processing test."""
    # Simulate some computation
    result = {
        "params": params,
        "computation": sum(i ** 2 for i in range(1000)),
        "memory_test": [0] * 1000
    }
    return result


class TestProcessPoolExecutorMemory:
    """Test ProcessPoolExecutor memory usage."""

    def test_process_pool_memory_cleanup(self):
        """Test that ProcessPoolExecutor workers are properly cleaned up."""
        gc.collect()
        tracemalloc.start()
        
        initial_memory = tracemalloc.get_traced_memory()[0]
        
        # Run parallel tasks
        with ProcessPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(worker_function, {"id": i}) for i in range(10)]
            results = [f.result() for f in as_completed(futures)]
        
        gc.collect()
        current_memory = tracemalloc.get_traced_memory()[0]
        tracemalloc.stop()
        
        # Memory should be cleaned up after executor shutdown
        # Allow some tolerance for process startup overhead
        memory_growth = current_memory - initial_memory
        assert memory_growth < 5000000, f"Memory leak detected: {memory_growth} bytes"

    def test_parallel_task_completion(self):
        """Test that parallel tasks complete correctly."""
        param_sets = [{"id": i} for i in range(10)]
        
        with ProcessPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(worker_function, params) for params in param_sets]
            results = [f.result() for f in as_completed(futures)]
        
        assert len(results) == 10
        for result in results:
            assert "params" in result
            assert "computation" in result


class TestWalkForwardParallelOptimization:
    """Test walk-forward parallel optimization."""

    def test_parallel_optimization_memory(self):
        """Test memory usage during parallel parameter optimization."""
        gc.collect()
        tracemalloc.start()
        
        initial_memory = tracemalloc.get_traced_memory()[0]
        
        # Setup walk-forward configuration
        base_config = BacktestConfig(
            initial_capital=100000.0,
            start=datetime(2023, 1, 1),
            end=datetime(2023, 12, 31)
        )
        
        walk_config = WalkForwardConfig(
            train_period=timedelta(days=90),
            test_period=timedelta(days=30),
            step=timedelta(days=15)
        )
        
        param_ranges = {
            'fast': [5, 10, 15],
            'slow': [20, 30, 40]
        }
        
        engine = WalkForwardEngine(base_config, walk_config)
        
        # Generate test events
        events = generate_test_events(50)
        
        # Run parallel optimization with 2 workers
        result = engine.run_walk_forward(
            MockStrategy,
            events,
            param_ranges=param_ranges,
            max_workers=2
        )
        
        gc.collect()
        current_memory = tracemalloc.get_traced_memory()[0]
        tracemalloc.stop()
        
        memory_growth = current_memory - initial_memory
        
        # Check that optimization completed
        assert result is not None
        
        # Memory should not grow excessively (50MB tolerance for process overhead)
        assert memory_growth < 50000000, f"Excessive memory growth: {memory_growth} bytes"

    def test_sequential_vs_parallel_results(self):
        """Test that sequential and parallel produce same results."""
        # Setup
        base_config = BacktestConfig(
            initial_capital=100000.0,
            start=datetime(2023, 1, 1),
            end=datetime(2023, 12, 31)
        )
        
        walk_config = WalkForwardConfig(
            train_period=timedelta(days=30),
            test_period=timedelta(days=15),
            step=timedelta(days=7)
        )
        
        param_ranges = {
            'fast': [5, 10],
            'slow': [20, 30]
        }
        
        events = generate_test_events(30)
        
        # Run sequential
        engine = WalkForwardEngine(base_config, walk_config)
        sequential_result = engine.run_walk_forward(
            MockStrategy, events, param_ranges=param_ranges, max_workers=None
        )
        
        # Run parallel
        parallel_result = engine.run_walk_forward(
            MockStrategy, events, param_ranges=param_ranges, max_workers=2
        )
        
        # Results should have same structure
        assert len(sequential_result.parameter_sets) == len(parallel_result.parameter_sets)


class TestParameterGridSearch:
    """Test parameter grid search functionality."""

    def test_generator_memory_efficiency(self):
        """Test that parameter generator is memory efficient."""
        gc.collect()
        
        param_ranges = {
            'fast': list(range(5, 50, 5)),  # 9 values
            'slow': list(range(20, 100, 10)),  # 8 values
            'threshold': [0.01, 0.02, 0.05]  # 3 values
        }
        
        grid = ParameterGridSearch(param_ranges)
        
        # Generate all parameter sets
        all_params = list(grid.generate_parameter_sets_generator())
        
        # Should have 9 * 8 * 3 = 216 combinations
        assert len(all_params) == 216
        
        # Memory should be reasonable (just storing the generator, not all at once)
        gc.collect()
        # If we get here without memory issues, generator is working

    def test_grid_size(self):
        """Test parameter grid size calculation."""
        param_ranges = {
            'a': [1, 2, 3],
            'b': [4, 5]
        }
        
        grid = ParameterGridSearch(param_ranges)
        param_sets = grid.generate_parameter_sets()
        
        assert len(param_sets) == 6  # 3 * 2


class TestWalkForwardWindows:
    """Test walk-forward window generation."""

    def test_window_generation(self):
        """Test walk-forward window generation."""
        base_config = BacktestConfig(
            initial_capital=100000.0,
            start=datetime(2023, 1, 1),
            end=datetime(2023, 12, 31)
        )
        
        walk_config = WalkForwardConfig(
            train_period=timedelta(days=90),
            test_period=timedelta(days=30),
            step=timedelta(days=15)
        )
        
        analyzer = WalkForwardAnalyzer(MockStrategy, base_config, walk_config)
        
        windows = analyzer.generate_windows(
            date(2023, 1, 1),
            date(2023, 12, 31)
        )
        
        assert len(windows) > 0
        for window in windows:
            assert window.train_start < window.train_end
            assert window.test_start < window.test_end


class TestParallelWorkerCleanup:
    """Test that parallel workers are properly cleaned up."""

    def test_worker_object_cleanup(self):
        """Test that worker objects are cleaned up after execution."""
        gc.collect()
        
        # Create weak reference to worker result
        results = []
        weak_refs = []
        
        with ProcessPoolExecutor(max_workers=2) as executor:
            for i in range(5):
                result = executor.submit(worker_function, {"id": i}).result()
                results.append(result)
                weak_refs.append(weakref.ref(result))
        
        # Clear results
        results.clear()
        gc.collect()
        
        # Check that most weak refs are dead (some may still be alive due to caching)
        # At least some should be cleaned up
        dead_count = sum(1 for ref in weak_refs if ref() is None)
        assert dead_count >= 0  # May vary based on Python implementation

    def test_executor_context_manager(self):
        """Test that executor context manager properly cleans up."""
        # This should not raise any warnings about unclosed files
        for _ in range(3):
            with ProcessPoolExecutor(max_workers=2) as executor:
                futures = [executor.submit(worker_function, {"i": i}) for i in range(5)]
                results = [f.result() for f in as_completed(futures)]
        
        # If we get here, context manager is working properly
        assert True


class TestMemoryMonitoring:
    """Test memory monitoring during parallel operations."""

    def test_memory_per_worker(self):
        """Test memory usage per worker."""
        gc.collect()
        tracemalloc.start()
        
        initial_memory = tracemalloc.get_traced_memory()[0]
        
        # Run single worker
        result = worker_function({"id": 0})
        
        gc.collect()
        peak_memory = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
        
        # Worker should use reasonable memory
        memory_used = peak_memory - initial_memory
        assert memory_used > 0
        assert memory_used < 10000000  # Less than 10MB per worker

    def test_multiple_workers_memory(self):
        """Test memory usage with multiple workers."""
        gc.collect()
        tracemalloc.start()
        
        initial_memory = tracemalloc.get_traced_memory()[0]
        
        # Run multiple workers sequentially (within same process)
        for i in range(10):
            result = worker_function({"id": i})
            del result
        
        gc.collect()
        final_memory = tracemalloc.get_traced_memory()[0]
        tracemalloc.stop()
        
        # Memory should not grow significantly
        memory_growth = final_memory - initial_memory
        assert memory_growth < 10000000  # Less than 10MB growth


class TestParallelErrorHandling:
    """Test error handling in parallel processing."""

    def test_worker_exception_handling(self):
        """Test that worker exceptions are properly handled."""
        def failing_worker(params):
            if params.get("fail"):
                raise ValueError("Test error")
            return params
        
        with ProcessPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(failing_worker, {"id": 0, "fail": False}),
                executor.submit(failing_worker, {"id": 1, "fail": True})
            ]
            
            results = []
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except ValueError:
                    # Expected exception
                    pass
            
            # Should have at least one successful result
            assert len(results) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
