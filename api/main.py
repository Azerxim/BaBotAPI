from typing import List

import asyncio
import discord
from discord.ext import commands
from discord.ext.commands import Bot
from discord.utils import get
import time as t, datetime as dt

from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader, APIKey
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, HTMLResponse

from . import crud, models, schemas
from . import gestion as ge, stats
from .database import SessionLocal, engine


models.Base.metadata.create_all(bind=engine)

# initialisation des variables.
PREFIX = "!api "
VERSION = open("config/version.txt").read().replace("\n", "")
TOKEN = open("config/token.txt", "r").read().replace("\n", "")
intents = discord.Intents(
    messages=True,
    guilds=True,
    members=True,
    emojis=True,
    voice_states=True,
    presences=True,
    guild_messages=True,
    dm_messages=True,
    reactions=True,
    guild_reactions=True,
    dm_reactions=True
)
SECRET_KEY = open("config/key.txt", "r").read().replace("\n", "")
SECRET_KEY_NAME = "access_token"
client = commands.Bot(command_prefix = "{p}".format(p=PREFIX), intents=intents)

app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


################# Security #####################

api_key_header = APIKeyHeader(name=SECRET_KEY_NAME)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == SECRET_KEY:
        return api_key_header
    else:
        raise HTTPException(status_code=403, detail="Could not validate credentials")


################### API ########################
client.remove_command("help")

# client.load_extension('core.stats')

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(client.start(TOKEN))
    await asyncio.sleep(2)
    print(f'{ge.bcolors.green}DISCORD{ge.bcolors.end}:  Connecté avec le nom {ge.bcolors.lightblue}{client.user}{ge.bcolors.end}')
    print(f'{ge.bcolors.green}DISCORD{ge.bcolors.end}:  Prefix {PREFIX}')
    print(f'{ge.bcolors.green}DISCORD{ge.bcolors.end}:  Version {ge.bcolors.lightblue}{VERSION}{ge.bcolors.end}')


@app.get("/", response_class=HTMLResponse)
def html_main():
    path = "html/index.html"
    html_content = open(path).read()
    return HTMLResponse(content=html_content, status_code=200)


@app.get("/version/")
def app_version():
    return {'api': 'BaBot', 'version': VERSION}


# ========= Info Global =========
@app.get("/infos/", tags=["Infos"])
def read_global_info(db: Session = Depends(get_db)):
    infos = {}
    # Devise
    res = crud.countTotalDevise(db=db)
    if res is None:
        res = {}
    infos['Devise'] = res
    # Super Devise
    res = crud.countTotalSuperDevise(db=db)
    if res is None:
        res = {}
    infos['Super Devise'] = res
    # Super Devise
    res = crud.countTotalMsg(db=db)
    if res is None:
        res = {}
    infos['Messages'] = res
    # Super Devise
    res = crud.countTotalXP(db=db)
    if res is None:
        res = {}
    infos['XP'] = res
    # Taille
    res = crud.taille(db=db)
    if res is None:
        res = {}
    infos['Total Players'] = res
    return JSONResponse(content=jsonable_encoder(infos))


@app.get("/infos/devise/", tags=["Infos"])
def read_global_devise(db: Session = Depends(get_db)):
    res = crud.countTotalDevise(db=db)
    if res is None:
        res = {}
    return JSONResponse(content=jsonable_encoder(res))


@app.get("/infos/super_devise/", tags=["Infos"])
def read_global_super_devise(db: Session = Depends(get_db)):
    res = crud.countTotalSuperDevise(db=db)
    if res is None:
        res = {}
    return JSONResponse(content=jsonable_encoder(res))


@app.get("/infos/msg/", tags=["Infos"])
def read_global_message(db: Session = Depends(get_db)):
    res = crud.countTotalMsg(db=db)
    if res is None:
        res = {}
    return JSONResponse(content=jsonable_encoder(res))


@app.get("/infos/xp/", tags=["Infos"])
def read_global_xp(db: Session = Depends(get_db)):
    res = crud.countTotalXP(db=db)
    if res is None:
        res = {}
    return JSONResponse(content=jsonable_encoder(res))


@app.get("/infos/nb_player/", tags=["Infos"])
def get_nb_player(db: Session = Depends(get_db)):
    res = crud.taille(db=db)
    if res is None:
        raise HTTPException(status_code=400, detail="Database not found")
    return res


