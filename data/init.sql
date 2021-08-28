create table if not exists users
(
    user_id           unsigned bigint not null
        constraint users_pk
            primary key,

    balance           unsigned int default 50 not null,
    last_free_credits unsigned int default 0 not null
);

create table if not exists transactions
(
    id         INTEGER         not null
        constraint transactions_pk
            primary key autoincrement,

    user_id    unsigned bigint not null,
    amount     int             not null,
    refundable boolean         not null default false,
    reason     varchar(64),
    date       timestamp                default current_timestamp,

    Foreign Key (user_id) References users (user_id) On Delete Cascade
);

create unique index if not exists transactions_id_uindex
    on transactions (id);
