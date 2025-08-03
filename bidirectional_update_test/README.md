

- initial kicad: manually created kicad project with just esp32-c6 and bulk cap
- step1: import from kicad to python
- step2: run python file and see that kicad files are generated which match the original project
- step3: edit the kicad files to connect the esp32 and capacitor to 3v3 and GND power symbols
- step4: re-import from kicad to python to see that the python logic does not change
- step5: add resistor to kicad project, then re-import to python code to see that a single resistor is added (we should add comments to the python script so we can see that the update logic is not over-writing the comments)
- step6: add a capacitor to the python side and re-export to the kicad side. see that user edits on the kicad side are not touched and only a capacitor is added
- step7: add voltage regulator circuit to kicad side, re-import to python and see that components and nets are added as appropriate
- step8: add usb-c subcircuit to python side, re-export and see that 



- stepX: move components from one shee to another, re-export, see that new sheets are made. user edits to original sheet should not be preserved


*** what if the user doesn't have the format we are expecting for the python project?  what if they put a few subcircuits in one filde, then a few subcircuits in another file?  not the 1 file 1 circuit logic we wanted?
- what are the possibilities and how can we accomodate them?