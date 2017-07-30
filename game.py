from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import *
from direct.gui.OnscreenText import OnscreenText

from pyevolve import G1DList, GSimpleGA, Initializators, Mutators, Crossovers, Selectors

from panda import Panda
from carrot import Carrot
from spike import Spike

from random import randrange
import sys, uuid, os

class Game(ShowBase):
	"""
	Class in charge of encapsulating everything
	
	Attributes:
		executionId (str): A unique random string
	    actualFrameNumber (int): Frame counter
	    maxFramesPerGeneration (int): Maximum number of frames per generation
	    maxGenerations (int): Maximum number of generations before exiting
	    numNeurons (int): Number of weights of the network
	    pandaNumber (int): Number of pandas
	    spikeNumber (int): Number of spikes
	    carrotNumber (int): Number of carrots
	    gameHeight (int): Height of the world geometry OY plane
	    gameWidth (int): Width of the world geometry OX plane
	    statsFilename (str): Path to save statistics
	    bestGenomeGenes (list): List of the best weights of a population
	    bestGenomeScore (int): Best score of all individuals
	    ga (GSimpleGA): PyEvolve's Genetic Algorithm object
	    genome (G1DList): PyEvolve's individual container
	    
	"""
	def __init__(self):
		"""
		Initialize base subsystems and prepare for the 1st generation
		"""
		ShowBase.__init__(self)

		self.executionId = str(uuid.uuid4()).replace('-','')
		self.statsFilename = "./stats/" + self.executionId + ".txt"
		if not os.path.exists(os.path.dirname(self.statsFilename)):
			os.makedirs(os.path.dirname(self.statsFilename))

		self.__setUpWindow()
		self.__setUpConstants()

		self.actualFrameNumber = 0
		self.bestGenomeScore = 0
		self.bestGenomeGenes = []

		self.__setUpScene()
		self.__setUpGA()

		self.__generateSpikes()
		self.__generatePandas()
		self.__generateCarrots()
	
		self.taskMgr.add(Carrot.spinCarrots, "spinCarrots")
		self.taskMgr.add(self.__logicLoop, "logicLoop")

	def __setUpWindow(self):
		"""
		Configure window resolution
		"""
		props = WindowProperties() 
		props.setSize(1280, 720) 
		base.win.requestProperties(props)

	def __setUpConstants(self):
		"""
		Constants
		"""
		self.gameWidth = 164
		self.gameHeight = 164

		self.pandaNumber = 8
		self.carrotNumber = 16
		self.spikeNumber = 8
		self.numNeurons = 252

		self.maxFramesPerGeneration = 1024
		self.maxGenerations = 32

	def __setUpScene(self):
		"""
		Build the scene geometry, lights, UI text, camera and spike walls
		"""
		cm = CardMaker('card')
		cm.setFrame(-self.gameWidth/2,self.gameWidth/2,-self.gameHeight/2,self.gameHeight/2)
		cm.setUvRange((0, 0), (2, 2))
		card = self.render.attachNewNode(cm.generate())

		tex = self.loader.loadTexture('models/grass.jpg')
		card.setTexture(tex)
		card.lookAt(0, 0, -1)

		self.frameGenText = OnscreenText(align=TextNode.ALeft, text = '', pos = (-1.7, 0.9), scale = 0.1, fg = (1,1,1,1))
		self.currentGenText = OnscreenText(align=TextNode.ALeft, text = '', pos = (-1.7, 0.8), scale = 0.1, fg = (1,1,1,1))
		self.avgScoreText = OnscreenText(align=TextNode.ALeft, text = '', pos = (-1.7, 0.7), scale = 0.1, fg = (1,1,1,1))
	
		dlight = DirectionalLight('dlight')
		dlight.setColor(VBase4(1, 1, 1, 1))
		dlnp = self.render.attachNewNode(dlight)
		dlnp.lookAt(1,-1,-1)
		self.render.setLight(dlnp)

		dlight2 = DirectionalLight('dlight2')
		dlight2.setColor(VBase4(1, 1, 1, 1))
		dlnp2 = self.render.attachNewNode(dlight2)
		dlnp2.lookAt(-1,1,-1)
		self.render.setLight(dlnp2)

		alight = AmbientLight('alight')
		alight.setColor(VBase4(0.2, 0.2, 0.2, 1))
		alnp = self.render.attachNewNode(alight)
		self.render.setLight(alnp)

		for i in range(-self.gameWidth/2, self.gameWidth/2 + 1, 8):
			Spike(self, i, -self.gameHeight/2, 'wall')
			Spike(self, i, self.gameHeight/2, 'wall')
		for i in range(-self.gameHeight/2 + 8,self.gameHeight/2 + 1 - 8, 8):
			Spike(self, -self.gameWidth/2, i, 'wall')
			Spike(self, self.gameWidth/2, i, 'wall')

		self.disableMouse()
		self.camera.setPos(0, -100, 80)
		self.camera.lookAt(0, 0, 0)

	def __setUpGA(self):
		"""
		Configure and initialize the genetic algorithm engine
		"""
		self.genome = G1DList.G1DList(self.numNeurons)
		self.genome.setParams(rangemin=-3.0, rangemax=3.0)
		self.genome.initializator.set(Initializators.G1DListInitializatorReal)
		self.genome.mutator.set(Mutators.G1DListMutatorRealGaussian)
		self.genome.crossover.set(Crossovers.G1DListCrossoverTwoPoint)
		self.genome.evaluator.set(self.scoreEvalFunc)
		self.ga = GSimpleGA.GSimpleGA(self.genome)
		self.ga.setMutationRate(0.05)
		self.ga.selector.set(Selectors.GRouletteWheel)
		self.ga.setElitism(False)
		self.ga.setPopulationSize(self.pandaNumber)
		self.ga.initialize()

	def __generateSpikes(self):
		"""
		Generate randomly positioned normal spikes in a way that there is
		a minimum distance between them
		"""
		i = 0
		while i < self.spikeNumber:
			colisionDetected = False
			x = randrange(10 - self.gameWidth/2, -10 + self.gameWidth/2)
			y = randrange(10 - self.gameHeight/2, -10 + self.gameHeight/2)
			spikePoint = Point3(x, y, 0)

			for spike in Spike.spikeNormalList:
				point = spike.spikeHandle.getPos(self.render)
				dist = (point.getXy() - spikePoint.getXy()).lengthSquared()
				if dist < 100:
					colisionDetected = True
					break

			if colisionDetected:
				continue

			Spike(self, x, y)
			i += 1

	def __generatePandas(self):
		"""
		Generate randomly positioned pandas in a way that there is
		a minimum distance between them and the spikes
		"""
		i = 0
		while(i < self.pandaNumber):
			colisionDetected = False
			x = randrange(50 - self.gameWidth/2, -50 + self.gameWidth/2)
			y = randrange(50 - self.gameHeight/2, -50 + self.gameHeight/2)
			pandaPoint = Point3(x, y, 1.5)

			for panda in Panda.pandaList:
				point = panda.pandaHandle.getPos(self.render)
				dist = (point.getXy() - pandaPoint.getXy()).lengthSquared()
				if dist < 100:
					colisionDetected = True
					break
			if colisionDetected:
				continue

			for spike in Spike.spikeNormalList:
				point = spike.spikeHandle.getPos(self.render)
				dist = (point.getXy() - pandaPoint.getXy()).lengthSquared()
				if dist < 100:
					colisionDetected = True
					break
			if colisionDetected:
				continue

			self.ga.internalPop[i].setParams(pandaId = i)
			Panda(self, x, y, self.ga.internalPop[i])
			i += 1

	def __generateCarrots(self):
		"""
		Generate randomly positioned carrots in a way that there is
		a minimum distance between them, the spikes and the pandas
		"""
		for i in range(self.carrotNumber):
			c = Carrot(self, 0, 0)
			c.reposition(self, Panda.pandaList, Spike.spikeNormalList)

	def __goNextGen(self):
		"""
		Evolve the population one generation, clear the scene and generate it again
		in other random positions
		"""
		if self.bestGenomeScore < Panda.getBestPanda().carrotsEaten:
			self.bestGenomeScore = Panda.getBestPanda().carrotsEaten
			self.bestGenomeGenes = Panda.getBestPanda().brainWeights

		self.actualFrameNumber = 0
		self.ga.step()

		Spike.clearNormalSpikes()
		Panda.clearPandas(self)
		Carrot.clearCarrots(self)

		self.__generateSpikes()
		self.__generatePandas()
		self.__generateCarrots()

	def scoreEvalFunc(self, chromosome):
		"""
		PyEvolve's individual score evaluation function
		
		Args:
		    chromosome (G1DList): the genes of the individual
		
		Returns:
		    int: the score of the genes of that panda
		"""
		return Panda.getScoreById(chromosome.getParam("pandaId"))

	def __logicLoop(self, task):
		"""
		Main logic loop, if the actual frames > max frames go to next generation,
		save statistics to file, update the pandas and the UI text
		
		Args:
		    task (task): Panda3D requires this param
		
		Returns:
		    int: Task.cont to continue looping
		"""
		if self.__terminationCriteria():
			sys.exit()

		if self.actualFrameNumber > self.maxFramesPerGeneration or Panda.livingPandas == 0:
			if self.bestGenomeScore < Panda.getBestPanda().carrotsEaten:
				self.bestGenomeScore = Panda.getBestPanda().carrotsEaten
				self.bestGenomeGenes = Panda.getBestPanda().brainWeights

			if ((self.ga.getCurrentGeneration()+1) % 10) == 0:
				self.__saveBestGenomeToFile()

			self.__saveGenomeStatsToFile()
			self.__goNextGen()

		for panda in Panda.pandaList:
			panda.update(self, Carrot.carrotList, Spike.spikeList)

		self.__updateText()
		self.actualFrameNumber += 1
		return Task.cont

	def __terminationCriteria(self):
		"""
		This function is evaluated each frame, if we need to exit return True here
		
		Returns:
		    bool: True for exit, False to continue
		"""
		if self.ga.getCurrentGeneration() > self.maxGenerations:
			return True
		if (self.ga.getCurrentGeneration() > 20) and (Panda.getAvgScore() < 0.5) and (self.actualFrameNumber > self.maxFramesPerGeneration//2):
			return True
		return False

	def __updateText(self):
		"""
		Update UI text
		"""
		self.frameGenText.setText("Frame: " + str(self.actualFrameNumber) + " of " + str(self.maxFramesPerGeneration))
		self.currentGenText.setText("Generation: " + str(self.ga.getCurrentGeneration()))
		self.avgScoreText.setText("Average score: " + str(Panda.getAvgScore()))

	def __saveBestGenomeToFile(self):
		"""
		Save best current individual to a file
		"""
		fh = open("bestGenomes.txt", "a")
		fh.write(str(self.bestGenomeScore) + ";" + self.executionId + ".txt;" + str(self.bestGenomeGenes) + "\n")
		fh.close

	def __saveGenomeStatsToFile(self):
		"""
		Save the population to a file
		"""
		fh = open(self.statsFilename, "a")
		for panda in Panda.pandaList:
			fh.write(str(self.ga.getCurrentGeneration()) + ";" + str(panda.carrotsEaten) + ";" + str(panda.brainWeights) + "\n")
		fh.close

	def printDebugStuff(self):
		"""
		debug stuff
		"""
		print("Panda.livingPandas: " + str(Panda.livingPandas))
		print("Panda.pandaList: " + str(len(Panda.pandaList)))
		print("Carrot.carrotList: " + str(len(Carrot.carrotList)))
		print("Spike.spikeList: " + str(len(Spike.spikeList)))
		print("Spike.spikeNormalList: " + str(len(Spike.spikeNormalList)))
		print("Spike.spikeWallList: " + str(len(Spike.spikeWallList)))
		print("================================")