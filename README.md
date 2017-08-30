# 3D Demonstration of Artificial Neural Networks with Genetic Algorithms

![](https://github.com/andres-zibula/project-images/blob/master/ann-ga-demo/ann-ga-demo.gif)

## Video demo

[Youtube](https://www.youtube.com/channel/UC5cOzH02FS-Nh_uCi_ihDUQ)

## Synopsis

The purpose of the following demonstration is to make an easy to understand application of Artificial Neural Networks and Genetic Algorithms.

The demonstration is about pandas that have to eat carrots in order to survive and avoid the spikes that kill them under the following rules:

1. Each panda has 100 life points
2. At each frame the life of a panda is reduced by 0.2 points
3. If a panda eats a carrot its life is increased by 30 points
4. If a panda touches a spike, or its health is reduced to 0, it dies

The spikes, the pandas and the carrots are all randomly placed, if a carrot is eaten it appears in another random position.

## How it works

Each panda has a Multilayer Perceptron consisting of 14 inputs, 2 hidden layers of 12 and 6 neurons respectively, and 2 outputs. All the layers are fully connected and the activation function is the hyperbolic tangent.

The weights of the net are generated using a Genetic Algorithm, the population is selected with the roulette wheel method and the crossover method is a two point list.

Each panda has a sight of range that is divided in 7 frustums, each frustum represents 2 inputs for the net, the first input is a normalized distance in the range of 0 and 1 between the panda and an object inside the frustum, and the second input depends on the type of object, -1 for a spike, 0 for nothing and 1 for carrot.

## Prerequisites

The following libraries are required:

- [Panda3D](https://github.com/panda3d/panda3d)
- [PyEvolve](https://github.com/perone/Pyevolve)
- [PyBrain](https://github.com/pybrain/pybrain)


In order to work properly a small change has to be made in PyEvolve:

1. In file GenomeBase.py
    1. In def copy(self, g):
        1. add the line
            1. g.internalParams = self.internalParams.copy()
        2. comment the line
            1. #g.internalParams = self.internalParams
2. In file GSimpleGA.py
    1. In def step(self):
        1. comment the lines
            1. #newPop.evaluate()
            2. #self.internalPop.sort()
        2. add the following line at the beginning of the function
            1. self.internalPop.evaluate()
            2. self.internalPop.sort()

## Art attributions

https://opengameart.org/content/spyke-trap-low-poly-updated

https://opengameart.org/content/simple-3d-carrot