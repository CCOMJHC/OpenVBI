
def to_temperature_kelvin(in_temp: float, unit: str):
    match unit:
        case 'K' | 'k':
            return in_temp
        case 'C' | 'c':
            return in_temp + 273.15
        case 'F' | 'f':
            return ( ((in_temp - 32.0) * 5.0) / 9.0 ) + 273.15
        case _:
            raise ValueError(f"Unknown temperature unit {unit}.")
