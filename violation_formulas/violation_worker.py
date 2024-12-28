"""Worker classes for violation detection and processing.

This module provides worker classes for handling violation detection and processing
in separate threads. It includes base classes and specific implementations for
different types of violation processing tasks.
"""

import sqlite3

from PyQt5.QtCore import (
    QObject,
    QThread,
    pyqtSignal,
)


class BaseWorker(QObject):
    """Base worker class for violation processing tasks.

    Provides common functionality and signals for all worker implementations.
    """

    finished = pyqtSignal()  # Emitted when worker completes
    error = pyqtSignal(str)  # Emitted on error with error message
    progress = pyqtSignal(int, str)  # Emitted to update progress (value, message)
    result = pyqtSignal(object)  # Emitted with the worker's result

    def __init__(self):
        super().__init__()
        self._is_cancelled = False

    def cancel(self):
        """Mark the worker for cancellation."""
        self._is_cancelled = True

    def check_cancelled(self):
        """Check if the worker has been cancelled.

        Raises:
            RuntimeError: If the worker has been cancelled
        """
        if self._is_cancelled:
            raise RuntimeError("Operation cancelled by user")


class DataFetchWorker(BaseWorker):
    """Worker for fetching data from the database."""

    def __init__(self, db_path, start_date, end_date):
        super().__init__()
        self.db_path = db_path
        self.start_date = start_date
        self.end_date = end_date

    def run(self):
        """Fetch data from database."""
        try:
            import pandas as pd

            self.progress.emit(0, "Connecting to database...")
            self.check_cancelled()

            # Connect to database
            conn = sqlite3.connect(self.db_path)

            # Fetch carrier data
            self.progress.emit(25, "Fetching carrier data...")
            carrier_data = pd.read_sql_query(
                """
                SELECT DISTINCT carrier_name, list_status
                FROM carriers
                """,
                conn,
            )

            # Fetch clock ring data
            self.progress.emit(50, "Fetching clock ring data...")
            clock_ring_data = pd.read_sql_query(
                """
                SELECT *
                FROM rings3
                WHERE DATE(rings_date) BETWEEN DATE(?) AND DATE(?)
                """,
                conn,
                params=(
                    self.start_date.strftime("%Y-%m-%d"),
                    self.end_date.strftime("%Y-%m-%d"),
                ),
            )

            # Merge data
            self.progress.emit(75, "Processing data...")
            merged_data = pd.merge(
                clock_ring_data, carrier_data, on="carrier_name", how="left"
            )

            self.progress.emit(100, "Data fetch complete")
            self.result.emit(merged_data)
            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))
        finally:
            if "conn" in locals():
                conn.close()


class ViolationDetectionWorker(BaseWorker):
    """Worker for detecting violations in clock ring data."""

    def __init__(self, clock_ring_data, violation_type, date_maximized_status=None):
        super().__init__()
        self.clock_ring_data = clock_ring_data
        self.violation_type = violation_type
        self.date_maximized_status = date_maximized_status or {}

    def run(self):
        """Process violations for the given data and type."""
        try:
            from violation_detection import detect_violations

            self.progress.emit(0, f"Detecting {self.violation_type} violations...")
            self.check_cancelled()

            # Process violations in chunks for progress updates
            violations = detect_violations(
                self.clock_ring_data, self.violation_type, self.date_maximized_status
            )

            self.progress.emit(100, "Violation detection complete")
            self.result.emit({self.violation_type: violations})
            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))


class RemedyCalculationWorker(BaseWorker):
    """Worker for calculating violation remedies."""

    def __init__(self, violation_data, clock_ring_data):
        super().__init__()
        self.violation_data = violation_data
        self.clock_ring_data = clock_ring_data

    def run(self):
        """Calculate remedies for detected violations."""
        try:
            from violation_detection import get_violation_remedies

            self.progress.emit(0, "Calculating remedies...")
            self.check_cancelled()

            # Calculate remedies
            remedies = get_violation_remedies(self.clock_ring_data, self.violation_data)

            self.progress.emit(100, "Remedy calculation complete")
            self.result.emit(remedies)
            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))


