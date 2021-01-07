import pathlib

from nonebot import get_driver
from nonebot.adapters import Bot, Event
from nonebot.adapters.cqhttp.event import GroupMessageEvent
from nonebot.adapters.cqhttp.message import MessageSegment
from nonebot.log import logger
from nonebot.plugin import on_command

from .config import Settings
from .db import ClanManager

SERVERS = ["JP", "TC", "SC"]
RANK_GUIDE_TYPES = ["前卫", "中卫", "后卫"]

global_config = get_driver().config
settings = Settings(**global_config.dict())

cache_dir = pathlib.Path(settings.cache_dir).absolute()
db_dir = cache_dir.joinpath("db")
img_dir = cache_dir.joinpath("img")

if not db_dir.exists():
    db_dir.mkdir(parents=True)
if not img_dir.exists():
    img_dir.mkdir(parents=True)

db_name = settings.pcr_db_name
db_path = db_dir.joinpath(db_name)
db_url = f"sqlite:///{str(db_path)}"
clan_manager = ClanManager(db_url)

guide_names = settings.pcr_rank_guide_names.split(",")
if len(guide_names) != 3:
    logger.error(f"Expected 3 rank guide names, but got {len(guide_names)}")


async def _on_bot_connect(bot: Bot):
    await clan_manager.connect()


get_driver().on_bot_connect(_on_bot_connect)

# pylint: disable=invalid-name
create_clan = on_command("建会", block=True)


@create_clan.handle()
async def handle_create_clan(bot: Bot, event: GroupMessageEvent):
    msg = str(event.get_message()).strip().split()
    if len(msg) != 2:
        await create_clan.finish("输入错误")

    group_id = event.group_id
    clan_name, server = msg
    if await clan_manager.clan_exists(group_id):
        await create_clan.finish("公会已存在")
    server = server.upper()
    if server not in SERVERS:
        await create_clan.finish("服务器不合法")

    await clan_manager.create_clan(group_id, clan_name, server)
    await create_clan.finish("成功建立公会")


join_clan = on_command("入会", block=True)


@join_clan.handle()
async def handle_join_clan(bot: Bot, event: GroupMessageEvent):
    group_id = event.group_id
    if not await clan_manager.clan_exists(group_id):
        await join_clan.finish("公会尚未建立")

    user_id = event.user_id
    if await clan_manager.member_exists(group_id, user_id):
        await join_clan.finish("成员已存在")

    msg = str(event.get_message()).strip()
    if msg:
        nickname = msg
    else:
        member_info = await bot.get_group_member_info(
            group_id=group_id, user_id=user_id
        )
        nickname = member_info["nickname"]

    await clan_manager.add_member(group_id, user_id, nickname)
    await join_clan.finish("成功加入公会")


list_members = on_command("查看成员", block=True)


@list_members.handle()
async def handle_list_members(bot: Bot, event: GroupMessageEvent):
    group_id = event.group_id
    if not await clan_manager.clan_exists(group_id):
        await list_members.finish("公会尚未建立")

    nicknames = await clan_manager.list_members(group_id)
    if not nicknames:
        await list_members.finish("公会尚无成员")
    await list_members.finish("\n".join(nicknames))


rank_guides = on_command("指南", block=True)


@rank_guides.handle()
async def handle_rank_guides(bot: Bot, event: GroupMessageEvent):
    msg = str(event.get_message()).strip()
    args = msg.split()
    if len(args) != 1:
        await rank_guides.finish("输入错误")
    guide_type = args[0]
    if guide_type not in RANK_GUIDE_TYPES:
        await rank_guides.finish("输入错误")

    if guide_type == RANK_GUIDE_TYPES[0]:
        rank_guide = guide_names[0]
    elif guide_type == RANK_GUIDE_TYPES[1]:
        rank_guide = guide_names[1]
    else:
        rank_guide = guide_names[2]

    rank_guide_path = f"file:///{img_dir.joinpath(rank_guide)}"
    guide_img = MessageSegment.image(rank_guide_path)
    await rank_guides.finish(guide_img, at_sender=True)
