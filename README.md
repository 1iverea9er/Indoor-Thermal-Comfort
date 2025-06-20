# Indoor Thermal Comfort Tool for Home Assistant

This is a custom [Home Assistant](https://www.home-assistant.io/) HACS integration that provides calculated thermal comfort indicators using the [CBE Comfort Tool](https://comfort.cbe.berkeley.edu/) logic and implements the provisions of ANSI/ASHRAE Standard 55-2023.

This integration is a Python reimplementation based on the original JavaScript version by the [Center for the Built Environment](https://github.com/CenterForTheBuiltEnvironment/comfort_tool).  
The original project is licensed under the GNU GPLv2 license, and this adaptation is licensed under the same terms. See the [LICENSE](LICENSE) file for details.

---

## 🧊 Features

This integration calculates and provides the following thermal comfort metrics as sensors:

- **PMV** (Predicted Mean Vote)
- **PPD** (Predicted Percentage of Dissatisfied)
- **SET** (Standard Effective Temperature)
- **CE** (Cooling Effect)
- **Thermal Sensation** (qualitative value)

---

## ⚙️ Configuration

This integration requires the following existing entities to work:

### Input Parameters (Sensors / Input Numbers):

| Parameter | Description                                                | Recommended Range                                       | Required / Optional            |
| --------- | ---------------------------------------------------------- | ----------------------------------------------------------------- | ------------------------------ |
| `ta`      | Average air temperature (°C)                                       | **10 – 40 °C**                                                    | Required                       |
| `rh`      | Relative humidity (%)                                      | **10 – 90%**                                                      | Required                       |
| `clo`     | Clothing insulation (clo)  *(see ASHRAE 55 Table 5-2 or Table C.1-C.3 ISO 7730)* | **0.0 – 1.5 clo**                                                 | Required                       |
| `met`     | Metabolic rate (met) *(see ASHRAE 55 Table 5-1 or Table B.1 ISO 7730)*       | **0.8 – 2.0 met**                                                 | Required                       |
| `tr`      | Mean radiant temperature (°C)                              | Typically **10 – 40 °C**                                          | Optional *(defaults to `ta`)*  |
| `va`      | Air velocity (m/s)                                         | **0.0 – 2.0 m/s** *(up to 3.0 m/s with elevated airspeed limits)* | Optional *(defaults to `0.0`)* |


You will select these entities via the UI during setup.

### 🛠️ Advanced Configuration
To improve the accuracy of thermal comfort calculations (such as PMV or SET), it is important to correctly define environmental input parameters beyond just basic room temperature. Two key parameters often require special consideration:

🌡️ ta – Average Air Temperature
ta represents the average air temperature in the occupant’s breathing or working zone. While it is sometimes approximated by a single room temperature sensor, in real environments it should reflect localized variations caused by HVAC systems, stratification, or airflow patterns.

For example:

In a room with an overhead air conditioner, the air temperature near the occupants' heads might be several degrees lower than the general room average.

Near ventilation diffusers, localized cooling or heating can significantly alter perceived comfort.

To improve precision, consider:

Averaging temperatures from multiple sensors positioned at occupant height (typically 1.1 m for seated persons).

Incorporating temperature bias in known affected zones (e.g., near windows or vents).

🌐 tr – Mean Radiant Temperature
tr is the mean radiant temperature, representing the average temperature of all surrounding surfaces "seen" by the occupant, weighted by their angle and distance. It plays a critical role in comfort, especially in:

Spaces with cold or warm walls or uninsulated windows

Rooms with significant solar radiation

☀️ If the occupant is exposed to direct sunlight through a window, tr should account for the increased radiant heat — not just the average temperature of room surfaces.

To estimate tr more accurately:

Use globe temperature sensors, or

Apply a weighted combination of wall/window temperatures and solar heat gain estimates.

---

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

1. Copy the contents of this repository into: `custom_components/`
2. Restart Home Assistant.
3. Add the integration via UI as described above.

---

## 🔍 Example Use Cases

- Use PMV and PPD in energy optimization automations.
- Display SET and Thermal Sensation on dashboards.
- Combine CE with cooling system logic.

---

## 🧪 Notes

- Internally uses a Python adaptation of the [comfort_tool](https://github.com/CenterForTheBuiltEnvironment/comfort_tool) model by the Center for the Built Environment (UC Berkeley).
- All sensors update automatically when any of the input values change.

---

## 🧾 License

This project is licensed under the GNU General Public License v2.0.  
See the [LICENSE](LICENSE) file for full license terms.

---

## 🙏 Acknowledgements

- [comfort_tool](https://github.com/CenterForTheBuiltEnvironment/comfort_tool) by the Center for the Built Environment (UC Berkeley)
- Home Assistant community and HACS maintainers