class DateRangeProcessor(QObject):
    """Coordinates the processing of a date range selection."""

    finished = pyqtSignal()  # Signal when all processing is complete

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.workers = []
        self.threads = []
        self.progress_callback = None
        self.error_callback = None
        self.finished_callback = None
        self.clock_ring_data = None
        self.active_violations = {}
        self.completed_workers = 0
        self.total_workers = 0
        self.error_occurred = False  # Track if any error occurred

    def set_callbacks(self, progress_cb=None, error_cb=None, finished_cb=None):
        """Set callbacks for worker progress updates."""
        self.progress_callback = progress_cb
        self.error_callback = error_cb
        self.finished_callback = finished_cb

    def register_worker(self, worker, thread):
        """Register a worker and connect its signals."""
        # Connect signals if callbacks are set
        if self.progress_callback:
            worker.progress.connect(self.progress_callback)
        if self.error_callback:
            worker.error.connect(self._handle_error)  # Use our error handler

        # Connect cleanup handlers
        worker.finished.connect(self._handle_worker_finished)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda: self._cleanup_thread(thread))

        # Store references
        self.workers.append(worker)
        self.threads.append(thread)
        self.total_workers += 1

    def _handle_worker_finished(self):
        """Handle completion of any worker."""
        self.completed_workers += 1

        # If all workers are done or there was an error, emit finished signal and cleanup
        if self.completed_workers == self.total_workers or self.error_occurred:
            if self.finished_callback:
                self.finished_callback()
            self.finished.emit()
            self.cleanup_all()

    def _cleanup_thread(self, thread):
        """Clean up a specific thread."""
        if thread in self.threads:
            self.threads.remove(thread)

    def cleanup_all(self):
        """Clean up all workers and threads."""
        # Wait for threads to finish
        for thread in self.threads[:]:  # Copy list since we'll modify it
            if thread.isRunning():
                thread.quit()
                thread.wait()
                thread.deleteLater()

        # Clear all references
        self.workers.clear()
        self.threads.clear()
        self.completed_workers = 0
        self.total_workers = 0
        self.clock_ring_data = None
        self.active_violations.clear()

    def cancel_all(self):
        """Cancel all running workers and clean up."""
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()

        # Clean up everything
        self.cleanup_all()

    def process_date_range(self, start_date, end_date, db_path):
        """Process the selected date range.

        Args:
            start_date: Start date of the range
            end_date: End date of the range
            db_path: Path to the database
        """
        # Create and start data fetch worker
        fetch_thread = QThread()
        fetch_worker = DataFetchWorker(db_path, start_date, end_date)

        # Move worker to thread
        fetch_worker.moveToThread(fetch_thread)

        # Connect signals
        fetch_thread.started.connect(fetch_worker.run)
        fetch_worker.finished.connect(fetch_thread.quit)
        fetch_worker.finished.connect(fetch_worker.deleteLater)
        fetch_thread.finished.connect(fetch_thread.deleteLater)

        # Store clock ring data for other workers
        fetch_worker.result.connect(self._store_clock_ring_data)

        # Register worker and connect signals
        self.register_worker(fetch_worker, fetch_thread)

        # Start processing
        fetch_thread.start()

    def _store_clock_ring_data(self, data):
        """Store clock ring data and start violation detection."""
        self.clock_ring_data = data
        if data is not None:
            # Start violation detection workers for implemented violation types only
            for violation_type in ["8.5.D", "8.5.F", "8.5.G"]:  # Only implemented types
                self._start_violation_detection(data, violation_type)

    def _handle_violation_detection_complete(self, violations, violation_type):
        """Handle completion of violation detection worker."""
        if violations is not None:
            self.active_violations.update(violations)

        # If this was the last violation detection, start remedy calculation
        if (
            len(self.active_violations) == 3
        ):  # Updated to match number of violation types
            self._start_remedy_calculation(self.active_violations)

    def _start_violation_detection(self, clock_ring_data, violation_type):
        """Start a violation detection worker for a specific type."""
        thread = QThread()
        worker = ViolationDetectionWorker(clock_ring_data, violation_type)

        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        # Register worker and connect signals
        self.register_worker(worker, thread)

        worker.result.connect(
            lambda result: self._handle_violation_detection_complete(
                result, violation_type
            )
        )

        thread.start()

    def _start_remedy_calculation(self, violations):
        """Start the remedy calculation worker."""
        thread = QThread()
        worker = RemedyCalculationWorker(violations, self.clock_ring_data)

        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        # Register worker and connect signals
        self.register_worker(worker, thread)

        worker.result.connect(self._handle_remedy_calculation_complete)

        thread.start()

    def _handle_remedy_calculation_complete(self, remedies):
        """Handle completion of remedy calculation worker."""
        if remedies is None:
            return

        # Update UI with final results
        if self.parent and hasattr(self.parent, "update_violations_and_remedies"):
            self.parent.update_violations_and_remedies(remedies)

    def _handle_error(self, error_msg):
        """Handle worker errors."""
        self.error_occurred = True
        if self.error_callback:
            self.error_callback(error_msg)
        # Trigger cleanup on error
        self._handle_worker_finished()
