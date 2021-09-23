from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from sqlalchemy import text
import time as t, datetime as dt
from operator import itemgetter
from . import models, schemas, crud, gestion as ge
import os
import requests
import json
import discord
from fastapi.encoders import jsonable_encoder
from discord.ext import commands, tasks
from discord.ext.commands import bot
from operator import itemgetter
import matplotlib.pyplot as plt

file = "cache/time.json"
co = "cache/co.json"


def fileExist():
	try:
		with open(file):
			pass
	except IOError:
		return False
	return True


def countCo():
	t = json.load(open(co, "r"))
	t["co local"] += 1
	t["co total"] += 1
	with open(co, 'w') as f:
		f.write(json.dumps(t, indent=4))


def countDeco():
	t = json.load(open(co, "r"))
	t["deco local"] += 1
	t["deco total"] += 1
	with open(co, 'w') as f:
		f.write(json.dumps(t, indent=4))


def hourCount(db: Session):
	d = dt.datetime.now().hour
	nbmsg = 0
	if fileExist() is False:
		t = {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0, "9": 0, "10": 0, "11": 0, "12": 0, "13": 0, "14": 0, "15": 0, "16": 0, "17": 0, "18": 0, "19": 0, "20": 0, "21": 0, "22": 0, "23": 0}
		nbmsg = crud.countTotalMsg(db=db)
		if nbmsg == {}:
			nbmsg = 0
		else:
			nbmsg = int(nbmsg['total_message'])
		t[str(d)] = nbmsg
		with open(file, 'w') as f:
			f.write(json.dumps(t, indent=4))
		return d
	else:
		with open(file, "r") as f:
			t = json.load(f)
			t[str(d)] = nbmsg
		with open(file, 'w') as f:
			f.write(json.dumps(t, indent=4))
	print("time.json modifié")


# ===============================================================
def hourMsg(db: Session, ha, hb):
	"""
	**[heure de début] [heure de fin]** | Donne le nombre de message posté dans l'heure ou entre deux heures.
	"""
	if (hb - ha) == 1:
		value = crud.value(db=db, PlayerID=0, nameTable='stats', fieldName='nbmsg', filtre = ['date', 'hour_start', 'hour_stop'], filtreValue = [dt.datetime.now().date(), ha, hb])
		if value is False:
			msg = "Les statistiques de cette plage horaire ne sont pas disponible"
		else:
			msg = "Aujourd'hui, entre {0}h et {1}h il y a eu {2} messages.".format(ha, hb, value)
	elif (ha >= 0 and hb >= 0 and ha < 24 and hb < 24):
		try:
			script = "SELECT SUM(nbmsg) FROM stats"
			script += " WHERE date = '{date}' AND (".format(date=dt.datetime.now().date())
			for hour in range(ha, hb):
				if hour != ha:
					script += " OR "
				script += "hour_start = '{val}'".format(val=hour)
			script += ") ORDER BY {0}".format('hour_start')
			# print(script)
			script = text(script)
			value = db.execute(script).fetchall()
		except:
			# Aucune données n'a été trouvé
			value = False

		if value is False:
			msg = "Les statistiques de cette plage horaire ne sont pas disponible"
		else:
			msg = "Aujourd'hui, entre {0}h et {1}h il y a eu {2} messages.".format(ha, hb, value[0][0])
	else:
		msg = 'Vous avez entré une heure impossible.'
	return msg


async def graphheure(db: Session, client, guildid, channelid, statue = "local", jour = "yesterday"):
	"""|local/total aaaa-mm-jj| Affiche le graph des messages envoyés par heure."""
	guild = client.get_guild(guildid)
	channel = guild.get_channel(int(channelid))
	if jour == "yesterday":
		jour = str(dt.date.today()-dt.timedelta(days = 1))
	value = crud.valueAll(db=db, PlayerID=0, nameTable='stats', fieldName=['hour_start', 'nbmsg'], filtre = 'date', filtreValue = jour, order='hour_start')
	# print(value)
	if value is False:
		msg = "Les statistiques de cette journée ne sont pas disponible"
		await channel.send(msg)
	else:
		if os.path.isfile("cache/graphheure.png"):
			os.remove('cache/graphheure.png')
			# print('removed old graphe file')
		x = []
		y = []
		for i in range(24):
			x.append(i)
			y_check = False
			for one in value:
				if one[0] == i:
					y_check = True
					y.append(one[1])
			if y_check is False:
				y.append(0)
		# print(x)
		# print(y)
		if statue == "local":
			plt.hist(x, bins = 24, weights = y)
		else :
			plt.plot(x, y, label="graph test")
			plt.fill_between(x, y[0]-100, y, color='blue', alpha=0.5)
		plt.xlabel('heures')
		plt.ylabel('messages')
		plt.title("graphique du {}".format(jour))
		plt.savefig("cache/graphheure.png")
		await channel.send(file=discord.File("cache/graphheure.png"))
		if os.path.isfile("cache/graphheure.png"):
			os.remove('cache/graphheure.png')
		plt.clf()


