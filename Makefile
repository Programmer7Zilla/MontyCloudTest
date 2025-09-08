.PHONY: help install start stop setup test status restart full-setup clean

help:
	@echo "Image Service Management Commands:"
	@echo "=================================="
	@echo "install     - Install Python dependencies"
	@echo "start       - Start LocalStack services"
	@echo "stop        - Stop LocalStack services"
	@echo "setup       - Setup AWS infrastructure"
	@echo "test        - Run API tests"
	@echo "status      - Check service status"
	@echo "restart     - Restart LocalStack"
	@echo "full-setup  - Complete setup (install + start + setup + test)"
	@echo "clean       - Clean up all resources"
	@echo ""
	@echo "Quick start: make full-setup"

install:
	@python manage.py install

start:
	@python manage.py start

stop:
	@python manage.py stop

setup:
	@python manage.py setup

test:
	@python manage.py test

status:
	@python manage.py status

restart:
	@python manage.py restart

full-setup:
	@python manage.py full-setup

clean:
	@echo "Cleaning up LocalStack resources..."
	@docker-compose down -v
	@docker system prune -f
	@echo "✓ Cleanup completed"
