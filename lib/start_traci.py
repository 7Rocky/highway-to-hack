import os
import subprocess
import sys
import time

import traci


if 'SUMO_HOME' in os.environ:
    sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

STEP_DURATION = 0.1


def start(sumocfg: str, *args: str, with_gui: bool = True, delay: int = 1000, step_duration: float = STEP_DURATION) -> subprocess.Popen:
    sumo_process = subprocess.Popen([
        'sumo-gui' if with_gui else 'sumo',
        '-c', sumocfg,
        '--step-length', str(step_duration),
        '--delay', str(delay),
        '--lateral-resolution', '0.1',
        '--window-size', '920,1080',
        '--remote-port', '8813',
        '--start',
        '--quit-on-end',
        *args,
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    time.sleep(1)
    traci.init()

    if with_gui:
        traci.gui.setSchema("View #0", "real world")

    return sumo_process
