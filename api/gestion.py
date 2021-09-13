from discord.utils import get

idBASTION = 417445502641111051


class bcolors:
    OK = '\033[92m' #GREEN
    WARNING = '\033[93m' #YELLOW
    FAIL = '\033[91m' #RED
    RESET = '\033[0m' #RESET COLOR


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
