# pyserial
# obs-websocket-py
# https://github.com/Elektordi/obs-websocket-py
# https://github.com/obsproject/obs-websocket/blob/master/docs/generated/protocol.md#requests

from obswebsocket import obsws, requests
import serial
import time


encoder_input_name = [
  "Áudio do desktop",
  "Mic/Aux",
  "Minecraft Audio",
  None,
  None
]

away = False


client = obsws("localhost", 4455)
client.connect()

s = serial.Serial("COM5")


def setScenesItemVisible(source_name, visible):
  global client

  scenes = client.call(requests.GetSceneList())

  for scene in scenes.getScenes():
    scene_name = scene["sceneName"]

    item = client.call(requests.GetSceneItemId(sceneName=scene_name, sourceName=source_name))

    if item.status:
      id = item.datain["sceneItemId"]

      client.call(requests.SetSceneItemEnabled(sceneName=scene_name, sceneItemId=id, sceneItemEnabled=visible))


def setMicrophoneMute(muted):
  global client

  client.call(requests.SetInputMute(inputName="Mic/Aux", inputMuted=muted))


def setWebcamVisible(visible):
  setScenesItemVisible("Webcam", visible)


def setAwayMessage(message=None):
  client.call(requests.SetInputSettings(inputName="Away Message", inputSettings={ "text": message if message is not None else "Já volto" }))

  time.sleep(0.1)

  message_item = client.call(requests.GetSceneItemId(sceneName="Away", sourceName="Away Message"))

  if not message_item.status:
    return

  message_id = message_item.datain["sceneItemId"]

  message_transform = client.call(requests.GetSceneItemTransform(sceneName="Away", sceneItemId=message_id))

  if not message_transform.status:
    return

  old_transform = message_transform.datain["sceneItemTransform"]
  new_transform = {
    "positionX": 960 - old_transform["width"] * 0.5,
    "positionY": 540 - old_transform["height"] * 0.5
  }

  client.call(requests.SetSceneItemTransform(sceneName="Away", sceneItemId=message_id, sceneItemTransform=new_transform))


def setAwayMessageVisible(visible):
  setScenesItemVisible("Away", visible)


def setAway(enabled, message=None):
  global client, away

  away = enabled

  setMicrophoneMute(away)
  setWebcamVisible(not away)

  if away:
    setAwayMessage(message)

  setAwayMessageVisible(away)

  print("Away set to:", away, "-", message)


def handle_button(button, value):
  global client, encoder_input_name, away

  print("Button", button, "with value", value)

  if value == 1:
    if button < 5:
      input_name = encoder_input_name[button]

      if input_name is not None:
        client.call(requests.ToggleInputMute(inputName=input_name))
    elif button == 5:
      client.call(requests.SetCurrentProgramScene(sceneName="Minecraft"))
    elif button == 6:
      client.call(requests.SetCurrentProgramScene(sceneName="Left Screen"))
    elif button == 7:
      client.call(requests.SetCurrentProgramScene(sceneName="Coding"))
    elif button == 20:
      setAway(True, "Já volto")
    elif button == 21:
      setAway(True, "Mijar")
    elif button == 22:
      setAway(True, "Cingaro")
    elif button == 24:
      setAway(False)


def handle_encoder(encoder, value):
  global client, encoder_input_name

  print("Encoder", encoder, "with value", value)

  if value == 0:
    return

  input_name = encoder_input_name[encoder]

  if input_name is None:
    return

  info = client.call(requests.GetInputVolume(inputName=input_name))
  if info.status:
    volume = info.datain["inputVolumeDb"] + value
    client.call(requests.SetInputVolume(inputName=input_name, inputVolumeDb=volume))


def main():
  while True:
    commands = s.readline().decode().strip().split(",")

    for command in commands:
      if len(command) == 0:
        continue

      arguments = command.split(":")

      if arguments[0] == "B" and len(arguments) == 3:
        handle_button(*map(int, arguments[1:]))
      elif arguments[0] == "E" and len(arguments) == 3:
        handle_encoder(*map(int, arguments[1:]))


if __name__ == "__main__":
  main()
