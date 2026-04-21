"""
core/auth_manager.py
Sistema de autenticación local con SQLite.
Maneja registro, login, sesión activa e historial de clips por usuario.
"""
import os
import sqlite3
import hashlib
import secrets
import json
from datetime import datetime
from typing import Optional, List, Dict
from dataclasses import dataclass


DB_PATH = os.path.join(os.path.expanduser("~"), ".streamerclipsai", "users.db")


@dataclass
class User:
    id: int
    username: str
    email: str
    created_at: str


@dataclass 
class ClipHistory:
    id: int
    user_id: int
    source_path: str
    output_path: str
    preset: str
    duration: float
    created_at: str
    label: str


class AuthManager:
    """Gestiona usuarios, sesiones e historial de clips."""

    def __init__(self):
        self._current_user: Optional[User] = None
        self._ensure_db()

    # ------------------------------------------------------------------
    # Base de datos
    # ------------------------------------------------------------------

    def _ensure_db(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = self._connect()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                username   TEXT NOT NULL UNIQUE,
                email      TEXT NOT NULL UNIQUE,
                password   TEXT NOT NULL,
                salt       TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS clip_history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                source_path TEXT NOT NULL,
                output_path TEXT NOT NULL,
                preset      TEXT NOT NULL,
                duration    REAL NOT NULL DEFAULT 0,
                label       TEXT NOT NULL DEFAULT '',
                created_at  TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """)
        conn.commit()
        conn.close()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(DB_PATH)

    # ------------------------------------------------------------------
    # Hash de contraseña
    # ------------------------------------------------------------------

    def _hash_password(self, password: str, salt: str) -> str:
        key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100_000
        )
        return key.hex()

    # ------------------------------------------------------------------
    # Registro
    # ------------------------------------------------------------------

    def register(self, username: str, email: str, password: str) -> tuple[bool, str]:
        """
        Registra un nuevo usuario.
        Retorna (éxito, mensaje)
        """
        username = username.strip()
        email    = email.strip().lower()
        password = password.strip()

        if not username or not email or not password:
            return False, "Todos los campos son obligatorios."
        if len(username) < 3:
            return False, "El nombre de usuario debe tener al menos 3 caracteres."
        if "@" not in email or "." not in email:
            return False, "El email no es válido."
        if len(password) < 6:
            return False, "La contraseña debe tener al menos 6 caracteres."

        salt         = secrets.token_hex(16)
        pwd_hash     = self._hash_password(password, salt)
        created_at   = datetime.now().isoformat()

        try:
            conn = self._connect()
            conn.execute(
                "INSERT INTO users (username, email, password, salt, created_at) VALUES (?,?,?,?,?)",
                (username, email, pwd_hash, salt, created_at)
            )
            conn.commit()
            conn.close()
            return True, "Cuenta creada correctamente."
        except sqlite3.IntegrityError as e:
            if "username" in str(e):
                return False, "Ese nombre de usuario ya está en uso."
            if "email" in str(e):
                return False, "Ese email ya está registrado."
            return False, "Error al crear la cuenta."

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    def login(self, email: str, password: str) -> tuple[bool, str]:
        """
        Inicia sesión.
        Retorna (éxito, mensaje)
        """
        email    = email.strip().lower()
        password = password.strip()

        conn = self._connect()
        row = conn.execute(
            "SELECT id, username, email, password, salt, created_at FROM users WHERE email=?",
            (email,)
        ).fetchone()
        conn.close()

        if not row:
            return False, "Email o contraseña incorrectos."

        user_id, username, user_email, pwd_hash, salt, created_at = row
        if self._hash_password(password, salt) != pwd_hash:
            return False, "Email o contraseña incorrectos."

        self._current_user = User(
            id=user_id,
            username=username,
            email=user_email,
            created_at=created_at
        )
        return True, f"¡Bienvenido, {username}!"

    # ------------------------------------------------------------------
    # Sesión
    # ------------------------------------------------------------------

    def logout(self):
        self._current_user = None

    @property
    def is_logged_in(self) -> bool:
        return self._current_user is not None

    @property
    def current_user(self) -> Optional[User]:
        return self._current_user

    # ------------------------------------------------------------------
    # Historial de clips
    # ------------------------------------------------------------------

    def save_clip(self, source_path: str, output_path: str, preset: str,
                  duration: float, label: str = "") -> bool:
        if not self._current_user:
            return False
        try:
            conn = self._connect()
            conn.execute(
                """INSERT INTO clip_history 
                   (user_id, source_path, output_path, preset, duration, label, created_at)
                   VALUES (?,?,?,?,?,?,?)""",
                (
                    self._current_user.id,
                    source_path,
                    output_path,
                    preset,
                    duration,
                    label,
                    datetime.now().isoformat()
                )
            )
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def get_clip_history(self) -> List[ClipHistory]:
        if not self._current_user:
            return []
        conn = self._connect()
        rows = conn.execute(
            """SELECT id, user_id, source_path, output_path, preset, duration, created_at, label
               FROM clip_history WHERE user_id=? ORDER BY created_at DESC""",
            (self._current_user.id,)
        ).fetchall()
        conn.close()
        return [
            ClipHistory(
                id=r[0], user_id=r[1], source_path=r[2], output_path=r[3],
                preset=r[4], duration=r[5], created_at=r[6], label=r[7]
            )
            for r in rows
        ]

    def delete_clip_history(self, clip_id: int):
        conn = self._connect()
        conn.execute("DELETE FROM clip_history WHERE id=?", (clip_id,))
        conn.commit()
        conn.close()
