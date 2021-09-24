from discord.utils import get

idBASTION = 417445502641111051


class bcolors:
	end = '\033[0m'
	black = '\033[30m'
	white = '\033[37m'
	red = '\033[31m'
	green = '\033[32m'
	yellow = '\033[33m'
	blue = '\033[34m'
	purple = '\033[35m'
	lightblue = '\033[36m'


async def addrole(member, role):
    setrole = get(member.guild.roles, name=role)
    if setrole != None:
        await member.add_roles(setrole)
    else:
        await print("Role introuvable")


async def removerole(member, role):
    setrole = get(member.guild.roles, name=role)
    if setrole != None:
        await member.remove_roles(setrole)
    else:
        await print("Role introuvable")


def lvlPalier(lvl):
    if lvl <= 0:
        return 10
    else:
        return int(30 * (lvl)**(2.5))
