"""
Backup controller for POS application.
Handles database backup and restore operations.
"""

import os
import time
import datetime
import subprocess
import shutil
import gzip
import threading


class BackupController:
    """Controller for backup operations."""
    
    def __init__(self, db):
        """Initialize controller with database connection.
        
        Args:
            db: Database connection instance
        """
        self.db = db
        self.backup_dir = "backups"
        self.ensure_backup_dir()
        self.ensure_tables()
        self.auto_backup_thread = None
        self.stop_auto_backup = False
        
    def ensure_tables(self):
        """Ensure that the necessary database tables exist."""
        # Create backups table if it doesn't exist
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS backups (
                backup_id VARCHAR(36) PRIMARY KEY,
                backup_name VARCHAR(100) NOT NULL,
                file_path VARCHAR(255) NOT NULL,
                file_size BIGINT NOT NULL,
                compressed BOOLEAN NOT NULL DEFAULT FALSE,
                description TEXT,
                created_at TIMESTAMP NOT NULL
            )
        """)
        
        # Create restore_logs table if it doesn't exist
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS restore_logs (
                restore_id VARCHAR(36) PRIMARY KEY,
                backup_id VARCHAR(36) NOT NULL,
                file_path VARCHAR(255) NOT NULL,
                restore_date TIMESTAMP NOT NULL,
                status VARCHAR(20) NOT NULL,
                message TEXT,
                CONSTRAINT fk_backup_id
                    FOREIGN KEY (backup_id)
                    REFERENCES backups(backup_id)
                    ON DELETE CASCADE
            )
        """)
    
    def ensure_backup_dir(self):
        """Create backup directory if it doesn't exist."""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def create_backup(self, compress=True, description=None):
        """Create a database backup.
        
        Args:
            compress (bool, optional): Whether to compress the backup
            description (str, optional): Description of the backup
            
        Returns:
            dict: Backup result information or error message
            
        Raises:
            Exception: If backup fails
        """
        # Create a timestamp for the backup filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"pos_backup_{timestamp}"
        
        # Full paths
        sql_path = os.path.join(self.backup_dir, f"{backup_name}.sql")
        gz_path = os.path.join(self.backup_dir, f"{backup_name}.sql.gz")
        
        try:
            # Get database connection info
            db_host = os.environ.get("PGHOST", "localhost")
            db_port = os.environ.get("PGPORT", "5432")
            db_name = os.environ.get("PGDATABASE", "pos_db")
            db_user = os.environ.get("PGUSER", "postgres")
            db_password = os.environ.get("PGPASSWORD", "")
            
            # Set environment for pg_dump
            env = os.environ.copy()
            env["PGPASSWORD"] = db_password
            
            # Run pg_dump to create backup
            pg_dump_cmd = [
                "pg_dump",
                "-h", db_host,
                "-p", db_port,
                "-U", db_user,
                "-F", "p",  # plain text format
                "-f", sql_path,
                db_name
            ]
            
            # Execute pg_dump
            process = subprocess.run(
                pg_dump_cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if process.returncode != 0:
                raise Exception(f"pg_dump failed: {process.stderr}")
            
            # Compress the backup if requested
            final_path = sql_path
            if compress:
                with open(sql_path, 'rb') as f_in:
                    with gzip.open(gz_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                # Remove the uncompressed file
                os.remove(sql_path)
                final_path = gz_path
            
            # Get file size
            file_size = os.path.getsize(final_path)
            
            # Log the backup
            backup_info = self._log_backup(
                backup_name,
                final_path,
                file_size,
                compress,
                description
            )
            
            return {
                "success": True,
                "backup_id": backup_info["backup_id"],
                "filename": os.path.basename(final_path),
                "file_size": file_size,
                "compressed": compress,
                "path": final_path,
                "timestamp": timestamp
            }
            
        except Exception as e:
            # Clean up any partial files
            if os.path.exists(sql_path):
                os.remove(sql_path)
            if os.path.exists(gz_path):
                os.remove(gz_path)
            
            return {
                "success": False,
                "error": str(e)
            }
    
    def restore_backup(self, backup_id=None, backup_path=None):
        """Restore a database from backup.
        
        Args:
            backup_id (str, optional): ID of the backup to restore
            backup_path (str, optional): Path to backup file to restore
            
        Returns:
            dict: Restore result information or error message
            
        Raises:
            Exception: If restore fails
        """
        if not backup_id and not backup_path:
            raise ValueError("Either backup_id or backup_path must be provided")
        
        try:
            # Get backup path from ID if provided
            if backup_id:
                backup_info = self.get_backup_by_id(backup_id)
                if not backup_info:
                    raise ValueError(f"Backup with ID {backup_id} not found")
                backup_path = backup_info["file_path"]
            
            if not os.path.exists(backup_path):
                raise ValueError(f"Backup file not found: {backup_path}")
            
            # Get database connection info
            db_host = os.environ.get("PGHOST", "localhost")
            db_port = os.environ.get("PGPORT", "5432")
            db_name = os.environ.get("PGDATABASE", "pos_db")
            db_user = os.environ.get("PGUSER", "postgres")
            db_password = os.environ.get("PGPASSWORD", "")
            
            # Set environment for psql
            env = os.environ.copy()
            env["PGPASSWORD"] = db_password
            
            # Check if the backup is compressed
            is_compressed = backup_path.endswith('.gz')
            
            # Create a temporary file for decompression if needed
            temp_file = None
            restore_path = backup_path
            
            if is_compressed:
                temp_file = os.path.join(self.backup_dir, "temp_restore.sql")
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(temp_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                restore_path = temp_file
            
            # Create a temporary SQL script to drop existing connections
            drop_conn_sql = """
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '%s'
              AND pid <> pg_backend_pid();
            """ % db_name
            
            drop_conn_path = os.path.join(self.backup_dir, "drop_connections.sql")
            with open(drop_conn_path, 'w') as f:
                f.write(drop_conn_sql)
            
            # Execute drop connections SQL
            psql_drop_cmd = [
                "psql",
                "-h", db_host,
                "-p", db_port,
                "-U", db_user,
                "-d", "postgres",  # connect to default database
                "-f", drop_conn_path
            ]
            
            subprocess.run(
                psql_drop_cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Drop and recreate the database
            subprocess.run(
                ["psql", "-h", db_host, "-p", db_port, "-U", db_user, "-d", "postgres", "-c", f"DROP DATABASE IF EXISTS {db_name}"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            subprocess.run(
                ["psql", "-h", db_host, "-p", db_port, "-U", db_user, "-d", "postgres", "-c", f"CREATE DATABASE {db_name}"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Restore the database
            psql_cmd = [
                "psql",
                "-h", db_host,
                "-p", db_port,
                "-U", db_user,
                "-d", db_name,
                "-f", restore_path
            ]
            
            process = subprocess.run(
                psql_cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Clean up temporary files
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)
            
            if os.path.exists(drop_conn_path):
                os.remove(drop_conn_path)
            
            if process.returncode != 0:
                raise Exception(f"Database restore failed: {process.stderr}")
            
            # Log the restore
            restore_info = {
                "restore_id": self._generate_id(),
                "backup_id": backup_id,
                "file_path": backup_path,
                "restore_date": datetime.datetime.now().isoformat(),
                "success": True
            }
            
            self._log_restore(restore_info)
            
            return {
                "success": True,
                "message": "Database restored successfully",
                "restore_id": restore_info["restore_id"],
                "backup_id": backup_id,
                "timestamp": restore_info["restore_date"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_backups(self, limit=20, offset=0):
        """List available backups.
        
        Args:
            limit (int, optional): Maximum number of records to return
            offset (int, optional): Number of records to skip
            
        Returns:
            list: List of backup information
        """
        query = """
            SELECT * FROM backups
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        return self.db.fetch_all(query, (limit, offset))
    
    def get_backup_by_id(self, backup_id):
        """Get backup information by ID.
        
        Args:
            backup_id (str): Backup ID
            
        Returns:
            dict: Backup information or None if not found
        """
        query = "SELECT * FROM backups WHERE backup_id = %s"
        return self.db.fetch_one(query, (backup_id,))
    
    def delete_backup(self, backup_id):
        """Delete a backup file and its record.
        
        Args:
            backup_id (str): Backup ID
            
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            ValueError: If backup not found
        """
        # Get backup info
        backup_info = self.get_backup_by_id(backup_id)
        if not backup_info:
            raise ValueError(f"Backup with ID {backup_id} not found")
        
        # Delete file
        file_path = backup_info["file_path"]
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete record
        query = "DELETE FROM backups WHERE backup_id = %s"
        self.db.execute(query, (backup_id,))
        
        return True
    
    def start_auto_backup(self, interval_hours=24):
        """Start automatic backup in a separate thread.
        
        Args:
            interval_hours (int, optional): Interval between backups in hours
            
        Returns:
            bool: True if started successfully
        """
        if self.auto_backup_thread and self.auto_backup_thread.is_alive():
            return False  # Already running
        
        self.stop_auto_backup = False
        self.auto_backup_thread = threading.Thread(
            target=self._auto_backup_thread,
            args=(interval_hours,),
            daemon=True
        )
        self.auto_backup_thread.start()
        
        return True
    
    def stop_auto_backup_thread(self):
        """Stop the automatic backup thread."""
        self.stop_auto_backup = True
        if self.auto_backup_thread:
            self.auto_backup_thread.join(timeout=1.0)
    
    def _auto_backup_thread(self, interval_hours):
        """Thread function for automatic backups.
        
        Args:
            interval_hours (int): Interval between backups in hours
        """
        interval_seconds = interval_hours * 3600
        
        while not self.stop_auto_backup:
            # Create a backup
            self.create_backup(compress=True, description="Automatic backup")
            
            # Sleep for the interval, checking periodically if we should stop
            for _ in range(interval_seconds // 10):
                if self.stop_auto_backup:
                    break
                time.sleep(10)
    
    def get_backup_status(self):
        """Get the status of automatic backups.
        
        Returns:
            dict: Backup status information
        """
        # Get the most recent backup
        query = """
            SELECT * FROM backups
            ORDER BY created_at DESC
            LIMIT 1
        """
        latest_backup = self.db.fetch_one(query)
        
        # Get count of backups
        query = "SELECT COUNT(*) as count FROM backups"
        count_result = self.db.fetch_one(query)
        backup_count = count_result["count"] if count_result else 0
        
        # Calculate total size
        query = "SELECT SUM(file_size) as total_size FROM backups"
        size_result = self.db.fetch_one(query)
        total_size = size_result["total_size"] if size_result and size_result["total_size"] else 0
        
        return {
            "auto_backup_running": self.auto_backup_thread is not None and self.auto_backup_thread.is_alive(),
            "latest_backup": latest_backup,
            "backup_count": backup_count,
            "total_size": total_size
        }
    
    def _log_backup(self, backup_name, file_path, file_size, compressed, description=None):
        """Log a backup operation to the database.
        
        Args:
            backup_name (str): Backup name
            file_path (str): Path to backup file
            file_size (int): Size of backup file in bytes
            compressed (bool): Whether the backup is compressed
            description (str, optional): Description of the backup
            
        Returns:
            dict: Backup information
        """
        backup_id = self._generate_id()
        now = datetime.datetime.now().isoformat()
        
        # Insert backup record
        query = """
            INSERT INTO backups (
                backup_id, backup_name, file_path, file_size, 
                compressed, description, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """
        params = (backup_id, backup_name, file_path, file_size, compressed, description, now)
        
        return self.db.fetch_one(query, params)
    
    def _log_restore(self, restore_info):
        """Log a restore operation to the database.
        
        Args:
            restore_info (dict): Information about the restore operation
            
        Returns:
            dict: Restore information
        """
        
        # Insert restore record
        query = """
            INSERT INTO restore_logs (
                restore_id, backup_id, file_path, restore_date, status, message
            ) VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING *
        """
        # Convert success boolean to string status
        status = "SUCCESS" if restore_info["success"] else "FAILED"
        
        params = (
            restore_info["restore_id"],
            restore_info.get("backup_id"),
            restore_info["file_path"],
            restore_info["restore_date"],
            status,
            restore_info.get("error")
        )
        
        return self.db.fetch_one(query, params)
    
    def _generate_id(self):
        """Generate a unique ID.
        
        Returns:
            str: Unique ID
        """
        import uuid
        return str(uuid.uuid4())
