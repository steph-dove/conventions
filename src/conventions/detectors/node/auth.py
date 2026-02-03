"""Node.js authentication provider conventions detector."""

from __future__ import annotations

import json

from ..base import DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from .base import NodeDetector
from .index import make_evidence


@DetectorRegistry.register
class NodeAuthDetector(NodeDetector):
    """Detect Node.js authentication provider conventions."""

    name = "node_auth"
    description = "Detects authentication providers and patterns"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect authentication provider conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        self._detect_auth_provider(ctx, index, result)

        return result

    def _detect_auth_provider(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect authentication provider (Auth0, Firebase, Passport, etc.)."""
        providers: dict[str, dict] = {}
        examples: list[tuple[str, int]] = []

        pkg_json_path = ctx.repo_root / "package.json"
        all_deps = {}
        if pkg_json_path.exists():
            try:
                pkg_data = json.loads(pkg_json_path.read_text())
                all_deps = {
                    **pkg_data.get("dependencies", {}),
                    **pkg_data.get("devDependencies", {}),
                }
            except (json.JSONDecodeError, OSError):
                pass

        # Auth0
        if "@auth0/auth0-react" in all_deps or "auth0-js" in all_deps:
            providers["auth0"] = {"name": "Auth0", "type": "frontend"}
            auth0_imports = index.find_imports_matching("auth0", limit=10)
            examples.extend([(r, ln) for r, _, ln in auth0_imports[:3]])
        if "express-openid-connect" in all_deps or "@auth0/nextjs-auth0" in all_deps:
            providers["auth0"] = {"name": "Auth0", "type": "fullstack"}
            auth0_imports = index.find_imports_matching("auth0", limit=10)
            examples.extend([(r, ln) for r, _, ln in auth0_imports[:3]])

        # Firebase Auth
        if "firebase" in all_deps or "@firebase/auth" in all_deps:
            providers["firebase"] = {"name": "Firebase Auth"}
            firebase_imports = index.find_imports_matching("firebase", limit=10)
            examples.extend([(r, ln) for r, _, ln in firebase_imports[:3]])

        # Passport.js
        if "passport" in all_deps:
            providers["passport"] = {"name": "Passport.js"}
            # Check for strategies
            strategies = []
            if "passport-local" in all_deps:
                strategies.append("local")
            if "passport-jwt" in all_deps:
                strategies.append("JWT")
            if "passport-google-oauth20" in all_deps:
                strategies.append("Google OAuth")
            if "passport-github2" in all_deps:
                strategies.append("GitHub")
            if strategies:
                providers["passport"]["strategies"] = strategies
            passport_imports = index.find_imports_matching("passport", limit=10)
            examples.extend([(r, ln) for r, _, ln in passport_imports[:3]])

        # NextAuth.js
        if "next-auth" in all_deps:
            providers["nextauth"] = {"name": "NextAuth.js"}
            nextauth_imports = index.find_imports_matching("next-auth", limit=10)
            examples.extend([(r, ln) for r, _, ln in nextauth_imports[:3]])

        # Clerk
        if "@clerk/clerk-react" in all_deps or "@clerk/nextjs" in all_deps:
            providers["clerk"] = {"name": "Clerk"}
            clerk_imports = index.find_imports_matching("@clerk/", limit=10)
            examples.extend([(r, ln) for r, _, ln in clerk_imports[:3]])

        # Supabase Auth
        if "@supabase/supabase-js" in all_deps:
            providers["supabase"] = {"name": "Supabase Auth"}

        # AWS Cognito
        if "amazon-cognito-identity-js" in all_deps or "@aws-amplify/auth" in all_deps:
            providers["cognito"] = {"name": "AWS Cognito"}

        # Keycloak
        if "keycloak-js" in all_deps or "@react-keycloak/web" in all_deps:
            providers["keycloak"] = {"name": "Keycloak"}

        # Okta
        if "@okta/okta-auth-js" in all_deps or "@okta/okta-react" in all_deps:
            providers["okta"] = {"name": "Okta"}

        # Simple JWT (custom auth)
        if "jsonwebtoken" in all_deps:
            jwt_imports = index.find_imports_matching("jsonwebtoken", limit=10)
            if jwt_imports and "passport" not in providers:
                providers["jwt"] = {"name": "Custom JWT auth"}
                examples.extend([(r, ln) for r, _, ln in jwt_imports[:3]])

        # bcrypt (password hashing)
        has_bcrypt = "bcrypt" in all_deps or "bcryptjs" in all_deps

        if not providers:
            return

        # Determine primary provider
        priority = [
            "auth0", "clerk", "nextauth", "firebase", "supabase",
            "cognito", "okta", "keycloak", "passport", "jwt"
        ]
        primary = None
        for p in priority:
            if p in providers:
                primary = p
                break
        if primary is None:
            primary = list(providers.keys())[0]

        provider_info = providers[primary]
        title = f"Auth provider: {provider_info['name']}"
        description = f"Uses {provider_info['name']} for authentication."

        if provider_info.get("strategies"):
            description += f" Strategies: {', '.join(provider_info['strategies'])}."
        if provider_info.get("type"):
            description += f" ({provider_info['type']})"
        if has_bcrypt:
            description += " Password hashing with bcrypt."

        if len(providers) > 1:
            others = [providers[k]["name"] for k in providers if k != primary]
            description += f" Also: {', '.join(others[:2])}."

        confidence = 0.95

        evidence = []
        for rel_path, line in examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="node.conventions.auth_provider",
            category="security",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=evidence,
            stats={
                "providers": list(providers.keys()),
                "primary_provider": primary,
                "provider_details": providers,
                "has_password_hashing": has_bcrypt,
            },
        ))
