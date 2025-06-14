# Indoor Thermal Comfort Tool for Home Assistant

This is a custom [Home Assistant](https://www.home-assistant.io/) HACS integration that provides calculated thermal comfort indicators using the [CBE Comfort Tool](https://comfort.cbe.berkeley.edu/) logic and implements the provisions of ANSI/ASHRAE Standard 55-2023.

## 🧊 Features

This integration calculates and provides the following thermal comfort metrics as sensors:

- **PMV** (Predicted Mean Vote)
- **PPD** (Predicted Percentage of Dissatisfied)
- **SET** (Standard Effective Temperature)
- **CE** (Cooling Effect)
- **Thermal Sensation** (qualitative value)

## ⚙️ Configuration

This integration requires the following existing entities to work:

### Minimal required Sensors / Input Numbers:

- `ta`: Air temperature (°C)
- `rh`: Relative humidity (%)
- `clo`: Clothing insulation level (clo)
- `met`: Metabolic rate (met)

### Optional Sensors:

- `tr`: Mean radiant temperature (°C)  
  *Defaults to `ta` (i.e. `ta`=`tr`=`to`) if not provided*
- `va`: Air velocity (m/s)  
  *Defaults to `0.0` m/s if not provided*

You will select these entities via the UI during setup.

## 📦 Installation

### Recommended: HACS

1. Go to HACS → Integrations → 3-dot menu → Custom repositories.
2. Add this repository URL:  
   `https://github.com/1iverea9er/ha-comfort-tool`  
   with category: *Integration*.
3. Install **Comfort Tool Sensors**.
4. Restart Home Assistant.
5. Add the integration via **Settings → Devices & Services → Add Integration** and search for **Indoor Thermal Comfort**.

### Manual Installation

1. Copy the contents of this repository into:
2. Restart Home Assistant.
3. Add the integration via UI as described above.

## 🔍 Example Use Cases

- Use PMV and PPD in energy optimization automations.
- Display SET and Thermal Sensation on dashboards.
- Combine CE with cooling system logic.

## 🧪 Notes

- Internally uses the [comfort_tool](https://github.com/CenterForTheBuiltEnvironment/comfort_tool) Python implementation by the Center for the Built Environment (UC Berkeley).
- All sensors update automatically when any of the input values change.

## 🧾 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for more information.

## 🙏 Acknowledgements

- [comfort_tool](https://github.com/CenterForTheBuiltEnvironment/comfort_tool) by CBE
- Home Assistant community and HACS maintainers
