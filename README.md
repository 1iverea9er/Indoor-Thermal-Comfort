# Indoor Thermal Comfort Tool for Home Assistant

A custom [Home Assistant](https://www.home-assistant.io/) HACS integration that provides calculated thermal comfort indicators using the [CBE Comfort Tool](https://comfort.cbe.berkeley.edu/) logic and implements the provisions of ANSI/ASHRAE Standard 55-2023.

---

## 🧊 Features

Calculates and provides the following thermal comfort metrics as sensors:

| Sensor | Description |
|--------|-------------|
| **PMV** | Predicted Mean Vote |
| **PPD** | Predicted Percentage of Dissatisfied |
| **SET** | Standard Effective Temperature |
| **CE** | Cooling Effect |
| **Thermal Sensation** | Qualitative comfort value |

**Optional solar radiation correction** adds two additional sensors when enabled:

| Sensor | Description |
|--------|-------------|
| **ERF** | Enhanced Radiant Field — additional radiant heat load from solar gain through glazing, W/m² |
| **ΔMrt Solar** | Solar correction to Mean Radiant Temperature, automatically applied to all comfort calculations |


---

## 📦 Installation

### Recommended: HACS

1. Go to HACS → Integrations → 3-dot menu → Custom repositories.
2. Add this repository URL:
   `https://github.com/1iverea9er/Indoor-Thermal-Comfort`
   with category: *Integration*.
3. Search and install **Indoor Thermal Comfort**.
4. Restart Home Assistant.
5. Add the integration via **Settings → Devices & Services → Add Integration** and search for **Indoor Thermal Comfort**.

### Manual Installation

1. Copy the contents of `custom_components/comfort_tool/` into your `config/custom_components/comfort_tool/`.
2. Restart Home Assistant.
3. Add the integration via UI as described above.

---

## ⚙️ Configuration

### Required and optional input parameters

| Parameter | Description | Recommended Range | Required |
|-----------|-------------|-------------------|----------|
| `ta` | Average air temperature | **10 – 40 °C / 50 – 104 °F** | ✅ Required |
| `rh` | Relative humidity (%) | **10 – 90 %** | ✅ Required |
| `clo` | Clothing insulation *(ASHRAE 55 Table 5-2, ISO 7730 Table C.1–C.3)* | **0.0 – 1.5 clo** | ✅ Required |
| `met` | Metabolic rate *(ASHRAE 55 Table 5-1, ISO 7730 Table B.1)* | **0.8 – 2.0 met** | ✅ Required |
| `tr` | Mean radiant temperature | Typically same range as `ta` | ☑️ Optional *(defaults to `ta`)* |
| `va` | Air velocity | **0.0 – 2.0 m/s** *(up to 3.0 m/s with elevated airspeed limits)* | ☑️ Optional *(defaults to 0.0)* |
| `direct_irradiance` | Direct solar beam intensity sensor (W/m²) | — | ☑️ Optional — enables solar correction |

All sensors accept any Home Assistant entity (`sensor.*`, `input_number.*`).

---

### 🚀 Quick Start

#### 1. Create helper `input_number` entities

```yaml
input_number:
  clo:
    name: Clothing insulation
    min: 0.0
    max: 1.5
    step: 0.01
    initial: 0.61

  met:
    name: Metabolic rate
    min: 0.8
    max: 2.0
    step: 0.01
    initial: 1.0
```

#### 2. Prepare temperature and humidity sensors

Assuming you already have:
- `sensor.temperature_room`
- `sensor.humidity_room`

#### 3. Select entities in the setup UI

| Field | Entity |
|-------|--------|
| ta | `sensor.temperature_room` |
| rh | `sensor.humidity_room` |
| clo | `input_number.clo` |
| met | `input_number.met` |
| tr | *(leave empty)* |
| va | *(leave empty)* |
| Direct solar beam intensity | *(leave empty to skip solar correction)* |

---

## ☀️ Solar Radiation Correction

When occupants are exposed to direct sunlight through a window, the standard Mean Radiant Temperature (`tr`) underestimates radiant heat load. The solar correction accounts for this using the **ERF methodology from ASHRAE 55-2023 Appendix C** and the CBE Comfort Tool.

### How to enable

In the setup form, select a sensor for **Direct solar beam intensity** (W/m²). This field is optional — leave it empty to skip solar correction and use the standard calculation.

### What happens when enabled

Six additional configuration entities appear in the device card under **Settings**:

| Entity | Description | Range |
|--------|-------------|-------|
| **Solar Azimuth** | Sun azimuth angle relative to the occupant's facing direction (°) | 0 – 360° |
| **Glazing Solar Transmittance (T_sol)** | Solar transmittance of the window glass | 0.0 – 1.0 |
| **Sky View Factor (f_svv)** | Fraction of the sky dome visible through the window from the occupant's position | 0.0 – 1.0 |
| **Body Exposed to Sun (f_bes)** | Fraction of the body surface directly exposed to sunlight | 0.0 – 1.0 |
| **Body SW Absorptivity (asa)** | Average shortwave absorptivity of the body and clothing surface *(ASHRAE 55 default: 0.7)* | 0.0 – 1.0 |
| **Occupant Posture** | Body posture affecting the projected area factor *fp* | Standing / Seated / Supine |

Solar altitude is read automatically from the built-in `sun.sun` entity — no additional configuration needed.

### What is calculated

- **ERF** (W/m²) — total additional radiant heat load from solar gain through glazing, per unit body surface area.
- **ΔMrt Solar** (°C / °F) — the equivalent MRT increase corresponding to ERF. Automatically added to `tr` before all comfort calculations (PMV, PPD, SET, CE).

### Parameter guidance

**T_sol** is the solar heat gain coefficient (SHGC) of the glazing. Typical values:
- Single clear glass: ~0.86
- Double low-e glass: ~0.35–0.55
- Triple glass: ~0.25–0.40

**f_svv** depends on window size and the occupant's distance and position relative to it. A full unobstructed window directly in front of the occupant ≈ 0.5. A small window at the side ≈ 0.05–0.15.

**f_bes** is 0 when the occupant is fully in shade, 1 when fully in the direct solar beam. For a typical seated office worker partially shaded by furniture: 0.2–0.5.

**Solar Azimuth** should be the angle between the sun's horizontal direction and the direction the occupant is facing — not the absolute compass azimuth. Use your sun position sensor and adjust for room orientation.

---

## 📝 Calibrating `clo` and `met`

`clo` and `met` should reflect **your personal comfort baseline**, not just theoretical table values.

**Goal:** adjust these parameters so that **PMV ≈ 0 when you actually feel comfortable**.

### Why this matters

The PMV/SET model is based on population averages. Real perception varies with individual sensitivity, climate adaptation, and personal preferences.

### How to calibrate

1. Wait until you feel genuinely comfortable in your environment.
2. Note the current conditions: temperature, humidity, airflow.
3. Adjust `clo` and/or `met` until PMV ≈ 0.

After calibration, PMV becomes personally meaningful and automations based on it become significantly more accurate.

---

## 🛠️ Advanced: improving `ta` and `tr` accuracy

### 🌡️ `ta` — Average Air Temperature

`ta` represents the air temperature in the occupant's breathing zone. In real environments it differs from a single room sensor due to HVAC stratification, diffuser proximity, and airflow patterns.

To improve precision:
- Average temperatures from multiple sensors at occupant height (typically 1.1 m for seated persons).
- Account for known temperature bias near windows, vents, or radiant panels.

### 🌐 `tr` — Mean Radiant Temperature

`tr` is the area-weighted average temperature of all surfaces surrounding the occupant. It dominates comfort in spaces with:
- Cold or warm walls and uninsulated windows
- Significant solar radiation

`tr` can be estimated as a weighted average of measured surface temperatures. When solar radiation is present and the **solar correction** is enabled, ΔMrt is added to `tr` automatically before all comfort calculations.

---

## 🔍 Example Use Cases

- Use **PMV** and **PPD** in energy optimization automations (e.g. adjust setpoint only when PMV drifts beyond ±0.5).
- Display **SET** and **Thermal Sensation** on dashboards for a human-readable comfort overview.
- Combine **CE** with cooling system logic.
- Use **ERF** and **ΔMrt Solar** to detect when solar gain requires shading or cooling compensation.
- Trigger blinds automation when **ΔMrt Solar** exceeds a threshold (e.g. > 3°C).

---

## 🚫 Limits of Applicability

ANSI/ASHRAE Standard 55 applies only to healthy individuals. It does **not** apply to occupants who:

- Wear clothing ensembles with insulation exceeding **1.5 clo**
- Wear highly impermeable clothing (e.g. protective suits)
- Are sleeping, reclining in contact with bedding, or able to adjust blankets

These exclusions exist because such conditions fall outside the steady-state thermal physiology assumptions of the PMV/SET model.

---

## 🧪 Under the Hood

- Python adaptation of the [CBE Comfort Tool](https://github.com/CenterForTheBuiltEnvironment/comfort_tool) model (UC Berkeley).
- Solar ERF and ΔMrt calculated per **ASHRAE 55-2023 Appendix C**, using bilinear interpolation of the projected area factor *fp* table for standing, seated, and supine postures.
- All sensors update immediately on any change to input entities via `async_track_state_change_event`.
- Solar configuration entities (`number.*`, `select.*`) are created automatically as part of the integration device and appear under **Settings** in the device card.

---

## 💬 Community Discussion

[Home Assistant Community Forum thread](https://community.home-assistant.io/t/indoor-thermal-comfort-tool/901623)

---

## 🧾 License

This integration is a Python reimplementation based on the original JavaScript version by the [Center for the Built Environment](https://github.com/CenterForTheBuiltEnvironment/comfort_tool).
The original project is licensed under the GNU GPLv2 license, and this adaptation is licensed under the same terms.
See the [LICENSE](LICENSE) file for full license terms.

---

## 🙏 Acknowledgements

- [CBE Thermal Comfort Tool](https://cbe-berkeley.gitbook.io/thermal-comfort-tool/) maintainers
- Home Assistant community and HACS maintainers
