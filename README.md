# Comfort Tool Sensors

Интеграция Home Assistant для расчета параметров микроклимата (PMV, PPD, SET, Cooling Effect, Sensation) с использованием библиотеки [comfort_tool](https://github.com/CenterForTheBuiltEnvironment/comfort_tool).

## Установка

1. Установите HACS, если он еще не установлен.
2. Добавьте этот репозиторий в HACS как пользовательский.
3. Установите интеграцию "Comfort Tool Sensors" через HACS.

## Настройка

После установки:

1. Перейдите в "Настройки" > "Устройства и службы".
2. Нажмите "Добавить интеграцию" и выберите "Comfort Tool Sensors".
3. Укажите:
   - Существующие сенсоры: температура воздуха (ta), радиационная температура (tr), скорость воздуха (va), влажность (rh).
   - `input_number` для одежды (clo) и метаболизма (met).

## Использование

После настройки будут доступны следующие сенсоры:
- PMV
- PPD
- SET
- Cooling Effect
- Sensation

## Лицензия

MIT
