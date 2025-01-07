# pyserial
# obs-websocket-py
# https://github.com/Elektordi/obs-websocket-py
# https://github.com/obsproject/obs-websocket/blob/master/docs/generated/protocol.md#requests

from obswebsocket import obsws, requests
import serial


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


def setAway(enabled):
  global client, away

  away = enabled

  client.call(requests.SetInputMute(inputName="Mic/Aux", inputMuted=away))

  scenes = client.call(requests.GetSceneList())

  if scenes.status:
    for scene in scenes.getScenes():
      scene_name = scene["sceneName"]
      webcam_item = client.call(requests.GetSceneItemId(sceneName=scene_name, sourceName="Webcam"))

      if webcam_item.status:
        webcam_id = webcam_item.datain["sceneItemId"]

        client.call(requests.SetSceneItemEnabled(sceneName=scene_name, sceneItemId=webcam_id, sceneItemEnabled=not away))

      away_item = client.call(requests.GetSceneItemId(sceneName=scene_name, sourceName="Away"))

      if away_item.status:
        away_id = away_item.datain["sceneItemId"]

        client.call(requests.SetSceneItemEnabled(sceneName=scene_name, sceneItemId=away_id, sceneItemEnabled=away))

  print("Away set to:", away)


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
    elif button == 24:
      setAway(not away)


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
  setAway(False)

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
