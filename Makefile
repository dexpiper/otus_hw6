VENV = env

setup-deps:
	apt-get install python3-pip python3-dev libpq-dev curl nginx -y

setup-db:
	apt-get install postgresql postgresql-contrib -y

migrations: setup-db
	./manage.py makemigrations
	./manage.py migrate

$(VENV)/bin/activate: setup-deps
	python3 -m venv env

prod: $(VENV)/bin/activate migrations
	export DJANGO_DEBUG=False
	pip install -r requirements-prod.txt
	gunicorn -c config/gunicorn/dev.py

