Engineering materials
====

This repository contains engineering materials of a self-driven vehicle's model participating in the WRO Future Engineers competition in the season 2025.

## Content

* `t-photos` contains 2 photos of the team (an official one and one funny photo with all team members)
* `v-photos` contains 6 photos of the vehicle (from every side, from top and bottom)
* `video` contains the video.md file with the link to a video where driving demonstration exists
* `schemes` contains one or several schematic diagrams of the electromechanical components illustrating all the elements (electronic components and motors) used in the vehicle and how they connect to each other.
* `src` contains code of control software for all components which were programmed to participate in the competition
* `models` is for the files for models used by 3D printers, laser cutting machines and CNC machines to produce the vehicle elements. If there is nothing to add to this location, the directory can be removed.
* `other` is for other files which can be used to understand how to prepare the vehicle for the competition.

## Introduction

The code runs on 2 threads, one for the Computer Vision algorithm and one for the HC-SR04 Proximity Sensor. This was necessary in order for the proximity sensor to work properly as it captures data at a much slower rate. The webcam attached to the Raspberry Pi is responsible for capturing video to feed the CV detection algorithm. We use GitHub to upload the code to the Raspberry Pi by cloning a repository with the updated code. We made a quick script to clone by using a PAT.