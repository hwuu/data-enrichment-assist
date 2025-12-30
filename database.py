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
    def get_ticket_list(self) -> List[Dict[str, Any]]:
        """Get ticket list with summary info only."""
        pass

    @abstractmethod
    def get_all_tickets(self) -> List[Dict[str, Any]]:
        """Get all tickets with full details."""
        pass

    @abstractmethod
    def get_ticket_by_id(self, process_id: str) -> Optional[Dict[str, Any]]:
        """Get a single ticket by process ID."""
        pass

    @abstractmethod
    def get_ticket_review(self, process_id: str) -> Optional[Dict[str, Any]]:
        """Get review for a ticket."""
        pass

    @abstractmethod
    def save_ticket_review(self, process_id: str, content: str) -> Dict[str, Any]:
        """Save or update review for a ticket. Returns the saved review."""
        pass

    def _parse_ticket_summary(self, row) -> Dict[str, Any]:
        """Parse a database row into a ticket summary dictionary."""
        create_time = row[3]
        update_time = row[4] if row[4] else create_time
        return {
            'processId': row[0],
            'issueType': row[1],
            'owner': row[2],
            'createTime': create_time,
            'updateTime': update_time,
            'problem': row[5],
            'score': row[6],
            'hasReview': bool(row[7]) if len(row) > 7 else False
        }

    def _parse_ticket_row(self, row) -> Dict[str, Any]:
        """Parse a database row into a full ticket dictionary."""
        create_time = row[3]
        update_time = row[4] if row[4] else create_time
        return {
            'processId': row[0],
            'issueType': row[1],
            'owner': row[2],
            'createTime': create_time,
            'updateTime': update_time,
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

    def _ensure_review_table(self, conn):
        """Create ticket_review table if not exists."""
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ticket_review (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                processId TEXT NOT NULL UNIQUE,
                createTime TEXT NOT NULL,
                updateTime TEXT NOT NULL,
                content TEXT NOT NULL
            )
        ''')
        conn.commit()

    def get_ticket_list(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            self._ensure_review_table(conn)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT T2."流程ID", C."issueType", C."owner", T2.create_time, T2.update_time,
                       T2."问题现象", T2."得分", R.id
                FROM operations_kb as T2
                JOIN ticket_classification_2512 as C ON T2."流程ID" = C."processId"
                LEFT JOIN ticket_review as R ON T2."流程ID" = R.processId
                ORDER BY T2.update_time DESC, T2.create_time DESC
            ''')
            rows = cursor.fetchall()
            return [self._parse_ticket_summary(row) for row in rows]
        finally:
            conn.close()

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

    def get_ticket_review(self, process_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            self._ensure_review_table(conn)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, processId, createTime, updateTime, content
                FROM ticket_review WHERE processId = ?
            ''', (process_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'processId': row[1],
                    'createTime': row[2],
                    'updateTime': row[3],
                    'content': row[4]
                }
            return None
        finally:
            conn.close()

    def save_ticket_review(self, process_id: str, content: str) -> Dict[str, Any]:
        from datetime import datetime
        conn = self._get_connection()
        try:
            self._ensure_review_table(conn)
            cursor = conn.cursor()
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Check if review exists
            cursor.execute('SELECT id, createTime FROM ticket_review WHERE processId = ?', (process_id,))
            existing = cursor.fetchone()

            if existing:
                # Update existing
                cursor.execute('''
                    UPDATE ticket_review SET content = ?, updateTime = ? WHERE processId = ?
                ''', (content, now, process_id))
                create_time = existing[1]
                review_id = existing[0]
            else:
                # Insert new
                cursor.execute('''
                    INSERT INTO ticket_review (processId, createTime, updateTime, content)
                    VALUES (?, ?, ?, ?)
                ''', (process_id, now, now, content))
                create_time = now
                review_id = cursor.lastrowid

            conn.commit()
            return {
                'id': review_id,
                'processId': process_id,
                'createTime': create_time,
                'updateTime': now,
                'content': content
            }
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

    def get_ticket_list(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            self._ensure_review_table(conn)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT T2."流程ID", C."issueType", C."owner", T2.create_time, T2.update_time,
                       T2."问题现象", T2."得分", R.id
                FROM operations_kb as T2
                JOIN ticket_classification_2512 as C ON T2."流程ID" = C."processId"
                LEFT JOIN ticket_review as R ON T2."流程ID" = R.processId
                ORDER BY T2.update_time DESC, T2.create_time DESC
            ''')
            rows = cursor.fetchall()
            return [self._parse_ticket_summary(row) for row in rows]
        finally:
            conn.close()

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

    def _ensure_review_table(self, conn):
        """Create ticket_review table if not exists."""
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ticket_review (
                id SERIAL PRIMARY KEY,
                processId TEXT NOT NULL UNIQUE,
                createTime TIMESTAMP NOT NULL,
                updateTime TIMESTAMP NOT NULL,
                content TEXT NOT NULL
            )
        ''')
        conn.commit()

    def get_ticket_review(self, process_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            self._ensure_review_table(conn)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, processId, createTime, updateTime, content
                FROM ticket_review WHERE processId = %s
            ''', (process_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'processId': row[1],
                    'createTime': row[2].strftime('%Y-%m-%d %H:%M:%S') if row[2] else None,
                    'updateTime': row[3].strftime('%Y-%m-%d %H:%M:%S') if row[3] else None,
                    'content': row[4]
                }
            return None
        finally:
            conn.close()

    def save_ticket_review(self, process_id: str, content: str) -> Dict[str, Any]:
        from datetime import datetime
        conn = self._get_connection()
        try:
            self._ensure_review_table(conn)
            cursor = conn.cursor()
            now = datetime.now()

            # Check if review exists
            cursor.execute('SELECT id, createTime FROM ticket_review WHERE processId = %s', (process_id,))
            existing = cursor.fetchone()

            if existing:
                # Update existing
                cursor.execute('''
                    UPDATE ticket_review SET content = %s, updateTime = %s WHERE processId = %s
                ''', (content, now, process_id))
                create_time = existing[1]
                review_id = existing[0]
            else:
                # Insert new
                cursor.execute('''
                    INSERT INTO ticket_review (processId, createTime, updateTime, content)
                    VALUES (%s, %s, %s, %s) RETURNING id
                ''', (process_id, now, now, content))
                create_time = now
                review_id = cursor.fetchone()[0]

            conn.commit()
            return {
                'id': review_id,
                'processId': process_id,
                'createTime': create_time.strftime('%Y-%m-%d %H:%M:%S'),
                'updateTime': now.strftime('%Y-%m-%d %H:%M:%S'),
                'content': content
            }
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
