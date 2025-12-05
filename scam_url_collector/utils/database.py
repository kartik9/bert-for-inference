"""
Database management for scam URL collection.
"""
import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScamURLDatabase:
    """SQLite database manager for scam URLs."""

    def __init__(self, db_path: str = 'data/scam_urls.db'):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path

        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        self._create_tables()
        logger.info(f"Database initialized at {db_path}")

    def _create_tables(self):
        """Create database tables if they don't exist."""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS scam_urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                url_normalized TEXT NOT NULL,
                source TEXT NOT NULL,
                source_id TEXT,
                source_url TEXT,
                context TEXT,
                scam_type TEXT,
                date_found TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date_posted TIMESTAMP,
                metadata JSON,
                priority_score REAL DEFAULT 0,
                validated BOOLEAN DEFAULT 0,
                investigation_status TEXT DEFAULT 'pending',
                UNIQUE(url_normalized, source, source_id)
            )
        ''')

        # Create indexes for better query performance
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_url_normalized
            ON scam_urls(url_normalized)
        ''')

        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_date_found
            ON scam_urls(date_found DESC)
        ''')

        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_priority
            ON scam_urls(priority_score DESC)
        ''')

        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_status
            ON scam_urls(investigation_status)
        ''')

        self.conn.commit()
        logger.info("Database tables created/verified")

    def insert_url(self, url_data: Dict[str, Any]) -> bool:
        """
        Insert a URL record into the database with deduplication.

        Args:
            url_data: Dictionary containing URL data

        Returns:
            True if inserted, False if duplicate
        """
        try:
            # Convert datetime objects to strings
            date_posted = url_data.get('date_posted')
            if isinstance(date_posted, datetime):
                date_posted = date_posted.isoformat()

            # Serialize metadata to JSON
            metadata = url_data.get('metadata', {})
            metadata_json = json.dumps(metadata)

            self.cursor.execute('''
                INSERT OR IGNORE INTO scam_urls
                (url, url_normalized, source, source_id, source_url,
                 context, scam_type, date_posted, metadata, priority_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                url_data.get('url'),
                url_data.get('url_normalized'),
                url_data.get('source'),
                url_data.get('source_id'),
                url_data.get('source_url'),
                url_data.get('context'),
                url_data.get('scam_type'),
                date_posted,
                metadata_json,
                url_data.get('priority_score', 0)
            ))

            self.conn.commit()

            # Check if a row was inserted
            if self.cursor.rowcount > 0:
                logger.debug(f"Inserted new URL: {url_data.get('url')}")
                return True
            else:
                logger.debug(f"Duplicate URL skipped: {url_data.get('url')}")
                return False

        except sqlite3.IntegrityError as e:
            logger.warning(f"Integrity error inserting URL: {e}")
            return False
        except Exception as e:
            logger.error(f"Error inserting URL: {e}", exc_info=True)
            return False

    def get_pending_urls(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get URLs pending investigation, sorted by priority.

        Args:
            limit: Maximum number of URLs to return

        Returns:
            List of URL records
        """
        try:
            self.cursor.execute('''
                SELECT * FROM scam_urls
                WHERE investigation_status = 'pending'
                ORDER BY priority_score DESC, date_found DESC
                LIMIT ?
            ''', (limit,))

            rows = self.cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Error getting pending URLs: {e}", exc_info=True)
            return []

    def get_urls_by_source(self, source: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get URLs from a specific source.

        Args:
            source: Source name (reddit, twitter, bbb, ftc)
            limit: Maximum number of URLs to return

        Returns:
            List of URL records
        """
        try:
            self.cursor.execute('''
                SELECT * FROM scam_urls
                WHERE source = ?
                ORDER BY date_found DESC
                LIMIT ?
            ''', (source, limit))

            rows = self.cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Error getting URLs by source: {e}", exc_info=True)
            return []

    def get_url_by_normalized(self, url_normalized: str) -> Optional[Dict[str, Any]]:
        """
        Get a URL record by its normalized form.

        Args:
            url_normalized: Normalized URL

        Returns:
            URL record or None
        """
        try:
            self.cursor.execute('''
                SELECT * FROM scam_urls
                WHERE url_normalized = ?
                LIMIT 1
            ''', (url_normalized,))

            row = self.cursor.fetchone()
            return self._row_to_dict(row) if row else None

        except Exception as e:
            logger.error(f"Error getting URL by normalized: {e}", exc_info=True)
            return None

    def count_sources_for_url(self, url_normalized: str) -> int:
        """
        Count how many different sources reported the same URL.

        Args:
            url_normalized: Normalized URL

        Returns:
            Number of unique sources
        """
        try:
            self.cursor.execute('''
                SELECT COUNT(DISTINCT source) as count
                FROM scam_urls
                WHERE url_normalized = ?
            ''', (url_normalized,))

            result = self.cursor.fetchone()
            return result['count'] if result else 0

        except Exception as e:
            logger.error(f"Error counting sources: {e}", exc_info=True)
            return 0

    def calculate_priority_score(self, url_record: Dict[str, Any]) -> float:
        """
        Calculate priority score for a URL.

        Scoring logic:
        - +10 per additional independent source
        - +10 if very recent (< 7 days)
        - +5 if recent (< 30 days)
        - +5 for high engagement
        - +15 for severe scam types
        - +5 for vetted sources (BBB)

        Args:
            url_record: URL record dictionary

        Returns:
            Calculated priority score
        """
        score = 0.0

        # Count multiple sources
        url_normalized = url_record.get('url_normalized', '')
        if url_normalized:
            source_count = self.count_sources_for_url(url_normalized)
            score += (source_count - 1) * 10  # -1 because we count current source

        # Recency bonus
        date_posted = url_record.get('date_posted')
        if date_posted:
            if isinstance(date_posted, str):
                try:
                    date_posted = datetime.fromisoformat(date_posted)
                except:
                    date_posted = None

            if isinstance(date_posted, datetime):
                days_old = (datetime.now() - date_posted).days
                if days_old < 7:
                    score += 10
                elif days_old < 30:
                    score += 5
                elif days_old > 90:
                    score -= 5  # Penalty for old URLs

        # Engagement score
        metadata = url_record.get('metadata', {})
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except:
                metadata = {}

        upvotes = metadata.get('upvotes', 0)
        retweets = metadata.get('retweets', 0)
        likes = metadata.get('likes', 0)

        engagement = upvotes + retweets + likes
        score += min(engagement / 10, 10)  # Max 10 points from engagement

        # Scam type severity
        scam_type = url_record.get('scam_type', '').lower()
        if scam_type in ['financial', 'identity_theft', 'banking', 'crypto']:
            score += 15
        elif scam_type in ['phishing', 'malware']:
            score += 10

        # Source credibility
        source = url_record.get('source', '')
        if source == 'bbb':
            score += 5  # BBB reports are vetted
        elif source == 'ftc':
            score += 5  # FTC mentions are authoritative

        return round(score, 2)

    def update_priority_scores(self):
        """Recalculate priority scores for all pending URLs."""
        try:
            self.cursor.execute('''
                SELECT * FROM scam_urls
                WHERE investigation_status = 'pending'
            ''')

            rows = self.cursor.fetchall()
            updated_count = 0

            for row in rows:
                record = self._row_to_dict(row)
                new_score = self.calculate_priority_score(record)

                self.cursor.execute('''
                    UPDATE scam_urls
                    SET priority_score = ?
                    WHERE id = ?
                ''', (new_score, record['id']))

                updated_count += 1

            self.conn.commit()
            logger.info(f"Updated priority scores for {updated_count} URLs")

        except Exception as e:
            logger.error(f"Error updating priority scores: {e}", exc_info=True)

    def mark_as_investigated(self, url_id: int, validated: bool = False):
        """
        Mark a URL as investigated.

        Args:
            url_id: Database ID of the URL
            validated: Whether the URL was confirmed as a scam
        """
        try:
            self.cursor.execute('''
                UPDATE scam_urls
                SET investigation_status = 'completed',
                    validated = ?
                WHERE id = ?
            ''', (1 if validated else 0, url_id))

            self.conn.commit()
            logger.info(f"Marked URL {url_id} as investigated")

        except Exception as e:
            logger.error(f"Error marking URL as investigated: {e}", exc_info=True)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Dictionary of statistics
        """
        try:
            stats = {}

            # Total URLs
            self.cursor.execute('SELECT COUNT(*) as count FROM scam_urls')
            stats['total_urls'] = self.cursor.fetchone()['count']

            # Pending URLs
            self.cursor.execute('''
                SELECT COUNT(*) as count FROM scam_urls
                WHERE investigation_status = 'pending'
            ''')
            stats['pending_urls'] = self.cursor.fetchone()['count']

            # URLs by source
            self.cursor.execute('''
                SELECT source, COUNT(*) as count
                FROM scam_urls
                GROUP BY source
            ''')
            stats['by_source'] = {row['source']: row['count'] for row in self.cursor.fetchall()}

            # Recent additions (last 24 hours)
            self.cursor.execute('''
                SELECT COUNT(*) as count FROM scam_urls
                WHERE date_found >= datetime('now', '-1 day')
            ''')
            stats['added_last_24h'] = self.cursor.fetchone()['count']

            return stats

        except Exception as e:
            logger.error(f"Error getting statistics: {e}", exc_info=True)
            return {}

    def export_to_json(self, output_file: str, limit: int = 500):
        """
        Export pending URLs to JSON file for investigation.

        Args:
            output_file: Output JSON file path
            limit: Maximum number of URLs to export
        """
        try:
            urls = self.get_pending_urls(limit=limit)

            export_data = {
                'collection_date': datetime.now().isoformat(),
                'total_urls': len(urls),
                'urls': []
            }

            for url in urls:
                # Get all sources for this URL
                url_normalized = url['url_normalized']
                self.cursor.execute('''
                    SELECT source, context, source_url
                    FROM scam_urls
                    WHERE url_normalized = ?
                ''', (url_normalized,))

                sources = [row['source'] for row in self.cursor.fetchall()]

                export_data['urls'].append({
                    'url': url['url'],
                    'priority_score': url['priority_score'],
                    'sources': list(set(sources)),
                    'first_seen': url['date_found'],
                    'scam_type': url['scam_type'],
                    'context': url['context'],
                    'metadata': json.loads(url['metadata']) if isinstance(url['metadata'], str) else url['metadata']
                })

            # Write to file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Exported {len(urls)} URLs to {output_file}")

        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}", exc_info=True)

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert SQLite row to dictionary."""
        if not row:
            return {}

        result = dict(row)

        # Parse JSON metadata
        if 'metadata' in result and isinstance(result['metadata'], str):
            try:
                result['metadata'] = json.loads(result['metadata'])
            except:
                result['metadata'] = {}

        return result

    def close(self):
        """Close database connection."""
        self.conn.close()
        logger.info("Database connection closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
