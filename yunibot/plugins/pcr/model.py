import sqlalchemy

metadata = sqlalchemy.MetaData()
clans = sqlalchemy.Table(
    "clans",
    metadata,
    sqlalchemy.Column("group_id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("clan_name", sqlalchemy.String),
    sqlalchemy.Column("server", sqlalchemy.String),
)
members = sqlalchemy.Table(
    "members",
    metadata,
    sqlalchemy.Column(
        "group_id",
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey("clans.group_id"),
        primary_key=True,
    ),
    sqlalchemy.Column("user_id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("nickname", sqlalchemy.String),
)