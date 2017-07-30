from direct.task import Task
from panda3d.core import Point3
from random import randrange

class Carrot(object):
	"""
	Class for manipulating the carrots
	
	Attributes:
	    carrotList (list): A list containing the carrots
	    carrotModel (GeomNode): Panda3D geometry node

	    carrotHandle (NodePath): Panda3D Node for the carrot
	    isActive (bool): True if the carrot is ready to be eaten
	    
	"""
	carrotList = []
	carrotModel = None

	def __init__(self, game, x, y):
		"""
		Initialize carrot
		
		Args:
		    game (Game): A reference to the Game object
		    x (int): x coordinate
		    y (int): y coordinate
		"""
		if not Carrot.carrotModel:
			Carrot.carrotModel = game.loader.loadModel("models/carrot")
			Carrot.carrotModel.setPos(0,0,0)

		self.isActive = True

		self.carrotHandle = game.render.attachNewNode("carrotHandle")
  		self.carrotHandle.setPos(x, y, 1.5)
		self.carrotHandle.setScale(8,8,8)
		self.carrotHandle.setHpr(0,45,0)
		#self.carrotHandle.showTightBounds()

		Carrot.carrotModel.instanceTo(self.carrotHandle)
		Carrot.carrotList.append(self)


	def __delete(self):
		"""
		remove the carrot from the list and free its memory
		"""
		Carrot.carrotList.remove(self)
		self.carrotHandle.removeNode()

	def reposition(self, game, pandas, spikes):
		"""
		Generate randomly positioned carrots in a way that there is
		a minimum distance between them, the spikes and the pandas
		
		Args:
		    game (Game): A reference to the Game object
		    pandas (list): List of pandas
		    spikes (list): List of spikes
		"""
		colisionDetected = True
		carrotPoint = None
		while(colisionDetected):
			colisionDetected = False
			x = randrange(50 - game.gameWidth/2, -50 + game.gameWidth/2)
			y = randrange(50 - game.gameHeight/2, -50 + game.gameHeight/2)
			carrotPoint = Point3(x, y, 1.5)

			for panda in pandas:
				if panda.isDying:
					continue
				
				point = panda.pandaHandle.getPos(game.render)
				dist = (point.getXy() - carrotPoint.getXy()).lengthSquared()
				if dist < 100:
					colisionDetected = True
					break
			if colisionDetected:
				continue

			for spike in spikes:
				point = spike.spikeHandle.getPos(game.render)
				dist = (point.getXy() - carrotPoint.getXy()).lengthSquared()
				if dist < 100:
					colisionDetected = True
					break
			if colisionDetected:
				continue

			for carrot in Carrot.carrotList:
				if not carrot.isActive:
					continue

				point = carrot.carrotHandle.getPos(game.render)
				dist = (point.getXy() - carrotPoint.getXy()).lengthSquared()
				if dist < 100:
					colisionDetected = True
					break

		self.carrotHandle.setPos(carrotPoint)
		self.isActive = True

	def goToHeaven(self, game, pandas, spikes):
		"""
		When the carrot is eaten this method is called, it shows an animation and then reposition it
		
		Args:
		    game (Game): A reference to the Game object
		    pandas (list): List of pandas
		    spikes (list): List of spikes
		
		Returns:
		    None: if the carrot is not active and this method is called
		"""
		if not self.isActive:
			return
		self.isActive = False
		pos = self.carrotHandle.getPos()
		goToHeavenInterval = self.carrotHandle.posInterval(2, Point3(pos.getX(), pos.getY(), 40))
		goToHeavenInterval.start()

		game.taskMgr.doMethodLater(2.5, self.reposition, 'reset carrot', extraArgs = [game, pandas, spikes])

	@staticmethod
	def spinCarrots(task):
		"""
		A visual effect for spining the carrots
		
		Args:
		    task (task): Panda3D requires this param
		
		Returns:
		    int: Task.cont to continue looping
		"""
		angleDegrees = task.time * 45.0

		for carrot in Carrot.carrotList:
			carrot.carrotHandle.setHpr(angleDegrees, 45, 0)
		return Task.cont

	@staticmethod
	def clearCarrots(game):
		"""
		Delete all carrots
		
		Args:
		    game (Game): A reference to the Game object
		"""
		game.taskMgr.remove('reset carrot')

		for carrot in Carrot.carrotList[:]:
			carrot.__delete()