# ========= Classement =========
@app.get("/infos/top/xp/", tags=["Classement"])
def read_global_top_xp(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    res = crud.topxp(db=db, min=skip, max=limit)
    if res is None:
        res = {}
    return JSONResponse(content=jsonable_encoder(res))


@app.get("/infos/top/level/", tags=["Classement"])
def read_global_top_level(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    res = crud.toplevel(db=db, min=skip, max=limit)
    if res is None:
        res = {}
    return JSONResponse(content=jsonable_encoder(res))


@app.get("/infos/top/msg/", tags=["Classement"])
def read_global_top_messages(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    res = crud.topmsg(db=db, min=skip, max=limit)
    if res is None:
        res = {}
    return JSONResponse(content=jsonable_encoder(res))


@app.get("/infos/top/reaction/", tags=["Classement"])
def read_global_top_reaction(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    res = crud.topreaction(db=db, min=skip, max=limit)
    if res is None:
        res = {}
    return JSONResponse(content=jsonable_encoder(res))


# ========= Users =========
@app.get("/users/playerid/{discord_id}", tags=["Users"])
def get_playerID(discord_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_PlayerID(db=db, discord_id=discord_id, platform="discord")
    if db_user is None:
        res = {'error': 404, 'ID': 0}
    else:
        res = {'error': 0, 'ID': "{}".format(db_user.playerid)}
    return JSONResponse(content=jsonable_encoder(res))


@app.post("/users/create/", tags=["Users"])
def create_user(discord_id: str, db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    db_user = crud.get_user_discord_id(db, discord_id=discord_id)
    if db_user:
        raise HTTPException(status_code=400, detail="Discord ID already registered")
    return crud.create_user(db=db, discord_id=str(discord_id))


@app.get("/users/", response_model=List[schemas.TableCore], tags=["Users"])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db=db, skip=skip, limit=limit)
    func = {'error': 0, 'etat': 'OK', 'skip': skip, 'limit': limit, 'users': users}
    return JSONResponse(content=jsonable_encoder(func))


@app.get("/users/{PlayerID}", response_model=schemas.TableCore, tags=["Users"])
def read_user(PlayerID: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db=db, PlayerID=PlayerID)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


# @app.get("/users/old/", response_model=List[schemas.TableCoreOld], tags=["Users"])
# def old_read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     users = crud.get_users_old(db=db, skip=skip, limit=limit)
#     return users
#
#
# @app.get("/users/old/{PlayerID}", response_model=schemas.TableCoreOld, tags=["Users"])
# def old_read_user(PlayerID: int, db: Session = Depends(get_db)):
#     db_user = crud.get_user_old(db=db, PlayerID=PlayerID)
#     if db_user is None:
#         raise HTTPException(status_code=404, detail="User not found")
#     return db_user

# ----- Devise -----
@app.get("/users/devise/{PlayerID}", tags=["Users"])
def user_devise(PlayerID: int, db: Session = Depends(get_db)):
    val = crud.value(db, PlayerID, "core", "devise")
    func = {'error': 0, 'etat': 'OK', 'devise': val}
    if val is None:
        raise HTTPException(status_code=404, detail="User not found")
    return JSONResponse(content=jsonable_encoder(func))


@app.put("/users/devise/{PlayerID}/{nb}", tags=["Users"])
def add_devise(PlayerID: int, nb: int, db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    try:
        bal = crud.value(db, PlayerID, "core", "devise")
        ns = bal + int(nb)
        if ns <= 0:
            ns = 0
        crud.update(db, PlayerID, "core", "devise", ns)
        func = {'error': 0, 'etat': 'OK', 'newvalue': ns, 'oldvalue': bal}
    except:
        func = {'error': 1, 'etat': 'NOK'}
    return JSONResponse(content=jsonable_encoder(func))


# ----- Super Devise -----
@app.get("/users/super_devise/{PlayerID}", tags=["Users"])
def user_super_devise(PlayerID: int, db: Session = Depends(get_db)):
    val = crud.value(db, PlayerID, "core", "super_devise")
    func = {'error': 0, 'etat': 'OK', 'super_devise': val}
    if val is None:
        raise HTTPException(status_code=404, detail="User not found")
    return JSONResponse(content=jsonable_encoder(func))


@app.put("/users/super_devise/{PlayerID}/{nb}", tags=["Users"])
def add_super_devise(PlayerID: int, nb: int, db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    try:
        bal = crud.value(db, PlayerID, "core", "super_devise")
        ns = bal + int(nb)
        if ns <= 0:
            ns = 0
        crud.update(db, PlayerID, "core", "super_devise", ns)
        func = {'error': 0, 'etat': 'OK', 'newvalue': ns, 'oldvalue': bal}
    except:
        func = {'error': 1, 'etat': 'NOK'}
    return JSONResponse(content=jsonable_encoder(func))


# ----- Level -----
@app.get("/users/level/{PlayerID}", tags=["Users"])
def user_level(PlayerID: int, db: Session = Depends(get_db)):
    val = crud.value(db, PlayerID, "core", "level")
    func = {'error': 0, 'etat': 'OK', 'level': val}
    if val is None:
        raise HTTPException(status_code=404, detail="User not found")
    return JSONResponse(content=jsonable_encoder(func))


@app.get("/users/level/{PlayerID}/palier", tags=["Users"])
def user_level_palier(PlayerID: int, db: Session = Depends(get_db)):
    val = crud.value(db, PlayerID, "core", "level")
    if val is None:
        raise HTTPException(status_code=404, detail="User not found")
    func = {'error': 0, 'etat': 'OK', 'palier': ge.lvlPalier(val)}
    return JSONResponse(content=jsonable_encoder(func))


@app.put("/users/level/{PlayerID}/{nb}", tags=["Users"])
def add_level(PlayerID: int, nb: int, db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    try:
        bal = crud.value(db, PlayerID, "core", "level")
        ns = bal + int(nb)
        if ns <= 0:
            ns = 0
        crud.update(db, PlayerID, "core", "level", ns)
        func = {'error': 0, 'etat': 'OK', 'newvalue': ns, 'oldvalue': bal}
    except:
        func = {'error': 1, 'etat': 'NOK'}
    return JSONResponse(content=jsonable_encoder(func))


# ----- XP -----
@app.get("/users/xp/{PlayerID}", tags=["Users"])
def user_xp(PlayerID: int, db: Session = Depends(get_db)):
    val = crud.value(db, PlayerID, "core", "xp")
    func = {'error': 0, 'etat': 'OK', 'xp': val}
    if val is None:
        raise HTTPException(status_code=404, detail="User not found")
    return JSONResponse(content=jsonable_encoder(func))


@app.put("/users/xp/{PlayerID}/{nb}", tags=["Users"])
def add_xp(PlayerID: int, nb: int, db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    try:
        bal = crud.value(db, PlayerID, "core", "xp")
        ns = bal + int(nb)
        if ns <= 0:
            ns = 0
        crud.update(db, PlayerID, "core", "xp", ns)
        func = {'error': 0, 'etat': 'OK', 'newvalue': ns, 'oldvalue': bal}
    except:
        func = {'error': 1, 'etat': 'NOK'}
    return JSONResponse(content=jsonable_encoder(func))


# ----- Messages -----
@app.get("/users/msg/{PlayerID}", tags=["Users"])
def user_msg(PlayerID: int, db: Session = Depends(get_db)):
    val = crud.value(db, PlayerID, "core", "nbmsg")
    func = {'error': 0, 'etat': 'OK', 'nbmsg': val}
    if val is None:
        raise HTTPException(status_code=404, detail="User not found")
    return JSONResponse(content=jsonable_encoder(func))


@app.put("/users/msg/{PlayerID}/{nb}", tags=["Users"])
def add_msg(PlayerID: int, nb: int, db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    try:
        bal = crud.value(db, PlayerID, "core", "nbmsg")
        ns = bal + int(nb)
        if ns <= 0:
            ns = 0
        crud.update(db, PlayerID, "core", "nbmsg", ns)
        func = {'error': 0, 'etat': 'OK', 'newvalue': ns, 'oldvalue': bal}
    except:
        func = {'error': 1, 'etat': 'NOK'}
    return JSONResponse(content=jsonable_encoder(func))


# ----- Reactions -----
@app.get("/users/reaction/{PlayerID}", tags=["Users"])
def user_reaction(PlayerID: int, db: Session = Depends(get_db)):
    val = crud.value(db, PlayerID, "core", "nbreaction")
    func = {'error': 0, 'etat': 'OK', 'nbreaction': val}
    if val is None:
        raise HTTPException(status_code=404, detail="User not found")
    return JSONResponse(content=jsonable_encoder(func))


@app.put("/users/reaction/{PlayerID}/{nb}", tags=["Users"])
def add_reaction(PlayerID: int, nb: int, db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    try:
        bal = crud.value(db, PlayerID, "core", "nbreaction")
        ns = bal + int(nb)
        if ns <= 0:
            ns = 0
        crud.update(db, PlayerID, "core", "nbreaction", ns)
        func = {'error': 0, 'etat': 'OK', 'newvalue': ns, 'oldvalue': bal}
    except:
        func = {'error': 1, 'etat': 'NOK'}
    return JSONResponse(content=jsonable_encoder(func))


# ----- Godchilds -----
@app.get("/users/godchilds/{PlayerID}", response_model=List[schemas.TableCore], tags=["Users"])
def get_godchilds(PlayerID: int, db: Session = Depends(get_db)):
    godchilds = crud.get_godchilds(db=db, PlayerID=PlayerID)
    func = {'error': 0, 'etat': 'OK', 'godchilds': godchilds}
    if godchilds is None:
        func = {'error': 0, 'etat': 'OK', 'godchilds': {}}
    return JSONResponse(content=jsonable_encoder(func))


@app.get("/users/godchilds/count/{PlayerID}", tags=["Users"])
def get_count_godchilds(PlayerID: int, db: Session = Depends(get_db)):
    godchilds = crud.countFilleul(db=db, PlayerID=PlayerID)
    func = {'error': 0, 'etat': 'OK', 'nbgodchilds': godchilds}
    return JSONResponse(content=jsonable_encoder(func))


@app.put("/users/{PlayerID}/godparent/{godparentID}", response_model=schemas.TableCore, tags=["Users"])
def add_godparent(PlayerID: int, godparentID: int, db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    GPID = crud.get_PlayerID(db, godparentID, "discord")
    if GPID is None:
        func = {'error': 2, 'etat': 'NOK'}
        return JSONResponse(content=jsonable_encoder(func))
    GPID = GPID.playerid
    myGP = crud.value(db, PlayerID, "core", "godparent")
    if (myGP == 0 or myGP == None or myGP is False) and PlayerID != GPID:
        crud.update(db, PlayerID, "core", "godparent", GPID)
        func = {'error': 0, 'etat': 'OK', 'new': GPID, 'old': myGP}
    else:
        func = {'error': 1, 'etat': 'NOK'}
    return JSONResponse(content=jsonable_encoder(func))


# ========= Com Time =========
@app.get("/comtime/spam/{PlayerID}/{Command}/{couldown}", tags=["Command Time"])
def get_command_time(PlayerID: int, Command: str, couldown: int, db: Session = Depends(get_db)):
    res = crud.spam(db, PlayerID, couldown, Command)
    func = {'error': 0, 'etat': 'OK', 'comtime': res}
    if res is None:
        func = {'error': 0, 'etat': 'OK', 'comtime': {}}
    return JSONResponse(content=jsonable_encoder(func))

@app.put("/comtime/update/{PlayerID}/{Command}", tags=["Command Time"])
def update_command_time(PlayerID: int, Command: str, db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    res = crud.updateComTime(db, PlayerID, Command)
    if res is None:
        res = {}
    return JSONResponse(content=jsonable_encoder(res))


# ========= Interface Web <> Discord =========
@app.put("/discord/{DiscordID}/roles/add/{Role}", tags=["Discord"])
async def discord_roles_add(DiscordID: int, Role: str, api_key: APIKey = Depends(get_api_key)):
    RolesList = [
        'Baron du Bastion',
        'Inquisiteur du Bastion',
        'BastioBot',
        'Groovy',
        'En direct',
        'Reine du babot 👑',
        'Bibliothécaire',
        'Maréchal président à vie',
        'Bouilleur de cru',
        'Twitch Subscriber: Tier 1',
        'Twitch Subscriber: Tier 2',
        'Twitch Subscriber: Tier 3',
        'Bastionaute',
        'Weekend Astro 27-29/08'
    ]
    if Role in RolesList:
        func = {'error': 2, 'etat': 'NOK', 'msg': 'Role {0} interdit'.format(Role)}
    else:
        guild = client.get_guild(ge.idBASTION)
        member = get(client.get_all_members(), id=DiscordID)
        res = await ge.addrole(member, Role)
        if res == "Role introuvable":
            func = {'error': 1, 'etat': 'NOK', 'msg': 'Role {0} introuvable'.format(Role)}
        else:
            func = {'error': 0, 'etat': 'OK', 'msg': 'Role {0} ajouté'.format(Role)}
    return func


@app.put("/discord/{DiscordID}/roles/remove/{Role}", tags=["Discord"])
async def discord_roles_remove(DiscordID: int, Role: str, api_key: APIKey = Depends(get_api_key)):
    RolesList = [
        'Baron du Bastion',
        'Inquisiteur du Bastion',
        'BastioBot',
        'Groovy',
        'En direct',
        'Reine du babot 👑',
        'Bibliothécaire',
        'Maréchal président à vie',
        'Bouilleur de cru',
        'Twitch Subscriber: Tier 1',
        'Twitch Subscriber: Tier 2',
        'Twitch Subscriber: Tier 3',
        'Bastionaute',
        'Weekend Astro 27-29/08'
    ]
    if Role in RolesList:
        func = {'error': 2, 'etat': 'NOK', 'msg': 'Role {0} interdit'.format(Role)}
    else:
        guild = client.get_guild(ge.idBASTION)
        member = get(client.get_all_members(), id=DiscordID)
        res = await ge.removerole(member, Role)
        if res == "Role introuvable":
            func = {'error': 1, 'etat': 'NOK', 'msg': 'Role {0} introuvable'.format(Role)}
        else:
            func = {'error': 0, 'etat': 'OK', 'msg': 'Role {0} retiré'.format(Role)}
    return func


# ========= Stats =========
@app.put("/stats/create/hour/", tags=["Statistiques"])
def stats_create_hour(date: str, hourA: int, hourB: int, nbmsg: int, nbreaction: int, db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    # try:
    res = crud.create_stats(db, date, hourA, hourB, nbmsg, nbreaction)
    func = {'error': 0, 'etat': 'OK', 'stats': res}
    # except:
    #     func = {'error': 1, 'etat': 'NOK'}
    return JSONResponse(content=jsonable_encoder(func))


@app.get("/stats/msg/hour/", tags=["Statistiques"])
def stats_message_hour(skip: int = (dt.datetime.now().hour) - 1, limit: int = dt.datetime.now().hour, db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    res = stats.hourMsg(db=db, ha=skip, hb=limit)
    func = {'error': 0, 'etat': 'OK', 'msghour': res}
    return func


@app.get("/stats/msg/hour/graph/", tags=["Statistiques"])
async def stats_message_graph_hour(guildid: int, channelid: int, db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    try:
        await stats.graphheure(db, client, guildid, channelid)
        func = {'error': 0, 'etat': 'OK'}
    except:
        func = {'error': 1, 'etat': 'NOK'}
    return func


@app.get("/stats/msg/day/graph/", tags=["Statistiques"])
async def stats_message_graph_jour(guildid: int, channelid: int, db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    try:
	    await stats.graphjour(db, client, guildid, channelid)
	    func = {'error': 0, 'etat': 'OK'}
    except:
        func = {'error': 1, 'etat': 'NOK'}
    return func


@app.get("/stats/msg/graph/", tags=["Statistiques"])
async def stats_message_graph(guildid: int, channelid: int, range: int = 6, db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    try:
	    await stats.graphmsg(db, client, guildid, channelid, range)
	    func = {'error': 0, 'etat': 'OK'}
    except:
        func = {'error': 1, 'etat': 'NOK'}
    return func


@app.get("/stats/xp/graph/", tags=["Statistiques"])
async def stats_xp_graph(guildid: int, channelid: int, range: int = 6, db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    try:
	    await stats.graphxp(db, client, guildid, channelid, range)
	    func = {'error': 0, 'etat': 'OK'}
    except:
        func = {'error': 1, 'etat': 'NOK'}
    return func


# ========= Test =========
# @app.post("/test/{PlayerID}", tags=["Test"])
# def test(PlayerID: int, db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
#     res = {}
#     if res is None:
#         res = {}
#     return JSONResponse(content=jsonable_encoder(res))

# @app.put("/old/{PlayerID}/{arrival}/{niv}/{xp}/{nbmsg}/{nbreaction}/{parrain}", tags=["Old"])
# def old_info(PlayerID: int, niv: int, xp: int, arrival: str, nbmsg: int, nbreaction: int, parrain: int, db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
#     try:
#         crud.update(db, PlayerID, "core_old", "level", niv)
#         crud.update(db, PlayerID, "core_old", "xp", xp)
#         crud.update(db, PlayerID, "core", "arrival", arrival)
#         crud.update(db, PlayerID, "core", "nbmsg", nbmsg)
#         crud.update(db, PlayerID, "core", "nbreaction", nbreaction)
#         ns = int(nbmsg) + int(nbreaction)
#         crud.update(db, PlayerID, "core", "xp", ns)
#         GPID = crud.get_PlayerID(db, parrain, "discord")
#         if GPID is None:
#             GPID = 0
#         else:
#             GPID = int(GPID.playerid)
#         crud.update(db, PlayerID, "core", "godparent", GPID)
#         func = {'error': 0, 'etat': 'OK'}
#     except:
#         func = {'error': 1, 'etat': 'NOK'}
#     return JSONResponse(content=jsonable_encoder(func))
