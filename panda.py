from math import pi, sin, cos
from direct.actor.Actor import Actor
from panda3d.core import *
from random import randrange

from pybrain.structure import FeedForwardNetwork, TanhLayer, FullConnection

import numpy

class Panda(object):
	"""
	This class is in charge of manipulating the pandas, the neural network, the collisions, etc
	
	Attributes:
		pandaIds (dict): Maps an int to a Panda object
	    pandaList (list): List of all the pandas
	    pandaActorIdle (Actor): Panda3d Actor class
	    pandaActorWalking (Actor): Panda3d Actor class
		livingPandas (int): counter of living pandas

		health (float): Amount of health
	    viewDistance (float): Maximum view distance
	    baseSpeed (float): Speed multiplier
	    baseTurnSpeed (float): Turn speed multiplier (in degrees)
	    isAlive (bool): True if alive
	    isDying (bool): True if health == 0
	    carrotsEaten (int): Number of carrots eaten by the panda (score)
	    brainWeights (list): List of weights for the net
	    network (FeedForwardNetwork): PyBrain Neural Network object
		inputNumber (int): Number of view frustums
	    inputDistanceList (list): float between 1.0 and 0.0; 1.0 -> farther, 0.0 -> closer
	    inputTypeList (list): -1 spike, 0 nothing, 1 carrot
	    lensNodeList (list): list of the nodes of the frustums
	    handleLifeBar (NodePath): Node for the life bar
	    pandaHandle (NodePath): Node for the panda
	    pandaActorIdleHandle (NodePath): Node for the idle panda animation
	    pandaActorWalkingHandle (NodePath): Node for the walking panda animation
	    
	"""
	pandaList = []
	pandaIds = {}
	pandaActorIdle = None
	pandaActorWalking = None
	livingPandas = 0

	def __init__(self, game, x, y, genome):
		"""
		Initialize
		
		Args:
		    game (game (Game): A reference to the Game object
		    x (int): x coordinate
		    y (int): y coordinate
		    genome (G1DList): PyEvolve's individual container
		"""
		if not Panda.pandaActorIdle:
			Panda.pandaActorIdle = Actor("models/panda-model", {"walk": "models/panda-walk4"})
			Panda.pandaActorIdle.setPos(0,0,0)
			Panda.pandaActorIdle.setScale(0.005, 0.005, 0.005)

		if not Panda.pandaActorWalking:
			Panda.pandaActorWalking = Actor("models/panda-model", {"walk": "models/panda-walk4"})
			Panda.pandaActorWalking.setPos(0,0,0)
			Panda.pandaActorWalking.setScale(0.005, 0.005, 0.005)
			Panda.pandaActorWalking.loop("walk")

		self.health = 100.0
		self.viewDistance = 50.0
		self.baseSpeed = 1.0
		self.baseTurnSpeed = 10.0
		self.isAlive = True
		self.isDying = False
		self.carrotsEaten = 0

		self.lensNodeList = []
		self.inputNumber = 7 #number of view frustums
		self.inputDistanceList = [0]*self.inputNumber # float between 1.0 and 0.0; 1.0 -> farther, 0.0 -> closer
		self.inputTypeList = [0]*self.inputNumber #-1 spike, 0 nothing, 1 carrot

		h = randrange(0, 360)
		self.pandaHandle = game.render.attachNewNode("pandaHandle")
		self.pandaHandle.setPos(x, y, 0)
		self.pandaHandle.setH(h)
		#self.pandaHandle.showTightBounds()

		self.pandaActorWalkingHandle = self.pandaHandle.attachNewNode("pandaActorWalkingHandle")
		self.pandaActorWalkingHandle.setPos(0,0,0)

		self.pandaActorIdleHandle = self.pandaHandle.attachNewNode("pandaActorIdleHandle")
		self.pandaActorIdleHandle.setPos(0,0,0)
		Panda.pandaActorWalking.instanceTo(self.pandaActorWalkingHandle)

		Panda.pandaList.append(self)
		Panda.livingPandas += 1
		
		Panda.pandaIds[genome.getParam("pandaId")] = self
		self.brainWeights = genome.genomeList

		self.__setUpLifeBar()
		self.__setUpLens()
		self.__setUpBrain(genome)

	def __delete(self, task = None):
		"""
		Free memory allocated by this panda
		
		Args:
		    task (task): Panda3D requires this param
		"""
		self.isAlive = False

		for node in self.lensNodeList:
			node.removeNode()
		del self.lensNodeList[:]

		self.bgHandle.removeNode()
		self.fgHandle.removeNode()
		self.handleLifeBar.removeNode()

		self.pandaActorIdleHandle.removeNode()
		self.pandaActorWalkingHandle.removeNode()
		self.pandaHandle.removeNode()
		Panda.livingPandas -= 1

	def __die(self, game):
		"""
		Prepare to die
		
		Args:
		    game (Game): A reference to the Game object
		"""
		
		if not self.isDying:
			self.health = 0.0 #maybe it is < 0
			self.isDying = True
			Panda.pandaActorIdle.instanceTo(self.pandaActorIdleHandle)
			self.pandaActorWalkingHandle.hide()
			game.taskMgr.doMethodLater(3, self.__delete, 'delete panda')

	def __setUpLens(self):
		"""
		Set up the view frustums
		"""
		hfov = 180.0 / self.inputNumber
		vfov = 10.0
		for i in range(1, self.inputNumber*2, 2):
			delta = 180.0 - (90 + vfov/2)
			delta *= (pi / 180.0)
			hfovRad = hfov*(pi / 180.0)
	
			pointTo = Vec3(cos(hfovRad*i/2), -sin(hfovRad*i/2),  cos(delta))
	
			lens = PerspectiveLens()
			lens.setFov(hfov, vfov)
			lens.setNear(0.01)
			lens.setFar(self.viewDistance)
			lens.setViewVector(pointTo, pointTo.up())
	
			lNode = LensNode("lensNode", lens)
			#lNode.showFrustum()
			handleLens = self.pandaHandle.attachNewNode(lNode)
			handleLens.setPos(0, 0, 0)
			
			self.lensNodeList.append(handleLens)

	def __setUpLifeBar(self):
		"""
		Set up the life bar
		"""
		self.handleLifeBar = self.pandaHandle.attachNewNode("lifeBarNode")
		self.handleLifeBar.setBillboardPointEye()
		self.handleLifeBar.setPos(0, 0, 3)

		self.bgCard = CardMaker("bg")
		self.bgCard.setColor(1, 0, 0, 1)
		self.bgCard.setFrame(-1, 1, -0.2, 0.2)
		self.bgHandle = self.handleLifeBar.attachNewNode(self.bgCard.generate())
		self.bgHandle.setPos(0,0,0)

		self.fgCard = CardMaker("fg")
		self.fgCard.setColor(0, 1, 0, 1)
		self.fgCard.setFrame(-1, 1, -0.2, 0.2)
		self.fgHandle = self.handleLifeBar.attachNewNode(self.fgCard.generate())
		self.fgHandle.setPos(0,0,0)

		self.__updateHealthBar()

	def update(self, game, carrots, spikes):
		"""

		
		Args:
		    game (Game): A reference to the Game object
		    carrots (list): list of carrots
		    spikes (list): list of spikes
		
		Returns:
		    None: if is dying
		"""
		if  self.isDying:
			return

		self.__updateInputs(carrots, spikes)
		brainInput = self.inputDistanceList + self.inputTypeList
		brainOutput = self.network.activate(brainInput).tolist()

		self.pandaHandle.setH(self.pandaHandle, (brainOutput[0])*self.baseTurnSpeed)
		self.pandaHandle.setPos(self.pandaHandle, 0, -((brainOutput[1]+1.0)*self.baseSpeed), 0)

		self.__handleCollisions(game, carrots, spikes)
		self.__decrementHealth()
		self.__updateHealthBar()

		if self.health <= 0.0:
			self.__die(game)

	def __decrementHealth(self):
		"""
		Decrement the health of the panda each frame
		"""
		self.health -= 0.2

	def __updateInputs(self, carrots, spikes):
		"""
		Update the inputs of the neural network
		
		Args:
		    carrots (list): list of carrots
		    spikes (list): list of spikes
		"""
		self.inputDistanceList = [self.viewDistance]*self.inputNumber # float between 1.0 and 0.0; 1.0 -> farther, 0.0 -> closer
		self.inputTypeList = [0]*self.inputNumber #-1 spike, 0 nothing, 1 carrot

		for i in range(self.inputNumber):
			carrotDistances = []
			spikeDistances = []

			for carrot in carrots:
				if not carrot.isActive:
					continue

				point = carrot.carrotHandle.getPos(self.lensNodeList[i])

				if self.lensNodeList[i].node().isInView(Point3(point.getX(), point.getY(), 0.01)):
					dist = (point.getXy() - self.lensNodeList[i].getPos().getXy()).length()
					carrotDistances.append(dist)

			for spike in spikes:
				point = spike.spikeHandle.getPos(self.lensNodeList[i])

				if self.lensNodeList[i].node().isInView(Point3(point.getX(), point.getY(), 0.01)):
					dist = (point.getXy() - self.lensNodeList[i].getPos().getXy()).length()
					spikeDistances.append(dist)

			self.inputTypeList[i] = 0
			minDist = None

			if carrotDistances:
				minDist = min(carrotDistances)
				self.inputTypeList[i] = 1

			if spikeDistances:
				minS = min(spikeDistances)

				if minDist != None: #minDist can be 0, which is evaluted false
					if minS < minDist:
						minDist = minS
						self.inputTypeList[i] = -1
				else:
					minDist = minS
					self.inputTypeList[i] = -1

			if minDist != None:
				self.inputDistanceList[i] = minDist
			
			if self.inputDistanceList[i] > self.viewDistance:
				self.inputDistanceList[i] = self.viewDistance

		self.inputDistanceList = [float(i)/self.viewDistance for i in self.inputDistanceList] #normalize the distances
		#print([round(i, 2) for i in self.inputDistanceList])

	def __updateHealthBar(self):
		"""
		Update health bar
		"""
		self.bgHandle.setScale(1.0 - self.health/100.0, 1, 1)
		self.bgHandle.setPos((self.health/100.0),0,0)

		self.fgHandle.setScale(self.health/100.0, 1, 1)
		self.fgHandle.setPos(-(1.0 - (self.health/100.0)),0,0)

	def __handleCollisions(self, game, carrots, spikes):
		"""
		If there is a collision with a carrot, increment health
		If there is a collision with a spike, kill the panda (NOOOO!!!)
		
		Args:
		    game (Game): A reference to the Game object
		    carrots (list): list of carrots
		    spikes (list): list of spikes
		"""
		for carrot in carrots:
			if not carrot.isActive:
				continue

			point = carrot.carrotHandle.getPos()
			dist = (point.getXy() - self.pandaHandle.getPos().getXy()).lengthSquared()
			if dist < 10:
				self.__eatCarrot()
				carrot.goToHeaven(game, Panda.pandaList, spikes)
				break
		for spike in spikes:
			point = spike.spikeHandle.getPos()
			dist = (point.getXy() - self.pandaHandle.getPos().getXy()).lengthSquared()
			if dist < 20:
				self.__die(game)
				break

	def __eatCarrot(self):
		"""
		Increment score and life points
		"""
		self.carrotsEaten += 1
		self.health += 40.0
		if self.health > 100.0:
			self.health = 100.0

	def __setUpBrain(self, genome):
		"""
		Set up PyBrain's neural network
		
		Args:
		    genome (G1DList): PyEvolve's individual container
		"""
		self.network = FeedForwardNetwork()

		inLayer = TanhLayer(14)
		hiddenLayer = TanhLayer(12)
		hiddenLayer2 = TanhLayer(6)
		outLayer = TanhLayer(2)
		
		self.network.addInputModule(inLayer)
		self.network.addModule(hiddenLayer)
		self.network.addModule(hiddenLayer2)
		self.network.addOutputModule(outLayer)
		
		in_to_hidden = FullConnection(inLayer, hiddenLayer)
		hidden_to_hidden2 = FullConnection(hiddenLayer, hiddenLayer2)
		hidden2_to_out = FullConnection(hiddenLayer2, outLayer)
		
		self.network.addConnection(in_to_hidden)
		self.network.addConnection(hidden_to_hidden2)
		self.network.addConnection(hidden2_to_out)
		
		self.network.sortModules()

		new_params = numpy.array(genome.genomeList)
		self.network._setParameters(new_params)

	@staticmethod
	def getBestPanda():
		"""
		Returns the panda with the highest score
		
		Returns:
		    Panda: panda with the highest score
		"""
		best = Panda.pandaList[0]
		for panda in Panda.pandaList:
			if best.carrotsEaten < panda.carrotsEaten:
				best = panda
		return best

	@staticmethod
	def getAvgScore():
		"""
		Returns the average population score
		
		Returns:
		    float: Average score
		"""
		avg = 0.0
		for panda in Panda.pandaList:
			avg += panda.carrotsEaten
		avg = avg / len(Panda.pandaList)
		return round(avg,3)

	@staticmethod
	def clearPandas(game):
		"""
		Remove all the pandas
		
		Args:
		    game (Game): A reference to the Game object
		"""
		game.taskMgr.remove('delete panda')

		for panda in Panda.pandaList[:]:
			if panda.isAlive:
				panda.__delete()
		del Panda.pandaList[:]
		Panda.pandaIds.clear()

	@staticmethod
	def getScoreById(pandaId):
		"""
		Given the Id of a panda return its score
		
		Args:
		    pandaId (int): Id of panda
		
		Returns:
		    int: panda score
		"""
		score = Panda.pandaIds[pandaId].carrotsEaten 
		if not Panda.pandaIds[pandaId].isDying:
			score += 3

		return score

	def drawDebugLines(self, game, carrots, spikes):
		"""
		Debug info
		
		Args:
		    game (Game): A reference to the Game object
		    carrots (list): list of carrots
		    spikes (list): list of spikes
		"""
		for carrot in carrots:
			if not carrot.isActive:
				continue

			point = carrot.carrotHandle.getPos()

			linesegs = LineSegs("lines")
			linesegs.setColor(1,1,1,1) 
			 
			linesegs.drawTo(point) 
			linesegs.drawTo(self.pandaHandle.getPos()) 
			 
			node = linesegs.create(False) 			 
			game.render.attachNewNode(node)
			
		for spike in spikes:
			point = spike.spikeHandle.getPos(self.pandaHandle)

			linesegs = LineSegs("lines")
			linesegs.setColor(1,1,1,1) 
			 
			linesegs.drawTo(point) 
			linesegs.drawTo(self.pandaHandle.getPos()) 
			 
			node = linesegs.create(False)  
			game.render.attachNewNode(node)