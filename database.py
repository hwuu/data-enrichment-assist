"""Database abstraction layer."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import json


class DatabaseInterface(ABC):
    """Abstract base class for database operations."""

    @abstractmethod
    def connect(self) -> None:
        """Establish database connection."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close database connection."""
        pass

    @abstractmethod
    def get_all_tickets(self) -> List[Dict[str, Any]]:
        """Get all tickets with classification info."""
        pass

    @abstractmethod
    def get_ticket_by_id(self, process_id: str) -> Optional[Dict[str, Any]]:
        """Get a single ticket by process ID."""
        pass

    def _parse_ticket_row(self, row) -> Dict[str, Any]:
        """Parse a database row into a ticket dictionary."""
        return {
            'processId': row[0],
            'issueType': row[1],
            'owner': row[2],
            'createTime': row[3],
            'updateTime': row[4],
            'problem': row[5],
            'rootCause': row[6],
            'analysis': json.loads(row[7]) if row[7] else [],
            'solution': json.loads(row[8]) if row[8] else [],
            'diffScore': row[9],
            'score': row[10],
            'reason': row[11]
        }


class SQLiteDatabase(DatabaseInterface):
    """SQLite implementation."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None

    def connect(self) -> None:
        import sqlite3
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    def close(self) -> None:
        if self.conn:
            self.conn.close()
            self.conn = None

    def _get_connection(self):
        import sqlite3
        # Create new connection for each request (thread-safe)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_all_tickets(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT T2."流程ID", C."issueType", C."owner", T2.create_time, T2.update_time,
                       T2."问题现象", T2."问题根因", T2."分析过程", T2."解决方案",
                       T2.diff_score, T2."得分", T2."理由"
                FROM operations_kb as T2, ticket_classification_2512 as C
                WHERE T2."流程ID" = C."processId"
                ORDER BY T2.update_time DESC, T2.create_time DESC
            ''')
            rows = cursor.fetchall()
            return [self._parse_ticket_row(row) for row in rows]
        finally:
            conn.close()

    def get_ticket_by_id(self, process_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT T2."流程ID", C."issueType", C."owner", T2.create_time, T2.update_time,
                       T2."问题现象", T2."问题根因", T2."分析过程", T2."解决方案",
                       T2.diff_score, T2."得分", T2."理由"
                FROM operations_kb as T2, ticket_classification_2512 as C
                WHERE T2."流程ID" = C."processId" AND T2."流程ID" = ?
            ''', (process_id,))
            row = cursor.fetchone()
            return self._parse_ticket_row(row) if row else None
        finally:
            conn.close()


class PostgreSQLDatabase(DatabaseInterface):
    """PostgreSQL implementation."""

    def __init__(self, host: str, port: int, database: str, user: str, password: str):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.conn = None

    def connect(self) -> None:
        import psycopg2
        self.conn = psycopg2.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password
        )

    def close(self) -> None:
        if self.conn:
            self.conn.close()
            self.conn = None

    def _get_connection(self):
        import psycopg2
        return psycopg2.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password
        )

    def get_all_tickets(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT T2."流程ID", C."issueType", C."owner", T2.create_time, T2.update_time,
                       T2."问题现象", T2."问题根因", T2."分析过程", T2."解决方案",
                       T2.diff_score, T2."得分", T2."理由"
                FROM operations_kb as T2, ticket_classification_2512 as C
                WHERE T2."流程ID" = C."processId"
                ORDER BY T2.update_time DESC, T2.create_time DESC
            ''')
            rows = cursor.fetchall()
            return [self._parse_ticket_row(row) for row in rows]
        finally:
            conn.close()

    def get_ticket_by_id(self, process_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT T2."流程ID", C."issueType", C."owner", T2.create_time, T2.update_time,
                       T2."问题现象", T2."问题根因", T2."分析过程", T2."解决方案",
                       T2.diff_score, T2."得分", T2."理由"
                FROM operations_kb as T2, ticket_classification_2512 as C
                WHERE T2."流程ID" = C."processId" AND T2."流程ID" = %s
            ''', (process_id,))
            row = cursor.fetchone()
            return self._parse_ticket_row(row) if row else None
        finally:
            conn.close()


def create_database(config: Dict[str, Any]) -> DatabaseInterface:
    """Factory function to create database instance based on config."""
    db_type = config.get('type', 'sqlite')

    if db_type == 'sqlite':
        return SQLiteDatabase(db_path=config.get('path', 'gaussdb_ops.db'))
    elif db_type == 'postgresql':
        return PostgreSQLDatabase(
            host=config.get('host', 'localhost'),
            port=config.get('port', 5432),
            database=config.get('database', 'gaussdb_ops'),
            user=config.get('user', 'postgres'),
            password=config.get('password', '')
        )
    else:
        raise ValueError(f"Unsupported database type: {db_type}")
