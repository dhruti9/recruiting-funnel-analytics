.PHONY: install data build docs dashboard all clean

install:
	pip install -r requirements.txt

data:
	python data_generator/generate.py --out data/raw

build:
	cd dbt_project && dbt build --profiles-dir .

docs:
	cd dbt_project && dbt docs generate --profiles-dir . && dbt docs serve --profiles-dir .

dashboard:
	python scripts/export_for_dashboard.py

all: data build dashboard

clean:
	rm -rf data/raw dbt_project/target dbt_project/*.duckdb
