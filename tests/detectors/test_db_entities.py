"""Tests for database entity detection across languages."""
from __future__ import annotations

import json
from pathlib import Path

from conventions.detectors.base import DetectorContext


class TestNodePrismaEntities:
    """Tests for Prisma entity detection."""

    def test_detect_prisma_models(self, tmp_path: Path):
        """Detects models from Prisma schema."""
        from conventions.detectors.node.migrations import NodeMigrationsDetector

        # Set up package.json + prisma schema
        (tmp_path / "package.json").write_text(json.dumps({
            "dependencies": {"@prisma/client": "^5.0.0"},
        }))
        prisma_dir = tmp_path / "prisma"
        prisma_dir.mkdir()
        (prisma_dir / "schema.prisma").write_text(
            "model User {\n"
            "  id    Int    @id @default(autoincrement())\n"
            "  email String @unique\n"
            "  name  String?\n"
            "}\n"
            "\n"
            "model Post {\n"
            "  id        Int    @id @default(autoincrement())\n"
            "  title     String\n"
            "  authorId  Int\n"
            "}\n"
            "\n"
            "model Comment {\n"
            "  id     Int    @id @default(autoincrement())\n"
            "  body   String\n"
            "  postId Int\n"
            "}\n"
        )
        # Need at least one .ts file for the index
        (tmp_path / "index.ts").write_text("import { PrismaClient } from '@prisma/client';\n")

        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages={"node"},
            max_files=100,
        )
        result = NodeMigrationsDetector().detect(ctx)

        entity_rules = [r for r in result.rules if r.id == "node.conventions.db_entities"]
        assert len(entity_rules) == 1
        entities = entity_rules[0].stats["entities"]
        assert len(entities) == 3
        names = [e["name"] for e in entities]
        assert "User" in names
        assert "Post" in names
        assert "Comment" in names
        assert entity_rules[0].stats["orm"] == "prisma"

    def test_detect_mongoose_models(self, tmp_path: Path):
        """Detects Mongoose models from source code."""
        from conventions.detectors.node.migrations import NodeMigrationsDetector

        (tmp_path / "package.json").write_text(json.dumps({
            "dependencies": {"mongoose": "^7.0.0", "express": "^4.0.0"},
        }))
        models_dir = tmp_path / "models"
        models_dir.mkdir()
        (models_dir / "user.ts").write_text(
            "import mongoose from 'mongoose';\n"
            "\n"
            "const userSchema = new mongoose.Schema({\n"
            "  name: String,\n"
            "  email: String,\n"
            "});\n"
            "\n"
            "export const User = mongoose.model('User', userSchema);\n"
        )
        (models_dir / "order.ts").write_text(
            "import { model, Schema } from 'mongoose';\n"
            "\n"
            "const orderSchema = new Schema({ total: Number });\n"
            "export const Order = model('Order', orderSchema);\n"
        )
        (tmp_path / "index.ts").write_text("import mongoose from 'mongoose';\n")

        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages={"node"},
            max_files=100,
        )
        result = NodeMigrationsDetector().detect(ctx)

        entity_rules = [r for r in result.rules if r.id == "node.conventions.db_entities"]
        assert len(entity_rules) == 1
        entities = entity_rules[0].stats["entities"]
        assert len(entities) == 2
        names = [e["name"] for e in entities]
        assert "User" in names
        assert "Order" in names
        assert entity_rules[0].stats["orm"] == "mongoose"

    def test_detect_mongodb_collections(self, tmp_path: Path):
        """Detects MongoDB collections from raw driver usage."""
        from conventions.detectors.node.migrations import NodeMigrationsDetector

        (tmp_path / "package.json").write_text(json.dumps({
            "dependencies": {"mongodb": "^5.0.1", "express": "^4.0.0"},
        }))
        store_dir = tmp_path / "data-store"
        store_dir.mkdir()
        (store_dir / "users.ts").write_text(
            "import { Db } from 'mongodb';\n"
            "\n"
            "export class UserStore {\n"
            "  constructor(private db: Db) {}\n"
            "  findAll() {\n"
            "    return this.db.collection<IUser>('users').find().toArray();\n"
            "  }\n"
            "}\n"
        )
        (store_dir / "invoices.ts").write_text(
            "import { Db } from 'mongodb';\n"
            "\n"
            "export class InvoiceStore {\n"
            "  constructor(private db: Db) {}\n"
            "  findAll() {\n"
            "    return this.db.collection('invoices').find().toArray();\n"
            "  }\n"
            "}\n"
        )
        (tmp_path / "index.ts").write_text("import { MongoClient } from 'mongodb';\n")

        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages={"node"},
            max_files=100,
        )
        result = NodeMigrationsDetector().detect(ctx)

        entity_rules = [r for r in result.rules if r.id == "node.conventions.db_entities"]
        assert len(entity_rules) == 1
        entities = entity_rules[0].stats["entities"]
        assert len(entities) == 2
        names = [e["name"] for e in entities]
        assert "users" in names
        assert "invoices" in names
        assert entity_rules[0].stats["orm"] == "mongodb"

    def test_no_prisma_schema(self, tmp_path: Path):
        """No entities emitted when no Prisma schema exists."""
        from conventions.detectors.node.migrations import NodeMigrationsDetector

        (tmp_path / "package.json").write_text(json.dumps({
            "dependencies": {"express": "^4.0.0"},
        }))
        (tmp_path / "index.ts").write_text("console.log('hi');\n")

        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages={"node"},
            max_files=100,
        )
        result = NodeMigrationsDetector().detect(ctx)

        entity_rules = [r for r in result.rules if r.id == "node.conventions.db_entities"]
        assert len(entity_rules) == 0


