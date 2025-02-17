#!/usr/bin/python3
# coding=utf-8
###########################################################################
# Name:   StartGame
# Author: Alan Jackson
# Date:   11th March 2009
#
# Game launcher for the Linux/OS X based launcher
# for the game Lord of the Rings Online
#
# Based on a script by SNy <SNy@bmx-chemnitz.de>
# Python port of PyLotRO by AJackson <ajackson@bcs.org.uk>
#
# (C) 2009 AJackson <ajackson@bcs.org.uk>
#
# This file is part of PyLotRO
#
# PyLotRO is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# PyLotRO is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PyLotRO.  If not, see <http://www.gnu.org/licenses/>.
###########################################################################
# from PyQt4 import QtCore, QtGui, uic
from Settings import Settings
from PyLotROUtils import DetermineOS, QByteArray2str
from PyLotROUtils import DetermineGame, LanguageConfig, Language
from PyLotROUtils import BaseConfig, GLSDataCentre, WorldQueueConfig
from PyLotROUtils import AuthenticateUser, JoinWorldQueue, GetText, WebConnection
import subprocess
import sys, os.path

class StartGame:
	def __init__(self, parent, worldQueueConfig, accSubscription, loginServer, ticket,
		chatServer, language, runDir, wineProgram, wineDebug, winePrefix, 
		hiResEnabled, wineApp, osType, homeDir, icoFileIn, rootDir):

		worldQueueConfig.gameClientFilename,
		worldQueueConfig.gameClientArgTemplate,
		self.homeDir = homeDir
		self.osType = osType

		self.aborted = False
		self.finished = False
		self.command = ""
		self.arguments = []

		gameParams = worldQueueConfig.gameClientArgTemplate.replace("{LOGIN}", loginServer)
		gameParams = gameParams.replace("{AUTHSERVERURL}", worldQueueConfig.gameClientAuthServerURL)
		gameParams = gameParams.replace("{GLS}", ticket)
		gameParams = gameParams.replace("{CHAT}", chatServer)
		gameParams = gameParams.replace("{LANG}", language)
		gameParams = gameParams.replace("{GLSTICKETLIFETIME}", worldQueueConfig.gameClientGLSTicketLifetime)
		gameParams = gameParams.replace("{SUBSCRIPTION}", accSubscription)

		if not hiResEnabled:
			gameParams = gameParams + " --HighResOutOfDate"

		if wineDebug != "":
			os.environ["WINEDEBUG"] = wineDebug

		if winePrefix != "" and wineApp == "Wine":
			os.environ["WINEPREFIX"] = winePrefix

		self.command = wineProgram
		self.arguments.append(worldQueueConfig.gameClientFilename)
		self.gameParams = gameParams

		for arg in gameParams.split(" "):
			self.arguments.append(arg)

	def run(self):
		self.finished = False
		print(f"\ncommand: {self.command}\narguments: {self.arguments}\n\n")
		steamRoot = '/home/steam'
		protonVersion = '8.0'
		protonRunner = steamRoot+'/steamapps/common/Proton '+protonVersion+'/proton'
		launcherExec = 'DNDLauncher.exe'
		gameCMD = 'x64/dndclient64.exe '+" ".join(self.arguments[1:])
		os.environ['STEAM_COMPAT_DATA_PATH'] = steamRoot+'/prefixes/DDO_Alt'
		os.environ['STEAM_COMPAT_CLIENT_INSTALL_PATH'] = steamRoot+'/prefixes/DDO_Alt'
		os.environ['WINEPREFIX'] = steamRoot+'/prefixes/DDO_Alt/pfx'
		os.environ['WINEARCH'] = 'win64'
		dndPath = '/home/steam/prefixes/DDO_Main/pfx/drive_c/Program Files (x86)/StandingStoneGames/Dungeons & Dragons Online'
		exec = f"cd \"{dndPath}\"; WINEPREFIX={steamRoot+'/prefixes/DDO_Alt/pfx'} WINEARCH=win64 wine {gameCMD}"
		exec = f"\"{protonRunner}\" run {gameCMD}"
		print(f"\n\n\nEXECUTABLE: {exec}\n\n\n")
		os.chdir(dndPath)
		os.system(exec)



