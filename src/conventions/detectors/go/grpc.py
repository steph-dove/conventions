"""Go gRPC and Protocol Buffers conventions detector."""

from __future__ import annotations

from pathlib import Path

from ..base import DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from .base import GoDetector
from .index import make_evidence


@DetectorRegistry.register
class GoGRPCDetector(GoDetector):
    """Detect Go gRPC and Protocol Buffers conventions."""

    name = "go_grpc"
    description = "Detects gRPC and Protocol Buffers usage"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect gRPC and Protocol Buffers conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        # Check for proto files
        proto_dirs = [
            ctx.repo_root / "proto",
            ctx.repo_root / "protos",
            ctx.repo_root / "api" / "proto",
            ctx.repo_root / "api",
        ]

        proto_files: list[Path] = []
        for proto_dir in proto_dirs:
            if proto_dir.is_dir():
                proto_files.extend(proto_dir.glob("**/*.proto"))

        # Also check root
        proto_files.extend(ctx.repo_root.glob("*.proto"))

        # Check for gRPC imports
        grpc_imports = index.find_imports_matching("google.golang.org/grpc", limit=30)
        protobuf_imports = index.find_imports_matching("google.golang.org/protobuf", limit=30)

        # Check for gRPC-gateway
        gateway_imports = index.find_imports_matching("github.com/grpc-ecosystem/grpc-gateway", limit=20)

        # Check for connect-go (modern gRPC alternative)
        connect_imports = index.find_imports_matching("connectrpc.com/connect", limit=20)

        if not proto_files and not grpc_imports and not connect_imports:
            return result

        features = []
        examples: list[tuple[str, int]] = []

        if proto_files:
            features.append(f"{len(proto_files)} proto files")

        if grpc_imports:
            features.append("gRPC")
            examples.extend([(r, ln) for r, _, ln in grpc_imports[:3]])

        if gateway_imports:
            features.append("gRPC-Gateway")
            examples.extend([(r, ln) for r, _, ln in gateway_imports[:2]])

        if connect_imports:
            features.append("Connect")
            examples.extend([(r, ln) for r, _, ln in connect_imports[:3]])

        if protobuf_imports and not grpc_imports:
            features.append("Protocol Buffers")
            examples.extend([(r, ln) for r, _, ln in protobuf_imports[:3]])

        title = f"gRPC/Protobuf: {', '.join(features[:2])}"
        description = f"Uses {', '.join(features)}."

        confidence = min(0.95, 0.7 + len(features) * 0.1)

        evidence = []
        for rel_path, line in examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="go.conventions.grpc",
            category="api",
            title=title,
            description=description,
            confidence=confidence,
            language="go",
            evidence=evidence,
            stats={
                "proto_file_count": len(proto_files),
                "grpc_import_count": len(grpc_imports),
                "gateway_import_count": len(gateway_imports),
                "connect_import_count": len(connect_imports),
                "features": features,
            },
        ))

        return result
