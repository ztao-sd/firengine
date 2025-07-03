create user grafanareader with PASSWORD '12345';
create database firengine;
grant connect on database firengine to grafanareader;