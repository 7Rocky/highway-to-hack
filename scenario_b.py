import random

import matplotlib.pyplot as plt

from lib.colors import CYAN, RED, WHITE
from lib.start_traci import start, STEP_DURATION, traci
from lib.vehicle_controller import VehicleController


def plot(trailing_vehicle_reaction: float, position_leading_vehicle: list[float], position_trailing_vehicle: list[float], output_file: str = ''):
    t = [step * STEP_DURATION for step in range(len(position_trailing_vehicle))]

    plt.plot(t, position_leading_vehicle, label='V2X-enabled vehicle (2)', color='blue')
    plt.plot(t, position_trailing_vehicle, label='Legacy vehicle (3)', color='red')

    plt.axvline(t[step_phantom_vehicle_appears], linestyle='--', label='Phantom vehicle (1) appears', color='black')
    plt.axvline(t[step_phantom_vehicle_appears] + trailing_vehicle_reaction, linestyle='--', label=f'Trailing vehicle (3) reacts ({trailing_vehicle_reaction:.1f} s)', color='red')

    plt.title('Measure emergency brake reaction')
    plt.xlabel('Time (s)')
    plt.ylabel('Position (m)')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    if output_file:
        plt.savefig(output_file, format=output_file.split('.')[-1])

    plt.show()


def simulation(step_trailing_vehicle_appears: int, step_trailing_vehicle_reaction: int, position_phantom_vehicle: int, step_phantom_vehicle_appears: int, step_phantom_vehicle_disappears: int, with_gui: bool = False) -> tuple[list[float], list[float]]:
    sumo_proc = start(CONFIG_FILE, '--seed', str(random.getrandbits(16)), *ARGS, with_gui=with_gui)

    position_leading_vehicle = []
    position_trailing_vehicle = []

    leading_vehicle = VehicleController('leading_vehicle', color=CYAN)

    for step in range(SIMULATION_STEPS):
        traci.simulationStep()

        if step == step_trailing_vehicle_appears:
            trailing_vehicle = VehicleController('trailing_vehicle', color=RED, automatic=False)

        if not leading_vehicle.is_in_simulation() or (step > step_trailing_vehicle_appears and not trailing_vehicle.is_in_simulation()):
            break

        if step_trailing_vehicle_appears <= step <= step_phantom_vehicle_appears and not trailing_vehicle.automatic:
            trailing_vehicle.set_speed(leading_vehicle.speed)

        if step == step_phantom_vehicle_disappears:
            traci.vehicle.remove(phantom_vehicle.veh_id)

        if step == step_trailing_vehicle_reaction:
            trailing_vehicle.set_automatic(True)

        if step == step_phantom_vehicle_appears:
            phantom_vehicle = VehicleController('phantom_vehicle', color=WHITE)
            phantom_vehicle.set_speed(0)
            phantom_vehicle.move_to('E0_0', position_phantom_vehicle)

        position_leading_vehicle.append(leading_vehicle.position[0])
        position_trailing_vehicle.append(0 if step <= step_trailing_vehicle_appears else trailing_vehicle.position[0])

    traci.close()
    sumo_proc.kill()
    sumo_proc.wait()

    return position_leading_vehicle, position_trailing_vehicle


random.seed(0x5eed)
SIMULATION_STEPS = 300
CONFIG_FILE = 'xml/highway/highway.sumocfg'
ARGS = ('--collision.action', 'warn', '--no-warnings', '--no-step-log')

step_trailing_vehicle_appears = 30
step_phantom_vehicle_appears = 100
step_phantom_vehicle_disappears = 115
position_phantom_vehicle = 150

data = []
reaction_time = 0.1

while reaction_time < 1.5:
    step_trailing_vehicle_reaction = step_phantom_vehicle_appears + int(reaction_time / STEP_DURATION)
    position_leading_vehicle, position_trailing_vehicle = simulation(step_trailing_vehicle_appears, step_trailing_vehicle_reaction, position_phantom_vehicle, step_phantom_vehicle_appears, step_phantom_vehicle_disappears)

    if position_leading_vehicle and position_trailing_vehicle:
        data.append((reaction_time, position_leading_vehicle, position_trailing_vehicle))

    reaction_time += 0.4

for trailing_vehicle_reaction, position_leading_vehicle, position_trailing_vehicle in data:
    plot(trailing_vehicle_reaction, position_leading_vehicle, position_trailing_vehicle, output_file=f'plots/plot_b_{trailing_vehicle_reaction}.pdf')

# Test single simulation with GUI
# simulation(step_trailing_vehicle_appears, step_phantom_vehicle_appears + int(0.1 / STEP_DURATION), position_phantom_vehicle, step_phantom_vehicle_appears, step_phantom_vehicle_disappears, with_gui=True)
# simulation(step_trailing_vehicle_appears, step_phantom_vehicle_appears + int(0.9 / STEP_DURATION), position_phantom_vehicle, step_phantom_vehicle_appears, step_phantom_vehicle_disappears, with_gui=True)
