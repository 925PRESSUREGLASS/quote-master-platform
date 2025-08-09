"""
Production health check script for Quote Master Pro.
Comprehensive system health monitoring and alerting.
"""

import argparse
import asyncio
import json
import logging
import smtplib
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from typing import Any, Dict, List, Optional

import aiohttp
import docker
import psutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health check status levels"""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Health check result"""

    name: str
    status: HealthStatus
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class ProductionHealthChecker:
    """
    Comprehensive production health monitoring system.
    """

    def __init__(self, base_url: str = "https://your-domain.com"):
        self.base_url = base_url
        self.session = None
        self.docker_client = None
        self.health_checks: List[HealthCheck] = []
        self.alert_thresholds = {
            "cpu_usage": 80.0,
            "memory_usage": 85.0,
            "disk_usage": 90.0,
            "response_time": 2.0,  # seconds
            "error_rate": 5.0,  # percentage
            "container_restart_count": 3,
        }

    async def initialize(self):
        """Initialize health checker"""
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))

        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            logger.warning(f"Docker client initialization failed: {e}")

        logger.info("Production health checker initialized")

    async def cleanup(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()

        if self.docker_client:
            self.docker_client.close()

    async def check_application_health(self) -> HealthCheck:
        """Check main application health endpoint"""
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/health") as response:
                response_time = time.time() - start_time

                if response.status == 200:
                    data = await response.json()

                    if response_time > self.alert_thresholds["response_time"]:
                        return HealthCheck(
                            name="Application Health",
                            status=HealthStatus.WARNING,
                            message=f"Slow response time: {response_time:.2f}s",
                            details={"response_time": response_time, "data": data},
                        )

                    return HealthCheck(
                        name="Application Health",
                        status=HealthStatus.HEALTHY,
                        message=f"Application healthy (Response: {response_time:.2f}s)",
                        details={"response_time": response_time, "data": data},
                    )

                else:
                    return HealthCheck(
                        name="Application Health",
                        status=HealthStatus.CRITICAL,
                        message=f"Health endpoint returned {response.status}",
                        details={
                            "status_code": response.status,
                            "response_time": response_time,
                        },
                    )

        except asyncio.TimeoutError:
            return HealthCheck(
                name="Application Health",
                status=HealthStatus.CRITICAL,
                message="Health check timed out",
                details={"timeout": True},
            )
        except Exception as e:
            return HealthCheck(
                name="Application Health",
                status=HealthStatus.CRITICAL,
                message=f"Health check failed: {str(e)}",
                details={"error": str(e)},
            )

    async def check_api_health(self) -> HealthCheck:
        """Check API endpoint health"""
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/api/health") as response:
                response_time = time.time() - start_time

                if response.status == 200:
                    data = await response.json()

                    # Check database connection in API health
                    if data.get("database") != "healthy":
                        return HealthCheck(
                            name="API Health",
                            status=HealthStatus.CRITICAL,
                            message="Database connection unhealthy",
                            details=data,
                        )

                    return HealthCheck(
                        name="API Health",
                        status=HealthStatus.HEALTHY,
                        message=f"API healthy (Response: {response_time:.2f}s)",
                        details={"response_time": response_time, "data": data},
                    )

                else:
                    return HealthCheck(
                        name="API Health",
                        status=HealthStatus.CRITICAL,
                        message=f"API health endpoint returned {response.status}",
                        details={"status_code": response.status},
                    )

        except Exception as e:
            return HealthCheck(
                name="API Health",
                status=HealthStatus.CRITICAL,
                message=f"API health check failed: {str(e)}",
                details={"error": str(e)},
            )

    def check_system_resources(self) -> HealthCheck:
        """Check system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            memory_percent = memory.percent
            disk_percent = (disk.used / disk.total) * 100

            details = {
                "cpu_usage": cpu_percent,
                "memory_usage": memory_percent,
                "disk_usage": disk_percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_free_gb": disk.free / (1024**3),
            }

            # Determine status based on thresholds
            if (
                cpu_percent > self.alert_thresholds["cpu_usage"]
                or memory_percent > self.alert_thresholds["memory_usage"]
                or disk_percent > self.alert_thresholds["disk_usage"]
            ):
                status = HealthStatus.CRITICAL
                message = f"Resource usage critical - CPU: {cpu_percent:.1f}%, Memory: {memory_percent:.1f}%, Disk: {disk_percent:.1f}%"

            elif (
                cpu_percent > self.alert_thresholds["cpu_usage"] * 0.8
                or memory_percent > self.alert_thresholds["memory_usage"] * 0.8
                or disk_percent > self.alert_thresholds["disk_usage"] * 0.8
            ):
                status = HealthStatus.WARNING
                message = f"Resource usage warning - CPU: {cpu_percent:.1f}%, Memory: {memory_percent:.1f}%, Disk: {disk_percent:.1f}%"

            else:
                status = HealthStatus.HEALTHY
                message = f"System resources healthy - CPU: {cpu_percent:.1f}%, Memory: {memory_percent:.1f}%, Disk: {disk_percent:.1f}%"

            return HealthCheck(
                name="System Resources", status=status, message=message, details=details
            )

        except Exception as e:
            return HealthCheck(
                name="System Resources",
                status=HealthStatus.UNKNOWN,
                message=f"Resource check failed: {str(e)}",
                details={"error": str(e)},
            )

    def check_docker_containers(self) -> HealthCheck:
        """Check Docker container health"""
        if not self.docker_client:
            return HealthCheck(
                name="Docker Containers",
                status=HealthStatus.UNKNOWN,
                message="Docker client not available",
                details={"docker_available": False},
            )

        try:
            containers = self.docker_client.containers.list()
            quote_master_containers = [
                c
                for c in containers
                if any(name in c.name for name in ["quote-master", "quote_master"])
            ]

            if not quote_master_containers:
                return HealthCheck(
                    name="Docker Containers",
                    status=HealthStatus.CRITICAL,
                    message="No Quote Master Pro containers found",
                    details={"container_count": 0},
                )

            container_details = {}
            unhealthy_containers = []

            for container in quote_master_containers:
                container_info = {
                    "status": container.status,
                    "health": getattr(
                        container.attrs.get("State", {}), "Health", {}
                    ).get("Status", "unknown"),
                    "restart_count": container.attrs.get("RestartCount", 0),
                    "created": container.attrs.get("Created", "unknown"),
                }

                container_details[container.name] = container_info

                # Check for unhealthy conditions
                if (
                    container.status != "running"
                    or container_info["health"] == "unhealthy"
                    or container_info["restart_count"]
                    > self.alert_thresholds["container_restart_count"]
                ):
                    unhealthy_containers.append(container.name)

            if unhealthy_containers:
                return HealthCheck(
                    name="Docker Containers",
                    status=HealthStatus.CRITICAL,
                    message=f"Unhealthy containers: {', '.join(unhealthy_containers)}",
                    details=container_details,
                )

            return HealthCheck(
                name="Docker Containers",
                status=HealthStatus.HEALTHY,
                message=f"All {len(quote_master_containers)} containers healthy",
                details=container_details,
            )

        except Exception as e:
            return HealthCheck(
                name="Docker Containers",
                status=HealthStatus.CRITICAL,
                message=f"Container check failed: {str(e)}",
                details={"error": str(e)},
            )

    def check_ssl_certificate(self) -> HealthCheck:
        """Check SSL certificate validity"""
        try:
            import socket
            import ssl
            from datetime import datetime

            # Extract domain from URL
            domain = (
                self.base_url.replace("https://", "")
                .replace("http://", "")
                .split("/")[0]
            )

            # Get certificate info
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()

            # Parse expiration date
            exp_date = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
            days_until_expiry = (exp_date - datetime.now()).days

            details = {
                "domain": domain,
                "expires": cert["notAfter"],
                "days_until_expiry": days_until_expiry,
                "issuer": dict(x[0] for x in cert["issuer"]),
                "subject": dict(x[0] for x in cert["subject"]),
            }

            if days_until_expiry < 7:
                return HealthCheck(
                    name="SSL Certificate",
                    status=HealthStatus.CRITICAL,
                    message=f"SSL certificate expires in {days_until_expiry} days",
                    details=details,
                )
            elif days_until_expiry < 30:
                return HealthCheck(
                    name="SSL Certificate",
                    status=HealthStatus.WARNING,
                    message=f"SSL certificate expires in {days_until_expiry} days",
                    details=details,
                )
            else:
                return HealthCheck(
                    name="SSL Certificate",
                    status=HealthStatus.HEALTHY,
                    message=f"SSL certificate valid for {days_until_expiry} days",
                    details=details,
                )

        except Exception as e:
            return HealthCheck(
                name="SSL Certificate",
                status=HealthStatus.WARNING,
                message=f"SSL check failed: {str(e)}",
                details={"error": str(e)},
            )

    async def check_database_performance(self) -> HealthCheck:
        """Check database performance via API"""
        try:
            # Test a simple database operation through the API
            start_time = time.time()
            async with self.session.get(
                f"{self.base_url}/api/v1/quotes/service-types"
            ) as response:
                response_time = time.time() - start_time

                if response.status == 200:
                    data = await response.json()

                    if response_time > 2.0:  # 2 second threshold for DB operations
                        return HealthCheck(
                            name="Database Performance",
                            status=HealthStatus.WARNING,
                            message=f"Slow database response: {response_time:.2f}s",
                            details={
                                "response_time": response_time,
                                "record_count": len(data),
                            },
                        )

                    return HealthCheck(
                        name="Database Performance",
                        status=HealthStatus.HEALTHY,
                        message=f"Database performing well ({response_time:.2f}s)",
                        details={
                            "response_time": response_time,
                            "record_count": len(data),
                        },
                    )

                else:
                    return HealthCheck(
                        name="Database Performance",
                        status=HealthStatus.CRITICAL,
                        message=f"Database query failed with status {response.status}",
                        details={"status_code": response.status},
                    )

        except Exception as e:
            return HealthCheck(
                name="Database Performance",
                status=HealthStatus.CRITICAL,
                message=f"Database performance check failed: {str(e)}",
                details={"error": str(e)},
            )

    def check_log_errors(self) -> HealthCheck:
        """Check for recent errors in application logs"""
        try:
            if not self.docker_client:
                return HealthCheck(
                    name="Log Errors",
                    status=HealthStatus.UNKNOWN,
                    message="Docker not available for log checking",
                )

            # Get backend container logs
            containers = self.docker_client.containers.list()
            backend_container = None

            for container in containers:
                if "backend" in container.name and "quote" in container.name:
                    backend_container = container
                    break

            if not backend_container:
                return HealthCheck(
                    name="Log Errors",
                    status=HealthStatus.WARNING,
                    message="Backend container not found for log analysis",
                )

            # Get last 100 lines of logs
            logs = backend_container.logs(tail=100).decode("utf-8")

            # Count error patterns
            error_patterns = ["ERROR", "CRITICAL", "FATAL", "Exception", "Traceback"]
            error_count = sum(
                logs.upper().count(pattern.upper()) for pattern in error_patterns
            )

            recent_errors = []
            for line in logs.split("\n")[-20:]:  # Last 20 lines
                if any(pattern.upper() in line.upper() for pattern in error_patterns):
                    recent_errors.append(line.strip())

            details = {
                "error_count": error_count,
                "recent_errors": recent_errors[:5],  # Show max 5 recent errors
            }

            if error_count > 10:
                return HealthCheck(
                    name="Log Errors",
                    status=HealthStatus.CRITICAL,
                    message=f"High error count in logs: {error_count}",
                    details=details,
                )
            elif error_count > 5:
                return HealthCheck(
                    name="Log Errors",
                    status=HealthStatus.WARNING,
                    message=f"Moderate error count in logs: {error_count}",
                    details=details,
                )
            else:
                return HealthCheck(
                    name="Log Errors",
                    status=HealthStatus.HEALTHY,
                    message=f"Low error count in logs: {error_count}",
                    details=details,
                )

        except Exception as e:
            return HealthCheck(
                name="Log Errors",
                status=HealthStatus.UNKNOWN,
                message=f"Log error check failed: {str(e)}",
                details={"error": str(e)},
            )

    async def run_all_checks(self) -> List[HealthCheck]:
        """Run all health checks"""
        self.health_checks = []

        # Application checks
        self.health_checks.append(await self.check_application_health())
        self.health_checks.append(await self.check_api_health())
        self.health_checks.append(await self.check_database_performance())

        # Infrastructure checks
        self.health_checks.append(self.check_system_resources())
        self.health_checks.append(self.check_docker_containers())
        self.health_checks.append(self.check_ssl_certificate())
        self.health_checks.append(self.check_log_errors())

        return self.health_checks

    def get_overall_status(self) -> HealthStatus:
        """Determine overall system health status"""
        if not self.health_checks:
            return HealthStatus.UNKNOWN

        critical_count = len(
            [c for c in self.health_checks if c.status == HealthStatus.CRITICAL]
        )
        warning_count = len(
            [c for c in self.health_checks if c.status == HealthStatus.WARNING]
        )

        if critical_count > 0:
            return HealthStatus.CRITICAL
        elif warning_count > 0:
            return HealthStatus.WARNING
        else:
            return HealthStatus.HEALTHY

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive health report"""
        overall_status = self.get_overall_status()

        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": overall_status.value,
            "summary": {
                "total_checks": len(self.health_checks),
                "healthy": len(
                    [c for c in self.health_checks if c.status == HealthStatus.HEALTHY]
                ),
                "warnings": len(
                    [c for c in self.health_checks if c.status == HealthStatus.WARNING]
                ),
                "critical": len(
                    [c for c in self.health_checks if c.status == HealthStatus.CRITICAL]
                ),
                "unknown": len(
                    [c for c in self.health_checks if c.status == HealthStatus.UNKNOWN]
                ),
            },
            "checks": [
                {
                    "name": check.name,
                    "status": check.status.value,
                    "message": check.message,
                    "details": check.details,
                    "timestamp": check.timestamp.isoformat(),
                }
                for check in self.health_checks
            ],
        }

        return report

    def print_report(self):
        """Print health report to console"""
        overall_status = self.get_overall_status()

        print("\n" + "=" * 60)
        print("QUOTE MASTER PRO - PRODUCTION HEALTH CHECK")
        print("=" * 60)
        print(f"Overall Status: {overall_status.value.upper()}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        for check in self.health_checks:
            status_emoji = {
                HealthStatus.HEALTHY: "✅",
                HealthStatus.WARNING: "⚠️",
                HealthStatus.CRITICAL: "❌",
                HealthStatus.UNKNOWN: "❓",
            }

            print(f"{status_emoji[check.status]} {check.name}: {check.message}")

            if check.details and check.status != HealthStatus.HEALTHY:
                for key, value in check.details.items():
                    if key != "error":
                        print(f"   {key}: {value}")

        print("\n" + "=" * 60)

    def save_report(self, filename: str = "health_report.json"):
        """Save health report to file"""
        report = self.generate_report()
        with open(filename, "w") as f:
            json.dump(report, f, indent=2)
        logger.info(f"Health report saved to {filename}")


async def main():
    """Main health check execution"""
    parser = argparse.ArgumentParser(
        description="Quote Master Pro Production Health Check"
    )
    parser.add_argument(
        "--url", default="https://your-domain.com", help="Base URL to check"
    )
    parser.add_argument("--output", default="health_report.json", help="Output file")
    parser.add_argument("--quiet", action="store_true", help="Suppress console output")
    parser.add_argument("--continuous", action="store_true", help="Run continuously")
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Check interval in seconds (for continuous mode)",
    )

    args = parser.parse_args()

    checker = ProductionHealthChecker(args.url)

    try:
        await checker.initialize()

        if args.continuous:
            logger.info(
                f"Starting continuous health monitoring (interval: {args.interval}s)"
            )
            while True:
                await checker.run_all_checks()

                if not args.quiet:
                    checker.print_report()

                checker.save_report(args.output)

                # Check for critical status and alert
                overall_status = checker.get_overall_status()
                if overall_status == HealthStatus.CRITICAL:
                    logger.error("CRITICAL: System health issues detected!")
                    # Here you could add email/Slack notifications

                await asyncio.sleep(args.interval)
        else:
            await checker.run_all_checks()

            if not args.quiet:
                checker.print_report()

            checker.save_report(args.output)

            # Exit with appropriate code
            overall_status = checker.get_overall_status()
            if overall_status == HealthStatus.CRITICAL:
                exit(2)
            elif overall_status == HealthStatus.WARNING:
                exit(1)
            else:
                exit(0)

    except KeyboardInterrupt:
        logger.info("Health check interrupted by user")
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        exit(3)
    finally:
        await checker.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
