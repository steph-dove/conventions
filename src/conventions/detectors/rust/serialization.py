"""Rust serialization conventions detector."""

from __future__ import annotations

from ..base import DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from .base import RustDetector
from .index import make_evidence


@DetectorRegistry.register
class RustSerializationDetector(RustDetector):
    """Detect Rust serialization conventions."""

    name = "rust_serialization"
    description = "Detects serialization patterns (Serde, formats)"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect serialization conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        uses_serde = False
        formats: dict[str, dict] = {}
        examples: list[tuple[str, int]] = []

        # Check for serde
        serde_uses = index.find_uses_matching("serde", limit=50)
        if serde_uses:
            uses_serde = True
            examples.extend([(r, ln) for r, _, ln in serde_uses[:3]])

        # Check for Serialize/Deserialize derives
        derive_count = index.count_pattern(
            r"#\[derive\([^)]*(?:Serialize|Deserialize)",
            exclude_tests=True,
        )

        # Check for serde attributes
        serde_attrs = index.count_pattern(
            r"#\[serde\(",
            exclude_tests=True,
        )

        # Check for JSON (serde_json)
        json_uses = index.find_uses_matching("serde_json", limit=30)
        if json_uses:
            formats["json"] = {
                "name": "JSON",
                "crate": "serde_json",
                "count": len(json_uses),
            }

        # Check for TOML
        toml_uses = index.find_uses_matching("toml", limit=30)
        if toml_uses:
            formats["toml"] = {
                "name": "TOML",
                "crate": "toml",
                "count": len(toml_uses),
            }

        # Check for YAML
        yaml_uses = index.find_uses_matching("serde_yaml", limit=30)
        if yaml_uses:
            formats["yaml"] = {
                "name": "YAML",
                "crate": "serde_yaml",
                "count": len(yaml_uses),
            }

        # Check for bincode (binary)
        bincode_uses = index.find_uses_matching("bincode", limit=20)
        if bincode_uses:
            formats["bincode"] = {
                "name": "Bincode",
                "crate": "bincode",
                "count": len(bincode_uses),
            }

        # Check for MessagePack
        msgpack_uses = index.find_uses_matching("rmp_serde", limit=20)
        if not msgpack_uses:
            msgpack_uses = index.find_uses_matching("rmpv", limit=20)
        if msgpack_uses:
            formats["msgpack"] = {
                "name": "MessagePack",
                "crate": "rmp-serde",
                "count": len(msgpack_uses),
            }

        # Check for CBOR
        cbor_uses = index.find_uses_matching("ciborium", limit=20)
        if cbor_uses:
            formats["cbor"] = {
                "name": "CBOR",
                "crate": "ciborium",
                "count": len(cbor_uses),
            }

        # Check for CSV
        csv_uses = index.find_uses_matching("csv", limit=20)
        if csv_uses:
            formats["csv"] = {
                "name": "CSV",
                "crate": "csv",
                "count": len(csv_uses),
            }

        # Check for Protocol Buffers
        prost_uses = index.find_uses_matching("prost", limit=20)
        if prost_uses:
            formats["protobuf"] = {
                "name": "Protocol Buffers",
                "crate": "prost",
                "count": len(prost_uses),
            }

        if not uses_serde and not formats:
            return result

        format_names = [f["name"] for f in formats.values()]

        if uses_serde:
            title = "Serialization: Serde"
            description = f"Uses Serde with {derive_count} derived types."

            if format_names:
                description += f" Formats: {', '.join(format_names[:4])}."

            if serde_attrs > 0:
                description += f" {serde_attrs} serde attributes."
        else:
            title = f"Serialization: {format_names[0]}"
            description = f"Uses {format_names[0]} for serialization."

        confidence = 0.95

        evidence = []
        for rel_path, line in examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="rust.conventions.serialization",
            category="data",
            title=title,
            description=description,
            confidence=confidence,
            language="rust",
            evidence=evidence,
            stats={
                "uses_serde": uses_serde,
                "derive_count": derive_count,
                "serde_attrs": serde_attrs,
                "formats": list(formats.keys()),
                "format_details": formats,
            },
        ))

        return result
