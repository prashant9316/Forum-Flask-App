-- create table users (
--     id INTEGER PRIMARY KEY autoincrement,
--     name text not null,
--     PASSWORD text not null,
--     expert boolean not null,
--     admin boolean not NULL
-- );

-- create table questions (
--     id INTEGER PRIMARY KEY autoincrement,
--     questions text NOT NULL,
--     answer text,
--     asked_by_id integer NOT NULL,
--     expert_id INTEGER not NULL

-- )

create table users
(
    id serial PRIMARY KEY,
    name text not null,
    PASSWORD text not null,
    expert boolean not null,
    admin boolean not NULL
);

create table questions
(
    id serial PRIMARY KEY,
    questions text NOT NULL,
    answer text,
    asked_by_id integer NOT NULL,
    expert_id INTEGER not NULL

)