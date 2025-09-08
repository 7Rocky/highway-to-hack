import traci

from .colors import WHITE


class VehicleController:
    def __init__(
        self: 'VehicleController',
        veh_id: str,
        route_id: str = '',
        depart: str = 'now',
        type_id: str = 'DEFAULT_VEHTYPE',
        color: tuple[int, int, int] = WHITE,
        accel: float = 2.6,
        decel: float = 4.5,
        max_speed: float = 50,  # 180 km/h
        length: float = 5.0,
        automatic: bool = False
    ):
        self.veh_id = veh_id
        self.route_id = route_id
        self.depart = depart
        self.type_id = type_id

        traci.vehicletype.setAccel(type_id, accel)
        traci.vehicletype.setDecel(type_id, decel)
        traci.vehicletype.setMaxSpeed(type_id, max_speed)
        traci.vehicletype.setLength(type_id, length)

        self._add_to_simulation()

        self.set_automatic(automatic)
        traci.vehicle.setLaneChangeMode(veh_id, 0)
        traci.vehicle.setColor(veh_id, color)

    @property
    def acceleration(self: 'VehicleController') -> float:
        return traci.vehicle.getAcceleration(self.veh_id)  # type: ignore

    @property
    def position(self: 'VehicleController') -> tuple[float, float]:
        return traci.vehicle.getPosition(self.veh_id)  # type: ignore

    @property
    def speed(self: 'VehicleController') -> float:
        return traci.vehicle.getSpeed(self.veh_id)  # type: ignore

    def _add_to_simulation(self: 'VehicleController'):
        traci.vehicle.add(vehID=self.veh_id, routeID=self.route_id, typeID=self.type_id, depart=self.depart)

    def remove(self: 'VehicleController'):
        traci.vehicle.remove(self.veh_id)

    def set_acceleration(self: 'VehicleController', acceleration: float):
        traci.vehicle.setAcceleration(self.veh_id, acceleration, 1)  # type: ignore

    def set_color(self: 'VehicleController', color: tuple[int, int, int]):
        traci.vehicle.setColor(self.veh_id, color)

    def set_speed(self: 'VehicleController', speed: float):
        traci.vehicle.setSpeed(self.veh_id, speed)

    def set_automatic(self: 'VehicleController', automatic: bool):
        self.automatic = automatic
        traci.vehicle.setSpeedMode(self.veh_id, 0x1f if automatic else 0)

    def move_to(self: 'VehicleController', lane_id: str, pos: float):
        traci.vehicle.moveTo(self.veh_id, lane_id, pos)

    def is_in_simulation(self: 'VehicleController') -> bool:
        return self.veh_id in traci.vehicle.getIDList()

    def is_emergency(self: 'VehicleController') -> bool:
        return int(self.acceleration) <= -int(traci.vehicle.getEmergencyDecel(self.veh_id))  # type: ignore

    def __str__(self: 'VehicleController') -> str:
        return (f'id:            {self.veh_id}\n'
                f'position:      {self.position[0]:.2f}, {self.position[1]:.2f}\n'
                f'speed:         {self.speed:.2f} m/s\n'
                f'acceleration:  {self.acceleration:.2f} m/s²\n')