async def graphjour(db: Session, client, guildid, channelid, statue = "local", mois = "now"):
	"""|local/total aaaa-mm| Affiche le graph des messages envoyés par jour."""
	guild = client.get_guild(guildid)
	channel = guild.get_channel(int(channelid))
	if mois == "now":
		mois = str(dt.date.today())[:7]
	aaaa , mm = mois.split("-")
	nom_mois = dt.datetime(int(aaaa), int(mm), 1).strftime("%B")
	jour_mois = 0
	value = {}
	for i in range(1, 32):
		try:
			a=dt.datetime(int(aaaa), int(mm), i)
			value_temp = crud.valueAll(db=db, PlayerID=0, nameTable='stats', fieldName='SUM(nbmsg)', filtre = 'date', filtreValue = '{0}-{1}-{2}'.format(aaaa, mm, i), order='hour_start')
			if value_temp is not False:
				value_temp = value_temp[0][0]
			value['{0}-{1}-{2}'.format(aaaa, mm, i)] = value_temp
		except : pass
		else : jour_mois = i
	# print(value)
	if value is False:
		msg = "Les statistiques de cette journée ne sont pas disponible"
		await channel.send(msg)
	else:
		if os.path.isfile("cache/graphjour.png"):
			os.remove('cache/graphjour.png')
			# print('removed old graphe file')
		x = []
		y = []
		for i in range(1, jour_mois+1):
			x.append(i)
			if value['{0}-{1}-{2}'.format(aaaa, mm, i)] is None:
				y.append(0)
			else:
				y.append(value['{0}-{1}-{2}'.format(aaaa, mm, i)])
		# print(x)
		# print(y)
		if statue == "local":
			plt.hist(x, bins = 24, weights = y)
		else :
			plt.plot(x, y, label="graph test")
			plt.fill_between(x, y[0]-100, y, color='blue', alpha=0.5)
		plt.xlabel('jour')
		plt.ylabel('messages')
		plt.title("graphique du 1 au {} {}".format(jour_mois, nom_mois))
		plt.savefig("cache/graphjour.png")
		await channel.send(file=discord.File("cache/graphjour.png"))
		if os.path.isfile("cache/graphjour.png"):
			os.remove('cache/graphjour.png')
		plt.clf()


async def graphmsg(db: Session, client, guildid, channelid, r = 6):
	"""
	Graphique représentant le classement des membres en fonction du nombre de messages écrit.
	"""
	guild = client.get_guild(guildid)
	channel = guild.get_channel(int(channelid))
	members = guild.members
	if os.path.isfile("cache/msggrapf.png"):
		os.remove('cache/msggrapf.png')
		# print('removed old graphe file')
	total = crud.countTotalMsg(db=db)
	if total == {}:
		total = 0
	else:
		total = int(total['total_message'])
	a = []
	taille = crud.taille(db=db)
	if taille == {}:
		taille = 0
	else:
		taille = int(taille['taille'])
	users = jsonable_encoder(crud.get_users(db=db, skip=0, limit=taille))
	for user in users:
		try:
			IDi = user['discord_id']
			nbMsg = user['nbmsg']
			label = "Utilisateur inconnu\n{}".format(IDi)
			for member in members:
				if str(member.id) == str(IDi):
					label = member.name
			a.append([nbMsg, IDi, label])
		except:
			pass
	a.sort(reverse = True)
	richest = a[:r]
	sous_total = 0
	for i in range(r):
		sous_total += richest[i][0]
	labels = []
	sizes = []
	for i in range(r):
		labels.append(richest[i][2])
		sizes.append(richest[i][0])
	labels.append("autre")
	sizes.append(total - sous_total)
	explode = ()
	i = 0
	while i <= r:
		if i < r:
			explode = explode + (0,)
		else:
			explode = explode + (0.2,)
		i += 1
	plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, explode=explode)
	plt.axis('equal')
	plt.savefig('cache/msggrapf.png')
	await channel.send(file=discord.File("cache/msggrapf.png"))
	plt.clf()
	if os.path.isfile("cache/msggrapf.png"):
		os.remove('cache/msggrapf.png')


async def graphxp(db: Session, client, guildid, channelid, r = 6):
	"""
	Graphique représentant le classement des membres en fonction de leur XP.
	"""
	guild = client.get_guild(guildid)
	channel = guild.get_channel(int(channelid))
	members = guild.members
	if os.path.isfile("cache/xpgrapf.png"):
		os.remove('cache/xpgrapf.png')
		# print('removed old graphe file')
	total = crud.countTotalXP(db=db)
	if total == {}:
		total = 0
	else:
		total = int(total['total_xp'])
	a = []
	taille = crud.taille(db=db)
	if taille == {}:
		taille = 0
	else:
		taille = int(taille['taille'])
	users = jsonable_encoder(crud.get_users(db=db, skip=0, limit=taille))
	for user in users:
		try:
			IDi = user['discord_id']
			nbMsg = user['nbmsg']
			label = "Utilisateur inconnu\n{}".format(IDi)
			for member in members:
				if str(member.id) == str(IDi):
					label = member.name
			a.append([nbMsg, IDi, label])
		except:
			pass
	a.sort(reverse = True)
	richest = a[:r]
	sous_total = 0
	for i in range(r):
		sous_total += richest[i][0]
	labels = []
	sizes = []
	for i in range(r):
		labels.append(richest[i][2])
		sizes.append(richest[i][0])
	labels.append("autre")
	sizes.append(total - sous_total)
	explode = ()
	i = 0
	while i <= r:
		if i < r:
			explode = explode + (0,)
		else:
			explode = explode + (0.2,)
		i += 1
	plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, explode=explode)
	plt.axis('equal')
	plt.savefig('cache/xpgrapf.png')
	await channel.send(file=discord.File("cache/xpgrapf.png"))
	plt.clf()
	if os.path.isfile("cache/xpgrapf.png"):
		os.remove('cache/xpgrapf.png')
