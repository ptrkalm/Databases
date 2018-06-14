CREATE DATABASE corp;

CREATE USER init PASSWORD 'qwerty';
ALTER USER init SUPERUSER;

CREATE TABLE employee (
      emp         int PRIMARY KEY,
      data        text,
      password    text,
      ancestors   integer[]
);

CREATE USER app PASSWORD 'qwerty';
GRANT CONNECT ON DATABASE corp TO app;
GRANT INSERT, SELECT, UPDATE, DELETE ON employee TO app;
