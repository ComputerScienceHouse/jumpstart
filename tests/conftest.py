import coverage
import os

# Get the absolute path to the src directory
src_path = os.path.join(os.path.dirname((os.path.abspath(__file__))), "..", "src")

cov: coverage.Coverage = coverage.Coverage(source=[src_path], omit=["__init__.py"])


def pytest_sessionstart(session) -> None:
	"""
	Start the coverage session.

	Args:
	    session: The pytest session.

	Returns:
	    None
	"""

	cov.start()


def pytest_sessionfinish(session, exitstatus) -> None:
	"""
	Finish the coverage session.

	Args:
	    session: The pytest session.
	    exitstatus: The exit status of the session.

	Returns:
	    None
	"""

	cov.stop()
	cov.save()

	try:
		cov.html_report(directory="htmlcov")
		cov.xml_report(outfile="coverage.xml")
		cov.report()
	except coverage.exceptions.NoDataError:
		print("Warning: No coverage data collected")
