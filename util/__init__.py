from .arguments import Arguments
from .decorators import *
from env import env
import aiohttp, re, json, traceback, sys


def nt_name_for_discord_id(id, con):
    """
        Gets the nt username associated with the discord account if there is one.
    """

    sql = """
        SELECT *
        FROM users
        WHERE id = ?
        LIMIT 1;
    """

    c = con.cursor()
    c.execute(sql, (id,))
    user = c.fetchone()
    return user['nitro_name'] if user else None

async def upload_to_imgur(buf):
    """
    Uploads a byte array to imgur
    :param buf: The byte array to upload
    :return:
    A link to the image on imgur or None if the image could not be uploaded
    """

    # Seeking to 0
    buf.seek(0)
    data = {
        'url': 'https://api.imgur.com/3/image',
        'data': {
            'image': buf,
            'type': 'file'
        },
        'headers': {
            'Authorization': f'Client-ID {env["IMGUR_TOKEN"]}'
        }
    }

    async with aiohttp.client.post(**data) as r:
        j = await r.json()

        # Checking if request is okay
        if j is None or not j['success']:
            return None

        return j['data']['link']
