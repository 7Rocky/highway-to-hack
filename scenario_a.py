import random

import matplotlib.pyplot as plt

from tqdm import trange

from lib.colors import CYAN, WHITE
from lib.start_traci import start, STEP_DURATION, traci
from lib.vehicle_controller import VehicleController


def plot(results: list[tuple[int, list[float]]], output_file: str = ''):
    for position_phantom_vehicle, speed_data in results:
        t = [step * STEP_DURATION for step in range(len(speed_data))]
        s_kmh = [s_ms * 3600 / 1000 for s_ms in speed_data]
        plt.plot(t, s_kmh, label=f'Phantom vehicle at {position_phantom_vehicle} m')

    plt.title('Victim vehicle (2) speed across phantom vehicle (1) positions')
    plt.xlabel('Time (s)')
    plt.ylabel('Speed (km/h)')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    if output_file:
        plt.savefig(output_file, format=output_file.split('.')[-1])

    plt.show()


def simulate(position_phantom_vehicle: int, step_phantom_vehicle_appears: int, step_phantom_vehicle_disappears: int, with_gui: bool = False) -> list[float]:
    sumo_proc = start(CONFIG_FILE, '--seed', str(random.getrandbits(16)), *ARGS, with_gui=with_gui)

    victim_vehicle = VehicleController('victim_vehicle', color=CYAN)
    speed_measurements = []

    for step in range(SIMULATION_STEPS):
        traci.simulationStep()

        if not victim_vehicle.is_in_simulation():
            break

        speed_measurements.append(victim_vehicle.speed)

        if step == step_phantom_vehicle_disappears:
            traci.vehicle.remove(phantom_vehicle.veh_id)

        if step == step_phantom_vehicle_appears:
            phantom_vehicle = VehicleController('phantom_vehicle', color=WHITE)
            phantom_vehicle.set_speed(0)
            phantom_vehicle.move_to('E0_0', position_phantom_vehicle)

    traci.close()
    sumo_proc.kill()
    sumo_proc.wait()

    return speed_measurements


random.seed(0x5eed)
SIMULATION_STEPS = 300
CONFIG_FILE = 'xml/highway/highway.sumocfg'
ARGS = ('--collision.action', 'warn', '--no-warnings', '--no-step-log')

step_phantom_vehicle_appears = 75
step_phantom_vehicle_disappears = 85

data = []

for position_phantom_vehicle in trange(60, 135, 15):
    speed_data = simulate(position_phantom_vehicle, step_phantom_vehicle_appears, step_phantom_vehicle_disappears)
    data.append((position_phantom_vehicle, speed_data))

plot(data, output_file='plots/plot_a.pdf')

# Test single simulation with GUI
# simulate(75, step_phantom_vehicle_appears, step_phantom_vehicle_disappears, with_gui=True)
