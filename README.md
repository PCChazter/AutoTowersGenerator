[![Github All Releases](https://img.shields.io/github/downloads/kartchnb/AutoTowersGenerator/total.svg)]()
# AutoTowersGenerator

### "I ... am rarely happier than when spending an entire day programming my computer to perform automatically a task that would otherwise take me a good ten seconds to do by hand." - Douglas Adams

This is a Cura plugin that automates the creation of 3D printer calibration towers.  It stems, ultimately, from my own laziness.

There are instructions all over explaining how to generate temperature towers and 5axes even created the incredibly useful "Calibration Shapes" plugin, which does most of the work for you - one click to create the tower model, another few clicks to add a temperature change script.  Viola!

And, yet, it was still too much work for me.  I wondered if it would be possible to automate the process even further.

So, I set out to learn how to write a Cura plugin to automate this entire process.  After many, many hours of effort learning, coding, debugging, pulling my hair out, and pestering experts online, my laziness has finally paid off!

## Usage
This plugin automates the generation of several types of calibration towers:
  
  - Fan Towers (varies the fan speed percentage)

  - Flow Towers (varies the flow rate)

  - Retraction Towers (varies the retraction distance or speed)

  - Speed Towers (varies the print, jerk, and several other speed parameters)

  - Temperature Towers (varies the hot end temperature)

Any of these towers can be generated by selecting a preset from the AutoTowersGenerator menu or choosing a custom tower (although this requires OpenSCAD to be installed).  There is no post-processing that needs to be done, as the plugin takes care of that.  Just generate, slice, and print!
Generating and printing a calibration tower is easy!  Simply select the tower you want from the AutoTowersGenerator menu, optionally enter parameters for a customized tower, slice, and print!

You can also print several types of bed level patterns that will be customized for your printer bed size. This can be a great way to ensure your printer bed is properly leveled and your first layer is adhering well.  You can find some good tips on how to best use these on this [Filament Friday Video](https://www.youtube.com/watch?v=_EfWVUJjBdA&ab_channel=CHEP).

## A couple of things to note:

 - Although this plugin can be used without having OpenSCAD installed, you'll get much more flexibility and power out of it if you do.  Download and install from [openscad.org](https://openscad.org/).

- There is no need to add a post-processing script after creating the tower.  The post-processing is automatically done for you!  

- The tower is generated based on your current layer height.  If the layer height is changed after a tower is created, it will automatically be removed from the scene.  It's easy to recreate it, though!

- The plugin attempts to automatically locate your OpenSCAD executable. If it fails to find it, try specifying the full path in the settings item under the AutoTowersGenerator plugin menu. 

- I owe a huge debt to 5axes and his [Calibration Shapes plugin](https://marketplace.ultimaker.com/app/cura/plugins/5axes/CalibrationShapes).  The post-processing code was adapted directly from his plugin and I learned a lot from reviewing his code.  If you haven't installed his plugin yet, stop reading and do so now.

- There have been a lot of questions about how to interpret the flow tower. My intention with this tower was for it to be used as a visual check of how well your flow settings are working. All3DP has a [good article](https://all3dp.com/2/extrusion-multiplier-cura-ways-to-improve-your-prints/) with some visual examples of what good and bad flow might look like. If you want a less subjective way to analyze your flow settings, you can measure the width of each section. By default, each section of the flow tower is 10 mm in size (width, depth, and height) and the holes are intended to be 5 mm in diameter. If your results differ, it may indicate problems with your flow settings.

- Although I've attempted to maintain compatibility with Cura versions older than 5.0, updates for this version have not been tested and may not work correctly. I strongly suggest upgrading your Cura version if you haven't yet.

- Finally, share and enjoy!