class TestPythonDBEntities:
    """Tests for Python database entity detection."""

    def test_detect_sqlalchemy_models(self, tmp_path: Path):
        """Detects SQLAlchemy models with __tablename__."""
        from conventions.detectors.python.db import PythonDBConventionsDetector

        models_dir = tmp_path / "models"
        models_dir.mkdir()
        (models_dir / "__init__.py").write_text("")
        (models_dir / "user.py").write_text(
            "from sqlalchemy import Column, Integer, String\n"
            "from sqlalchemy.orm import DeclarativeBase\n"
            "\n"
            "class Base(DeclarativeBase):\n"
            "    pass\n"
            "\n"
            "class User(Base):\n"
            "    __tablename__ = 'users'\n"
            "    id = Column(Integer, primary_key=True)\n"
            "    name = Column(String)\n"
        )
        (models_dir / "order.py").write_text(
            "from sqlalchemy import Column, Integer, ForeignKey\n"
            "from .user import Base\n"
            "\n"
            "class Order(Base):\n"
            "    __tablename__ = 'orders'\n"
            "    id = Column(Integer, primary_key=True)\n"
            "    user_id = Column(Integer, ForeignKey('users.id'))\n"
        )

        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages={"python"},
            max_files=100,
        )
        result = PythonDBConventionsDetector().detect(ctx)

        entity_rules = [r for r in result.rules if r.id == "python.conventions.db_entities"]
        assert len(entity_rules) == 1
        entities = entity_rules[0].stats["entities"]
        assert len(entities) == 2
        names = [e["name"] for e in entities]
        assert "User" in names
        assert "Order" in names
        assert entity_rules[0].stats["orm"] == "sqlalchemy"

    def test_detect_django_models(self, tmp_path: Path):
        """Detects Django models inheriting from models.Model."""
        from conventions.detectors.python.db import PythonDBConventionsDetector

        app_dir = tmp_path / "myapp"
        app_dir.mkdir()
        (app_dir / "__init__.py").write_text("")
        (app_dir / "models.py").write_text(
            "from django.db import models\n"
            "\n"
            "class Product(models.Model):\n"
            "    name = models.CharField(max_length=200)\n"
            "    price = models.DecimalField(max_digits=10, decimal_places=2)\n"
        )

        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages={"python"},
            max_files=100,
        )
        result = PythonDBConventionsDetector().detect(ctx)

        entity_rules = [r for r in result.rules if r.id == "python.conventions.db_entities"]
        assert len(entity_rules) == 1
        assert entity_rules[0].stats["orm"] == "django"
        names = [e["name"] for e in entity_rules[0].stats["entities"]]
        assert "Product" in names


class TestGoDBEntities:
    """Tests for Go database entity detection."""

    def test_detect_gorm_structs(self, tmp_path: Path):
        """Detects Go structs with gorm tags."""
        from conventions.detectors.go.migrations import GoMigrationsDetector

        (tmp_path / "go.mod").write_text(
            "module example.com/myapp\n\ngo 1.21\n"
        )
        models_dir = tmp_path / "models"
        models_dir.mkdir()
        (models_dir / "user.go").write_text(
            'package models\n'
            '\n'
            'type User struct {\n'
            '    ID    uint   `gorm:"primaryKey"`\n'
            '    Name  string `gorm:"column:name"`\n'
            '    Email string `gorm:"column:email;uniqueIndex"`\n'
            '}\n'
            '\n'
            'type Order struct {\n'
            '    ID     uint `gorm:"primaryKey"`\n'
            '    UserID uint `gorm:"index"`\n'
            '    Total  int\n'
            '}\n'
        )

        # Need migration dir for the detector to do anything
        mig_dir = tmp_path / "migrations"
        mig_dir.mkdir()
        (mig_dir / "001_init.sql").write_text("CREATE TABLE users (id INT);\n")

        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages={"go"},
            max_files=100,
        )
        result = GoMigrationsDetector().detect(ctx)

        entity_rules = [r for r in result.rules if r.id == "go.conventions.db_entities"]
        assert len(entity_rules) == 1
        entities = entity_rules[0].stats["entities"]
        assert len(entities) == 2
        names = [e["name"] for e in entities]
        assert "User" in names
        assert "Order" in names
        assert entity_rules[0].stats["orm"] == "gorm"


class TestRustDBEntities:
    """Tests for Rust database entity detection."""

    def test_detect_sqlx_from_row(self, tmp_path: Path):
        """Detects Rust structs with FromRow derive."""
        from conventions.detectors.rust.database import RustDatabaseDetector

        (tmp_path / "Cargo.toml").write_text(
            "[package]\nname = \"myapp\"\nversion = \"0.1.0\"\n"
        )
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "main.rs").write_text(
            'use sqlx::FromRow;\n'
            '\n'
            '#[derive(Debug, FromRow)]\n'
            'pub struct User {\n'
            '    pub id: i64,\n'
            '    pub name: String,\n'
            '    pub email: String,\n'
            '}\n'
            '\n'
            '#[derive(Debug, FromRow)]\n'
            'pub struct Product {\n'
            '    pub id: i64,\n'
            '    pub title: String,\n'
            '}\n'
        )

        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages={"rust"},
            max_files=100,
        )
        result = RustDatabaseDetector().detect(ctx)

        entity_rules = [r for r in result.rules if r.id == "rust.conventions.db_entities"]
        assert len(entity_rules) == 1
        entities = entity_rules[0].stats["entities"]
        assert len(entities) == 2
        names = [e["name"] for e in entities]
        assert "User" in names
        assert "Product" in names
        assert entity_rules[0].stats["orm"] == "sqlx"
