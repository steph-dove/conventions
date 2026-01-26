"""Python messaging and event-driven patterns detector."""

from __future__ import annotations

from collections import Counter

from ..base import DetectorContext, DetectorResult, PythonDetector
from ..registry import DetectorRegistry
from .index import make_evidence


@DetectorRegistry.register
class PythonMessagingDetector(PythonDetector):
    """Detect Python messaging and event-driven patterns."""

    name = "python_messaging"
    description = "Detects message brokers, event-driven patterns, and async HTTP clients"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect messaging and event-driven patterns."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Detect message brokers
        self._detect_message_broker(ctx, index, result)

        # Detect async HTTP clients
        self._detect_async_http_client(ctx, index, result)

        return result

    def _detect_message_broker(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect message broker usage."""
        broker_libs: Counter[str] = Counter()
        broker_examples: dict[str, list[tuple[str, int]]] = {}

        for rel_path, imp in index.get_all_imports():
            # Skip test files
            file_idx = index.files.get(rel_path)
            if file_idx and file_idx.role in ("test", "docs"):
                continue

            # Kafka
            if any(x in imp.module for x in ["kafka", "aiokafka", "confluent_kafka"]):
                broker_libs["kafka"] += 1
                if "kafka" not in broker_examples:
                    broker_examples["kafka"] = []
                broker_examples["kafka"].append((rel_path, imp.line))

            # RabbitMQ / AMQP
            if any(x in imp.module for x in ["pika", "aio_pika", "kombu", "amqp"]):
                broker_libs["rabbitmq"] += 1
                if "rabbitmq" not in broker_examples:
                    broker_examples["rabbitmq"] = []
                broker_examples["rabbitmq"].append((rel_path, imp.line))

            # Redis pub/sub (distinct from caching)
            if "redis" in imp.module:
                # Check if pubsub is used
                broker_libs["redis_candidate"] += 1
                if "redis_pubsub" not in broker_examples:
                    broker_examples["redis_pubsub"] = []
                broker_examples["redis_pubsub"].append((rel_path, imp.line))

            # NATS
            if "nats" in imp.module:
                broker_libs["nats"] += 1
                if "nats" not in broker_examples:
                    broker_examples["nats"] = []
                broker_examples["nats"].append((rel_path, imp.line))

            # ZeroMQ
            if "zmq" in imp.module or "pyzmq" in imp.module:
                broker_libs["zeromq"] += 1
                if "zeromq" not in broker_examples:
                    broker_examples["zeromq"] = []
                broker_examples["zeromq"].append((rel_path, imp.line))

            # AWS SQS/SNS
            if "boto3" in imp.module or "aioboto3" in imp.module:
                broker_libs["aws_candidate"] += 1

        # Check for actual pub/sub usage patterns
        for rel_path, call in index.get_all_calls():
            # Redis pub/sub
            if any(x in call.name for x in ["pubsub", "publish", "subscribe"]):
                if broker_libs.get("redis_candidate", 0) > 0:
                    broker_libs["redis_pubsub"] = broker_libs.get("redis_pubsub", 0) + 1

            # AWS SQS/SNS
            if any(x in call.name for x in ["send_message", "receive_message", "create_queue"]):
                if broker_libs.get("aws_candidate", 0) > 0:
                    broker_libs["aws_sqs"] = broker_libs.get("aws_sqs", 0) + 1

        # Clean up candidate counts
        broker_libs.pop("redis_candidate", None)
        broker_libs.pop("aws_candidate", None)

        if not broker_libs:
            return

        primary, primary_count = broker_libs.most_common(1)[0]

        broker_names = {
            "kafka": "Apache Kafka",
            "rabbitmq": "RabbitMQ",
            "redis_pubsub": "Redis Pub/Sub",
            "nats": "NATS",
            "zeromq": "ZeroMQ",
            "aws_sqs": "AWS SQS",
        }

        title = f"Message broker: {broker_names.get(primary, primary)}"
        description = (
            f"Uses {broker_names.get(primary, primary)} for messaging. "
            f"Found {primary_count} usages."
        )
        confidence = min(0.9, 0.6 + primary_count * 0.05)

        # Build evidence
        evidence = []
        for rel_path, line in broker_examples.get(primary, broker_examples.get("redis_pubsub", []))[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.message_broker",
            category="messaging",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "broker_library_counts": dict(broker_libs),
                "primary_broker": primary,
            },
        ))

    def _detect_async_http_client(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect async HTTP client usage (only if async code exists)."""
        # First check if this project uses async
        async_count = 0
        for rel_path, func in index.get_all_functions():
            if func.is_async:
                async_count += 1

        if async_count < 3:
            return  # Not significantly async, don't check for async HTTP clients

        http_clients: Counter[str] = Counter()
        client_examples: dict[str, list[tuple[str, int]]] = {}

        for rel_path, imp in index.get_all_imports():
            # Skip test files
            file_idx = index.files.get(rel_path)
            if file_idx and file_idx.role in ("test", "docs"):
                continue

            # httpx (modern, supports both sync and async)
            if "httpx" in imp.module:
                http_clients["httpx"] += 1
                if "httpx" not in client_examples:
                    client_examples["httpx"] = []
                client_examples["httpx"].append((rel_path, imp.line))

            # aiohttp (async-first)
            if "aiohttp" in imp.module and "ClientSession" in imp.names:
                http_clients["aiohttp"] += 1
                if "aiohttp" not in client_examples:
                    client_examples["aiohttp"] = []
                client_examples["aiohttp"].append((rel_path, imp.line))
            elif "aiohttp" in imp.module:
                http_clients["aiohttp"] += 1
                if "aiohttp" not in client_examples:
                    client_examples["aiohttp"] = []
                client_examples["aiohttp"].append((rel_path, imp.line))

            # requests (sync only - check if used in async context)
            if imp.module == "requests":
                http_clients["requests"] += 1
                if "requests" not in client_examples:
                    client_examples["requests"] = []
                client_examples["requests"].append((rel_path, imp.line))

            # asks (async requests-like)
            if "asks" in imp.module:
                http_clients["asks"] += 1
                if "asks" not in client_examples:
                    client_examples["asks"] = []
                client_examples["asks"].append((rel_path, imp.line))

        # Check for AsyncClient usage
        for rel_path, call in index.get_all_calls():
            if "AsyncClient" in call.name:
                http_clients["httpx_async"] = http_clients.get("httpx_async", 0) + 1

        if not http_clients:
            return

        primary, primary_count = http_clients.most_common(1)[0]

        # Merge httpx variants
        if "httpx_async" in http_clients:
            http_clients["httpx"] = http_clients.get("httpx", 0) + http_clients.pop("httpx_async")
            if primary == "httpx_async":
                primary = "httpx"

        client_names = {
            "httpx": "httpx",
            "aiohttp": "aiohttp",
            "requests": "requests",
            "asks": "asks",
        }

        # Quality assessment for async context
        if primary == "httpx":
            quality = "excellent"
            title = "Async HTTP client: httpx (recommended)"
        elif primary == "aiohttp":
            quality = "good"
            title = "Async HTTP client: aiohttp"
        elif primary == "requests":
            quality = "poor"
            title = "HTTP client: requests (sync in async codebase)"
        else:
            quality = "good"
            title = f"Async HTTP client: {client_names.get(primary, primary)}"

        description = f"Uses {client_names.get(primary, primary)} for HTTP requests."
        if quality == "poor":
            description += " Consider using httpx for async/await compatibility."

        confidence = min(0.85, 0.6 + primary_count * 0.05)

        # Build evidence
        evidence = []
        for rel_path, line in client_examples.get(primary, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.async_http_client",
            category="async",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "http_client_counts": dict(http_clients),
                "primary_client": primary,
                "quality": quality,
            },
        ))