def EnterWorldQueue(queueURL, worldQueueConfig, account, accNumber, valHomeDir, osType):
	worldQueue = JoinWorldQueue(worldQueueConfig.worldQueueParam,
		accNumber, account.ticket, queueURL, worldQueueConfig.worldQueueURL, valHomeDir, osType)

	print(f"Joined Queue? {worldQueue.joinSuccess}")
	if not worldQueue.joinSuccess: exit(-1)
	while worldQueue.number > worldQueue.serving and worldQueue.joinSuccess:
		worldQueue = JoinWorldQueue(worldQueueConfig.worldQueueParam,
			accNumber, account.ticket, queueURL, worldQueueConfig.worldQueueURL,
			valHomeDir, osType)


if __name__ == '__main__':
	valHomeDir = os.environ.get('HOME')+"/"
	osType = DetermineOS()
	gameType = DetermineGame()
	settings = Settings(valHomeDir, osType)
	settings.usingDND = True # for DDO as opposed to Lotro
	settings.hiResEnabled = True
	settings.app = "Wine"
	settings.realm = ""
	settings.language = ""
	settings.account = ""
	settings.wineProg = "wine"
	settings.wineDebug = ""
	settings.patchClient = "patchclient.dll"
	settings.focusAccount = True
	settings.winePrefix = '/home/steam/prefixes/DDO_Main/pfx'
	settings.gameDir = '/home/steam/prefixes/DDO_Main/pfx/drive_c/Program Files (x86)/StandingStoneGames/Dungeons & Dragons Online'
	settings.hideWinMain = False

	gameType.GetSettings(settings.usingDND, settings.usingTest)
	gameType.configFile = "/ddo.launcherconfig"

	configFile = settings.gameDir + gameType.configFile
	baseConfig = BaseConfig(configFile)
	print(f"Config loaded? {baseConfig.isConfigOK}")
	if not baseConfig.isConfigOK: sys.exit(-1)
	
	dataCentre = GLSDataCentre(baseConfig.GLSDataCentreService, baseConfig.gameName, valHomeDir, osType)
	if not dataCentre.loadSuccess: sys.exit(-1)
	
	worldQueueConfig = WorldQueueConfig(dataCentre.launchConfigServer, settings.usingDND, valHomeDir, osType)
	print(f"World Queue configuration read? {worldQueueConfig.loadSuccess}")
	if not worldQueueConfig.loadSuccess: sys.exit(-1)

	print("ENTER PASSWORD IN DDO_USERNAME and DDO_PASSWORD!!")
	username = os.environ["DDO_USERNAME"]
	password = os.environ["DDO_PASSWORD"]
	
	account = AuthenticateUser(dataCentre.authServer, username, password, 
							baseConfig.gameName, valHomeDir, osType)
	print(f"Account Authenticated? {account.authSuccess}")
	print(f"{account.messError}")
	if not account.authSuccess: sys.exit(-1)

	print(f"gameList = {account.gameList}")

	accSubscription = account.gameList[0].name
	tempRealm = dataCentre.realmList[0] #self.uiMain.cboRealm.currentIndex()]
	tempRealm.CheckRealm(settings.usingDND, valHomeDir, osType)

	print(f"Realm available? {tempRealm.realmAvailable}")
	if not tempRealm.realmAvailable: sys.exit(-1)
	urlChatServer = tempRealm.urlChatServer
	urlLoginServer = tempRealm.loginServer

	if tempRealm.queueURL != "":
		EnterWorldQueue(tempRealm.queueURL, worldQueueConfig, account, accSubscription, valHomeDir, osType)
	
	print(f'\n\nTEMPLATE: {worldQueueConfig.gameClientArgTemplate}\n\n')

	print(f"Qeueing done, joining server...")
	game = StartGame(None, #self.winMain,
					 worldQueueConfig,
					 accSubscription,
					 urlLoginServer, # dataCentre.authServer?
					 account.ticket,
					 urlChatServer,
					 "English", #self.langConfig.langList[self.uiMain.cboLanguage.currentIndex()].code,
					 settings.gameDir,
					 settings.wineProg,
					 settings.wineDebug,
					 settings.winePrefix,
					 settings.hiResEnabled,
					 settings.app,
					 osType,
					 valHomeDir,
					 None, #self.gameType.icoFile,
					 '/home/soul/share/pylotro/headless/') #self.rootDir)
	game.run()