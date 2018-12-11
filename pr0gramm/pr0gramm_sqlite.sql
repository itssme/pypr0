-- sql file designed for sqlite3

PRAGMA foreign_keys = ON;

begin transaction;

create table users (
    name varchar(256) primary key,
    id int,
    registered int,
    admin tinyint,
    banned tinyint,
    bannedUntil int,
    mark int,
    score int,
    tags int,
    likes int,
    comments int,
    followers int
);

create table posts (
    id int primary key,
    user varchar(256) references users,
    promoted int,
    up int,
    down int,
    created int,
    image varchar(256),
    thumb varchar(256),
    fullsize varchar(256),
    width int,
    height int,
    audio tinyint,
    source varchar(1024),
    flags int,
    mark int,
    deleted int
);

create table comments (
    id integer primary key,
    comment text,
    user varchar(256) references users,
    parent int references comments,
    created int,
    up int,
    down int,
    confidence float,
    mark int
);

create table comment_assignments (
    post int references posts,
    comment int references comments,
    primary key(post, comment)
);

insert into comments values(0, Null, Null, 0, 0, 0, 0, 0, 0);
insert into comment_assignments values(Null, 0);

create table tags (
    id integer primary key AUTOINCREMENT,
    tag varchar(256) unique
);

create table tag_assignments (
    post int references posts,
    tag int primary key,
    id int references tags,
    confidence float
);

commit;