import random
from nonebot import require, logger, get_bot
from nonebot.exception import ActionFailed
from nonebot.adapters.onebot.v11 import Message

from src.plugins.repeater.model import Chat
from src.common.config import BotConfig
from src.common.utils import is_bot_admin

change_name_sched = require('nonebot_plugin_apscheduler').scheduler


@change_name_sched.scheduled_job('cron', minute='*/1')
async def change_name():
    rand_messages = Chat.get_random_message_from_each_group()
    if not rand_messages:
        return

    for group_id, target_msg in rand_messages.items():
        if random.random() > 0.002:  # 期望约每8个多小时改一次
            continue

        bot_id = target_msg['bot_id']
        config = BotConfig(bot_id, group_id)
        if config.is_sleep():
            continue

        target_user_id = target_msg['user_id']
        logger.info(
            'rename | bot [{}] ready to change name by using [{}] in group [{}]'.format(
                bot_id, target_user_id, group_id))
        try:
            # 获取群友昵称
            info = await get_bot(str(bot_id)).call_api('get_group_member_info', **{
                'group_id': group_id,
                'user_id': target_user_id,
                'no_cache': True
            })
        except ActionFailed:
            # 可能这人退群了
            continue

        card = info['card'] if info['card'] else info['nickname']
        logger.info(
            'rename | bot [{}] ready to change name to[{}] in group [{}]'.format(
                bot_id, card, group_id))
        try:
            # 改牛牛自己的群名片
            await get_bot(str(bot_id)).call_api('set_group_card', **{
                'group_id': group_id,
                'user_id': bot_id,
                'card': card
            })

            # 酒后夺舍！改群友的！
            if config.drunkenness() and is_bot_admin(bot_id, group_id, True):
                await get_bot(str(bot_id)).call_api('set_group_card', **{
                    'group_id': group_id,
                    'user_id': target_user_id,
                    'card': random.choice(['帕拉斯', '牛牛', '牛牛喝酒', '牛牛干杯', '牛牛继续喝'])
                })

            # 戳一戳
            await get_bot(str(bot_id)).call_api('send_group_msg', **{
                'message': Message('[CQ:poke,qq={}]'.format(target_user_id)),
                'group_id': group_id
            })

        except ActionFailed:
            # 可能牛牛退群了
            continue
