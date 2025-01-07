from machine import Pin
from rotary_irq_rp2 import RotaryIRQ

encoders = []
rows = []
cols = []

values = [0] * 5
statuses = [0] * 25

for i in range(5):
    encoder = RotaryIRQ(2 * i, 2 * i + 1, pull_up=True)
    row = Pin(10 + i, Pin.OUT)
    col = Pin(15 + i, Pin.IN, Pin.PULL_DOWN)

    encoder.reset()
    row.low()

    encoders.append(encoder)
    rows.append(row)
    cols.append(col)

while True:
    commands = []

    for j in range(5):
        encoder = encoders[j]
        value_old = values[j]
        value_new = encoder.value()

        if value_new != value_old:
            values[j] = value_new
            commands.append("E:{}:{}".format(j, value_new - value_old))

        row = rows[j]
        row.high()

        for i in range(5):
            index = j * 5 + i
            col = cols[i]
            status_old = statuses[index]
            status_new = col.value()

            if status_new != status_old:
                statuses[index] = status_new
                commands.append("B:{}:{}".format(index, status_new))

        row.low()

    if len(commands) > 0:
        print(",".join(commands))
