from dataclasses import dataclass
from datetime import datetime

@dataclass
class ZTData:
    timestamp: datetime

    def pretty(self) -> str:
        return f"Sensorzeit: {self.timestamp.strftime('%d.%m.%Y %H:%M:%S')}"

def parse_ZT(s: str) -> ZTData:
    try:
        dt = datetime.strptime(s, "%d.%m.%y;%H:%M:%S")
        return ZTData(timestamp=dt)
    except Exception as e:
        raise ValueError(f"Ungültiges ZT-Format: {s}") from e



@dataclass
class DAData:
    temperature: float
    humidity: float
    wind_speed: float
    wind_direction: int

    def pretty(self) -> str:
        return (
            f"Temperatur: {self.temperature:.1f} °C\n"
            f"Feuchte: {self.humidity:.1f} %rF\n"
            f"Windgeschwindigkeit: {self.wind_speed:.1f} m/s\n"
            f"Windrichtung: {self.wind_direction}°"
        )

def parse_DA(s: str) -> DAData:
    try:
        parts = s.split(";")
        if len(parts) != 4:
            raise ValueError("DA muss 4 Felder enthalten")

        return DAData(
            temperature=float(parts[0]),
            humidity=float(parts[1]),
            wind_speed=float(parts[2]),
            wind_direction=int(parts[3])
        )
    except Exception as e:
        raise ValueError(f"Ungültiges DA-Format: {s}") from e



@dataclass
class DDData:
    inner_temp: float
    laser_driver_temp: int
    laser_current_mA: float
    regulation_voltage_mV: int
    optical_output_mV: int
    sensor_supply_V: float
    heater_glass_laser_mA: int
    heater_glass_receiver_mA: int
    outer_temp: float
    heater_supply_V: float
    heater_case_mA: int
    heater_head_mA: int
    heater_bow_mA: int

    def pretty(self) -> str:
        return (
            f"Innentemperatur: {self.inner_temp:.1f} °C\n"
            f"Laser-Treiber Temp: {self.laser_driver_temp} °C\n"
            f"Laserstrom: {self.laser_current_mA:.2f} mA\n"
            f"Regel-Istspannung: {self.regulation_voltage_mV} mV\n"
            f"Optischer Regelausgang: {self.optical_output_mV} mV\n"
            f"Sensorversorgung: {self.sensor_supply_V:.1f} V\n"
            f"Glasheizung Laser: {self.heater_glass_laser_mA} mA\n"
            f"Glasheizung Empfänger: {self.heater_glass_receiver_mA} mA\n"
            f"Außentemperatur: {self.outer_temp:.1f} °C\n"
            f"Heizungsversorgung: {self.heater_supply_V:.1f} V\n"
            f"Gehäuseheizung: {self.heater_case_mA} mA\n"
            f"Kopfheizung: {self.heater_head_mA} mA\n"
            f"Bügelheizung: {self.heater_bow_mA} mA"
        )

def parse_DD(s: str) -> DDData:
    try:
        parts = s.split(";")
        if len(parts) != 13:
            raise ValueError("DD muss 13 Felder enthalten")

        return DDData(
            inner_temp=float(parts[0]),
            laser_driver_temp=int(parts[1]),
            laser_current_mA=float(parts[2]) / 100,  # 1/100 mA
            regulation_voltage_mV=int(parts[3]),
            optical_output_mV=int(parts[4]),
            sensor_supply_V=float(parts[5]) / 10,    # 1/10 V
            heater_glass_laser_mA=int(parts[6]),
            heater_glass_receiver_mA=int(parts[7]),
            outer_temp=float(parts[8]),
            heater_supply_V=float(parts[9]) / 10,    # 1/10 V
            heater_case_mA=int(parts[10]),
            heater_head_mA=int(parts[11]),
            heater_bow_mA=int(parts[12])
        )
    except Exception as e:
        raise ValueError(f"Ungültiges DD-Format: {s}") from e


from dataclasses import dataclass

DX_DESCRIPTIONS = [
    "Laserstatus (1=aus, 0=an)",
    "Statisches Signal außerhalb Bereich (F)",
    "Lasertemperatur analog zu hoch (F)",
    "Lasertemperatur digital zu hoch (F)",
    "Laserstrom analog zu hoch (F)",
    "Laserstrom digital zu hoch (F)",
    "Sensorversorgung außerhalb Bereich (F)",
    "Strom Glasheizung Laserkopf (W)",
    "Strom Glasheizung Empfangskopf (W)",
    "Temperaturfühler (W)",
    "Heizungsversorgung außerhalb Bereich (W)",
    "Strom Gehäuseheizung (W)",
    "Strom Kopfheizung (W)",
    "Strom Bügelheizung (W)",
    "Regelausgang Laserleistung hoch (W)",
    "Reserve"
]

@dataclass
class DXData:
    flags: list[int]

    def pretty(self) -> str:
        lines = []
        for i, val in enumerate(self.flags):
            status = "OK" if val == 0 else "FEHLER/WARNUNG"
            lines.append(f"{i:02d}: {DX_DESCRIPTIONS[i]} → {status}")
        return "\n".join(lines)

def parse_DX(s: str) -> DXData:
    try:
        parts = s.split(";")
        if len(parts) != 16:
            raise ValueError("DX muss 16 Felder enthalten")

        flags = [int(p) for p in parts]
        return DXData(flags=flags)

    except Exception as e:
        raise ValueError(f"Ungültiges DX-Format: {s}") from e
