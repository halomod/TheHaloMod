"""
Created on Jun 18, 2013

@author: Steven
"""

with open("TheHaloMod/settings.py") as f:
    the_lines = f.readlines()
    for i, line in enumerate(the_lines):
        if line.startswith("DEBUG"):
            the_lines[i] = "DEBUG = False\n"

with open("TheHaloMod/settings.py", "w") as f:
    for line in the_lines:
        f.write(line)
