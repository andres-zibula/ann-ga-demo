from direct.actor.Actor import Actor

class Spike(object):
	"""
	Class for manipulating the spikes
	
	Attributes:
	    spikeActor (Actor): Panda3d Actor class
	    spikeList (list): A list containing all the spikes
	    spikeNormalList (list):  A list containing all the normal spikes
	    spikeWallList (list):  A list containing all the wall spikes


	    spikeHandle (NodePath): Panda3D Node for the spike
	    spikeType (str): 'normal' or 'wall'
	    
	"""
	spikeList = []
	spikeNormalList = []
	spikeWallList = []
	spikeActor = None

	def __init__(self, game, x, y, spikeType = 'normal'):
		"""
		Initialize
		
		Args:
		    game (Game): A reference to the Game object
		    x (int): x coordinate
		    y (int): y coordinate
		    spikeType (str, optional): 'normal' or 'wall'
		"""
		if not Spike.spikeActor:
			Spike.spikeActor = Actor("models/Spikes", {"Anim0": "models/Spikes-Anim0", "Anim1": "models/Spikes-Anim1"})
			Spike.spikeActor.setPos(0,0,0)
			Spike.spikeActor.setScale(3, 3, 4)
			Spike.spikeActor.play("Anim0")

		self.spikeHandle = game.render.attachNewNode("spikeHandle")
  		self.spikeHandle.setPos(x, y, -0.6)
		#self.spikeHandle.showTightBounds()

		self.spikeType = spikeType

		Spike.spikeActor.instanceTo(self.spikeHandle)
		Spike.spikeList.append(self)

		if spikeType == 'wall':
			Spike.spikeWallList.append(self)
		else:
			Spike.spikeNormalList.append(self)

	def __delete(self):
		"""
		remove the spike from the lists and free its memory
		"""
		Spike.spikeList.remove(self)

		if self.spikeType == 'normal':
			Spike.spikeNormalList.remove(self)
		elif self.spikeType == 'wall':
			Spike.spikeWallList.remove(self)

		self.spikeHandle.removeNode()

	@staticmethod
	def clearNormalSpikes():
		"""
		delete all spikes
		"""
		for spike in Spike.spikeNormalList[:]:
			spike.__delete()