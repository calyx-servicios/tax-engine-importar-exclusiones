Generic single-database configuration.

## Alembic DB Management

#### Modify the models as needed
- Create, Modify or Drop tables
- Modify Columns, Indexes, Constains



#### Generate Migrations

- Access into the api container in your local to do the changes. Into the /code/app directory

```bash
➜  tax-engine-bot-arba-padron git:(feature/API-004_database_migration) ✗ docker exec -it tax-engine-bot-arba-padron_api_1 /bin/bash
08:31:04 root@b26f72c5c392 code ±|feature/API-004_database_migration ✗|→ cd app
/code/app
```

- Autogenerate the migrations
```bash
08:31:06 root@b26f72c5c392 app ±|feature/API-004_database_migration ✗|→ alembic revision --autogenerate -m test
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.autogenerate.compare] Detected added column 'arba_data.test'
  Generating /code/app/alembic/versions/3a7d97388af0_test.py ...  done
  Running post write hook "black" ...
reformatted /code/app/alembic/versions/3a7d97388af0_test.py

All done! ✨ 🍰 ✨
1 file reformatted.
  done
```


#### Apply changes to database
alembic upgrade head

```bash
08:31:44 root@b26f72c5c392 app ±|feature/API-004_database_migration ✗|→ alembic upgrade head
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade 29ab91b71644 -> 3a7d97388af0, test
```