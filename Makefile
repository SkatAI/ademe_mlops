format:
# format
	black -l 100 **/*.py

lint:
# linting
	pylint --disable=C0301,C0413,C0103 **/*.py