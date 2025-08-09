"""
Performance benchmarking script for Quote Master Pro.
Measures system performance under various load conditions.
"""

import argparse
import asyncio
import json
import logging
import os
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Tuple

import aiohttp
import psutil

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.pricing_service import PricingService, calculate_final_quote

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Benchmark test result"""

    test_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_time: float
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    requests_per_second: float
    p95_response_time: float
    p99_response_time: float
    error_rate: float


class PerformanceBenchmark:
    """
    Comprehensive performance benchmarking suite.
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.auth_headers = {}
        self.results: List[BenchmarkResult] = []

    async def setup(self):
        """Set up benchmark environment"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=100),
        )

        # Get authentication token for API tests
        await self._authenticate()

        logger.info("Benchmark setup completed")

    async def teardown(self):
        """Clean up benchmark environment"""
        if self.session:
            await self.session.close()
        logger.info("Benchmark teardown completed")

    async def _authenticate(self):
        """Authenticate for API testing"""
        try:
            # Create test user
            register_data = {
                "email": "benchmark@example.com",
                "username": "benchmark_user",
                "full_name": "Benchmark User",
                "password": "BenchmarkPass123!",
            }

            async with self.session.post(
                f"{self.base_url}/api/v1/auth/register", json=register_data
            ) as response:
                if response.status not in [200, 201, 409]:  # 409 = user already exists
                    logger.warning(f"User registration failed: {response.status}")

            # Login
            login_data = {
                "username": register_data["email"],
                "password": register_data["password"],
            }

            async with self.session.post(
                f"{self.base_url}/api/v1/auth/login", data=login_data
            ) as response:
                if response.status == 200:
                    auth_data = await response.json()
                    self.auth_headers = {
                        "Authorization": f"Bearer {auth_data['access_token']}"
                    }
                    logger.info("Authentication successful")
                else:
                    logger.warning("Authentication failed, continuing without auth")

        except Exception as e:
            logger.warning(f"Authentication setup failed: {e}")

    async def benchmark_pricing_service(
        self, num_calculations: int = 1000
    ) -> BenchmarkResult:
        """Benchmark pricing service performance"""
        logger.info(
            f"Running pricing service benchmark with {num_calculations} calculations"
        )

        pricing_service = PricingService()
        response_times = []
        successful = 0
        failed = 0

        test_scenarios = [
            ("window_cleaning", 100.0, 1.2, "Perth"),
            ("glass_repair", 25.0, 1.0, "Cottesloe"),
            ("pressure_cleaning", 200.0, 1.5, "Subiaco"),
            ("gutter_cleaning", 150.0, 1.3, "Nedlands"),
            ("window_cleaning", 300.0, 1.8, "Fremantle"),
        ]

        start_time = time.time()

        for i in range(num_calculations):
            scenario = test_scenarios[i % len(test_scenarios)]
            service_type, area, difficulty, suburb = scenario

            calc_start = time.time()
            try:
                price = pricing_service.calculate_price(
                    service_type=service_type,
                    area_sqm=area,
                    difficulty_multiplier=difficulty,
                    suburb=suburb,
                )
                calc_time = time.time() - calc_start
                response_times.append(calc_time)
                successful += 1
            except Exception as e:
                logger.error(f"Pricing calculation failed: {e}")
                failed += 1

        total_time = time.time() - start_time

        return self._create_benchmark_result(
            test_name="Pricing Service",
            total_requests=num_calculations,
            successful_requests=successful,
            failed_requests=failed,
            total_time=total_time,
            response_times=response_times,
        )

    async def benchmark_api_endpoints(
        self, num_requests: int = 100, concurrency: int = 10
    ) -> BenchmarkResult:
        """Benchmark API endpoint performance"""
        logger.info(
            f"Running API benchmark with {num_requests} requests, concurrency {concurrency}"
        )

        quote_request = {
            "service_type": "window_cleaning",
            "property_type": "residential",
            "area_sqm": 120.0,
            "suburb": "Perth",
            "contact_email": "benchmark@example.com",
            "contact_phone": "+61412345678",
            "customer_notes": "Benchmark test quote",
        }

        async def make_request(session, request_id):
            """Make single API request"""
            request_start = time.time()
            try:
                # Modify request data to make it unique
                unique_request = quote_request.copy()
                unique_request["contact_email"] = f"benchmark{request_id}@example.com"

                async with session.post(
                    f"{self.base_url}/api/v1/quotes/generate",
                    json=unique_request,
                    headers=self.auth_headers,
                ) as response:
                    request_time = time.time() - request_start
                    success = response.status in [200, 201]
                    return request_time, success
            except Exception as e:
                request_time = time.time() - request_start
                logger.debug(f"Request {request_id} failed: {e}")
                return request_time, False

        # Execute requests with controlled concurrency
        semaphore = asyncio.Semaphore(concurrency)

        async def controlled_request(request_id):
            async with semaphore:
                return await make_request(self.session, request_id)

        start_time = time.time()

        tasks = [controlled_request(i) for i in range(num_requests)]
        results = await asyncio.gather(*tasks)

        total_time = time.time() - start_time

        response_times = [r[0] for r in results]
        successful = len([r for r in results if r[1]])
        failed = num_requests - successful

        return self._create_benchmark_result(
            test_name="API Endpoints",
            total_requests=num_requests,
            successful_requests=successful,
            failed_requests=failed,
            total_time=total_time,
            response_times=response_times,
        )

    async def benchmark_quote_generation(self, num_quotes: int = 50) -> BenchmarkResult:
        """Benchmark end-to-end quote generation"""
        logger.info(f"Running quote generation benchmark with {num_quotes} quotes")

        response_times = []
        successful = 0
        failed = 0

        test_quotes = [
            {
                "service_type": "window_cleaning",
                "property_type": "residential",
                "area_sqm": 80.0,
                "suburb": "Perth",
            },
            {
                "service_type": "glass_repair",
                "property_type": "commercial",
                "area_sqm": 15.0,
                "suburb": "Subiaco",
            },
            {
                "service_type": "pressure_cleaning",
                "property_type": "residential",
                "area_sqm": 150.0,
                "suburb": "Cottesloe",
            },
        ]

        start_time = time.time()

        for i in range(num_quotes):
            quote_data = test_quotes[i % len(test_quotes)].copy()
            quote_data.update(
                {
                    "contact_email": f"quotegen{i}@example.com",
                    "contact_phone": "+61412345678",
                    "customer_notes": f"Benchmark quote generation test {i}",
                }
            )

            gen_start = time.time()
            try:
                async with self.session.post(
                    f"{self.base_url}/api/v1/quotes/generate",
                    json=quote_data,
                    headers=self.auth_headers,
                ) as response:
                    gen_time = time.time() - gen_start
                    response_times.append(gen_time)

                    if response.status in [200, 201]:
                        successful += 1
                    else:
                        failed += 1
                        logger.debug(
                            f"Quote generation failed with status {response.status}"
                        )

            except Exception as e:
                gen_time = time.time() - gen_start
                response_times.append(gen_time)
                failed += 1
                logger.debug(f"Quote generation error: {e}")

        total_time = time.time() - start_time

        return self._create_benchmark_result(
            test_name="Quote Generation",
            total_requests=num_quotes,
            successful_requests=successful,
            failed_requests=failed,
            total_time=total_time,
            response_times=response_times,
        )

    def benchmark_memory_usage(self, num_operations: int = 10000) -> Dict[str, Any]:
        """Benchmark memory usage during operations"""
        logger.info(f"Running memory usage benchmark with {num_operations} operations")

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Perform memory-intensive operations
        pricing_service = PricingService()

        for i in range(num_operations):
            quote = calculate_final_quote(
                service_type="window_cleaning",
                area_sqm=100.0 + (i % 100),
                difficulty_multiplier=1.0 + (i % 5) * 0.1,
                suburb=["Perth", "Subiaco", "Cottesloe"][i % 3],
            )

            # Trigger garbage collection periodically
            if i % 1000 == 0:
                import gc

                gc.collect()

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        return {
            "test_name": "Memory Usage",
            "operations": num_operations,
            "initial_memory_mb": round(initial_memory, 2),
            "final_memory_mb": round(final_memory, 2),
            "memory_increase_mb": round(memory_increase, 2),
            "memory_per_operation_kb": round(
                (memory_increase * 1024) / num_operations, 3
            ),
        }

    def _create_benchmark_result(
        self,
        test_name: str,
        total_requests: int,
        successful_requests: int,
        failed_requests: int,
        total_time: float,
        response_times: List[float],
    ) -> BenchmarkResult:
        """Create benchmark result from raw data"""

        if not response_times:
            response_times = [0.0]

        avg_response_time = statistics.mean(response_times)
        min_response_time = min(response_times)
        max_response_time = max(response_times)
        requests_per_second = total_requests / total_time if total_time > 0 else 0

        # Calculate percentiles
        sorted_times = sorted(response_times)
        p95_response_time = (
            sorted_times[int(0.95 * len(sorted_times))] if len(sorted_times) > 0 else 0
        )
        p99_response_time = (
            sorted_times[int(0.99 * len(sorted_times))] if len(sorted_times) > 0 else 0
        )

        error_rate = (
            (failed_requests / total_requests) * 100 if total_requests > 0 else 0
        )

        return BenchmarkResult(
            test_name=test_name,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            total_time=round(total_time, 3),
            avg_response_time=round(avg_response_time * 1000, 2),  # Convert to ms
            min_response_time=round(min_response_time * 1000, 2),
            max_response_time=round(max_response_time * 1000, 2),
            requests_per_second=round(requests_per_second, 2),
            p95_response_time=round(p95_response_time * 1000, 2),
            p99_response_time=round(p99_response_time * 1000, 2),
            error_rate=round(error_rate, 2),
        )

    def print_results(self):
        """Print benchmark results in a formatted table"""
        print("\n" + "=" * 80)
        print("QUOTE MASTER PRO - PERFORMANCE BENCHMARK RESULTS")
        print("=" * 80)

        for result in self.results:
            print(f"\n{result.test_name} Benchmark Results:")
            print("-" * 40)
            print(f"Total Requests:        {result.total_requests:,}")
            print(f"Successful:           {result.successful_requests:,}")
            print(f"Failed:               {result.failed_requests:,}")
            print(f"Error Rate:           {result.error_rate}%")
            print(f"Total Time:           {result.total_time}s")
            print(f"Requests/Second:      {result.requests_per_second}")
            print(f"Avg Response Time:    {result.avg_response_time}ms")
            print(f"Min Response Time:    {result.min_response_time}ms")
            print(f"Max Response Time:    {result.max_response_time}ms")
            print(f"95th Percentile:      {result.p95_response_time}ms")
            print(f"99th Percentile:      {result.p99_response_time}ms")

        print("\n" + "=" * 80)

    def save_results(self, filename: str = "benchmark_results.json"):
        """Save results to JSON file"""
        results_data = {
            "timestamp": datetime.now().isoformat(),
            "system_info": {
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": round(
                    psutil.virtual_memory().total / (1024**3), 2
                ),
                "python_version": sys.version,
            },
            "results": [
                {
                    "test_name": r.test_name,
                    "total_requests": r.total_requests,
                    "successful_requests": r.successful_requests,
                    "failed_requests": r.failed_requests,
                    "total_time": r.total_time,
                    "avg_response_time_ms": r.avg_response_time,
                    "min_response_time_ms": r.min_response_time,
                    "max_response_time_ms": r.max_response_time,
                    "requests_per_second": r.requests_per_second,
                    "p95_response_time_ms": r.p95_response_time,
                    "p99_response_time_ms": r.p99_response_time,
                    "error_rate_percent": r.error_rate,
                }
                for r in self.results
            ],
        }

        with open(filename, "w") as f:
            json.dump(results_data, f, indent=2)

        logger.info(f"Results saved to {filename}")

    async def run_full_benchmark(self):
        """Run complete performance benchmark suite"""
        logger.info("Starting full performance benchmark suite")

        # 1. Pricing service benchmark
        pricing_result = await self.benchmark_pricing_service(1000)
        self.results.append(pricing_result)

        # 2. API endpoints benchmark
        api_result = await self.benchmark_api_endpoints(100, 10)
        self.results.append(api_result)

        # 3. Quote generation benchmark
        quote_result = await self.benchmark_quote_generation(50)
        self.results.append(quote_result)

        # 4. Memory usage benchmark
        memory_result = self.benchmark_memory_usage(5000)
        logger.info(f"Memory benchmark: {memory_result}")

        logger.info("Benchmark suite completed")


async def main():
    """Main benchmark execution"""
    parser = argparse.ArgumentParser(
        description="Quote Master Pro Performance Benchmark"
    )
    parser.add_argument(
        "--url", default="http://localhost:8000", help="Base URL for API testing"
    )
    parser.add_argument(
        "--pricing-only", action="store_true", help="Run only pricing benchmarks"
    )
    parser.add_argument(
        "--api-only", action="store_true", help="Run only API benchmarks"
    )
    parser.add_argument(
        "--requests", type=int, default=100, help="Number of requests for API tests"
    )
    parser.add_argument(
        "--concurrency", type=int, default=10, help="Concurrent requests"
    )
    parser.add_argument(
        "--output", default="benchmark_results.json", help="Output file"
    )

    args = parser.parse_args()

    benchmark = PerformanceBenchmark(args.url)

    try:
        await benchmark.setup()

        if args.pricing_only:
            result = await benchmark.benchmark_pricing_service(1000)
            benchmark.results.append(result)
        elif args.api_only:
            result = await benchmark.benchmark_api_endpoints(
                args.requests, args.concurrency
            )
            benchmark.results.append(result)
        else:
            await benchmark.run_full_benchmark()

        benchmark.print_results()
        benchmark.save_results(args.output)

    except KeyboardInterrupt:
        logger.info("Benchmark interrupted by user")
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
    finally:
        await benchmark.teardown()


if __name__ == "__main__":
    asyncio.run(main())
