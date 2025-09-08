import random

import matplotlib.pyplot as plt

from matplotlib.container import BarContainer

from threading import Event, Thread
from typing import cast, IO

from tqdm import trange

from traci.exceptions import TraCIException

from lib.colors import WHITE
from lib.vehicle_controller import VehicleController
from lib.start_traci import start, traci


def listen_warnings(pipe: IO[bytes], stop_event: Event):
    global num_collisions

    num_collisions = 0

    while not stop_event.is_set():
        if b'collision' in pipe.readline():
            num_collisions += 1

    pipe.close()


def plot(collisions: list[int], output_file: str = ''):
    _, _, bars = plt.hist(collisions, align='left', bins=range(7), rwidth=0.8)
    bars = cast(BarContainer, bars)
    plt.title('Number of collisions across simulations')
    plt.xlabel('Number of collisions')
    plt.ylabel('Frequency')
    plt.tight_layout()

    for bar in bars:
        if (height := bar.get_height()) > 0:
            plt.text(bar.get_x() + bar.get_width() / 2, height + 0.07, str(int(height)), fontsize=10, ha='center', va='bottom')

    if output_file:
        plt.savefig(output_file, format=output_file.split('.')[-1])

    plt.show()


def rand_position_phantom_vehicle(a: float = 5, b: float = 95) -> float:          return random.randint(int(a * 100), int(b * 100)) / 100
def rand_lane_id_route_id_phantom_vehicle() -> tuple[str, str]:                   return random.choice(edge_ids) + '_0', 'rphantom'
def rand_step_phantom_vehicle_appears(a: int = 50, b: int = 950) -> int:          return random.randint(a, b)
def rand_step_phantom_vehicle_disappears_offset(a: int = 10, b: int = 30) -> int: return random.randint(a, b)


def generate_random_phantom_vehicle() -> tuple[float, tuple[str, str], int, int]:
    return rand_position_phantom_vehicle(), rand_lane_id_route_id_phantom_vehicle(), rand_step_phantom_vehicle_appears(), rand_step_phantom_vehicle_disappears_offset()

def simulation(
    position_phantom_vehicle: float | None = None,
    lane_id_route_id_phantom_vehicle: tuple[str, str] | None = None,
    step_phantom_vehicle_appears: int | None = None,
    step_phantom_vehicle_disappears_offset: int | None = None,
    number_phantom_vehicles: int = 5,
    with_gui: bool = False,
):
    sumo_proc = start(CONFIG_FILE, '--seed', str(random.getrandbits(16)), *ARGS, with_gui=with_gui, delay=200)

    stop_event = Event()
    Thread(target=listen_warnings, args=(sumo_proc.stderr, stop_event), daemon=True).start()

    if number_phantom_vehicles == 1 and any((position_phantom_vehicle, lane_id_route_id_phantom_vehicle, step_phantom_vehicle_appears, step_phantom_vehicle_disappears_offset)):
        if position_phantom_vehicle is None:
            position_phantom_vehicle = rand_position_phantom_vehicle()
        if lane_id_route_id_phantom_vehicle is None:
            lane_id_route_id_phantom_vehicle = rand_lane_id_route_id_phantom_vehicle()
        if step_phantom_vehicle_appears is None:
            step_phantom_vehicle_appears = rand_step_phantom_vehicle_appears()
        if step_phantom_vehicle_disappears_offset is None:
            step_phantom_vehicle_disappears_offset = rand_step_phantom_vehicle_disappears_offset()

        lane_id_phantom_vehicle, route_id_phantom_vehicle = lane_id_route_id_phantom_vehicle
        step_phantom_vehicle_disappears = step_phantom_vehicle_appears + step_phantom_vehicle_disappears_offset
        phantom_vehicles_data = [(position_phantom_vehicle, lane_id_phantom_vehicle, route_id_phantom_vehicle, step_phantom_vehicle_appears, step_phantom_vehicle_disappears)]
    else:
        phantom_vehicles_data = []

        for _ in range(number_phantom_vehicles):
            position_phantom_vehicle, lane_id_route_id_phantom_vehicle, step_phantom_vehicle_appears, step_phantom_vehicle_disappears_offset = generate_random_phantom_vehicle()

            lane_id_phantom_vehicle, route_id_phantom_vehicle = lane_id_route_id_phantom_vehicle
            step_phantom_vehicle_disappears = step_phantom_vehicle_appears + step_phantom_vehicle_disappears_offset

            phantom_vehicles_data.append((position_phantom_vehicle, lane_id_phantom_vehicle, route_id_phantom_vehicle, step_phantom_vehicle_appears, step_phantom_vehicle_disappears))

    try:
        phantom_vehicles: list[VehicleController | None] = [None for _ in range(number_phantom_vehicles)]

        for step in range(SIMULATION_STEPS):
            traci.simulationStep()

            for i, (position_phantom_vehicle, lane_id_phantom_vehicle, route_id_phantom_vehicle, step_phantom_vehicle_appears, step_phantom_vehicle_disappears) in enumerate(phantom_vehicles_data):
                if step == step_phantom_vehicle_appears:
                    vc = phantom_vehicles[i] = VehicleController(f'phantom_vehicle_{i}', route_id=route_id_phantom_vehicle, color=WHITE)
                    vc.set_speed(0)
                    vc.move_to(lane_id_phantom_vehicle, position_phantom_vehicle)

                if step == step_phantom_vehicle_disappears:
                    cast(VehicleController, phantom_vehicles[i]).remove()
    except TraCIException:
        pass
    finally:
        stop_event.set()
        traci.close()


random.seed(0x5eed)
SIMULATION_STEPS = 1000
CONFIG_FILE = 'xml/osm/osm.sumocfg'
ARGS = ('--collision.action', 'warn', '--no-step-log')
edge_ids = '367876722#2 591363443 777327165 589941922 591363441#0 591363441#1 -367876722#2 -367876722#1 -367876722#0 -1219409110'.split()

collisions: list[int] = []
runs = 1000
number_phantom_vehicles = 5

for _ in trange(runs):
    simulation(number_phantom_vehicles=number_phantom_vehicles)
    collisions.append(num_collisions)

with open(f'txt/sim_c_{runs}_{number_phantom_vehicles}.txt', 'w') as f:
    f.write(str(collisions) + '\n')

plot(collisions, output_file=f'plots/plot_c_{runs}_{number_phantom_vehicles}.pdf')

# Test single simulation with GUI
# simulation(58, rand_lane_id_route_id_phantom_vehicle(), 77, 150, with_gui=True)
