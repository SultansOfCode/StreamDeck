# pyserial
# obs-websocket-py
# https://github.com/Elektordi/obs-websocket-py
# https://github.com/obsproject/obs-websocket/blob/master/docs/generated/protocol.md#requests

from obswebsocket import obsws, requests
import easygui
import serial
import time
import winsound


AUDIO_DESKTOP_NAME = "Desktop"
AUDIO_BGM_NAME = "BGM"
AUDIO_MICROPHONE_NAME = "Microphone"
VIDEO_WEBCAM_NAME = "Webcam"
SCENE_AWAY_NAME = "Away"
ITEM_AWAY_MESSAGE_NAME = "Away Message"
SOUND_AWAY_START = "C:\\Users\\SultansOfCode\\Desktop\\perae.wav"
SOUND_AWAY_END = "C:\\Users\\SultansOfCode\\Desktop\\voltei.wav"


encoder_input_name = [
  AUDIO_DESKTOP_NAME,
  AUDIO_BGM_NAME,
  AUDIO_MICROPHONE_NAME,
  None,
  None
]

away = False


client = obsws("localhost", 4455)
client.connect()

s = serial.Serial("COM5")


def playSound(filename):
  winsound.PlaySound(filename, winsound.SND_FILENAME)


def setScenesItemVisible(source_name, visible):
  global client

  scenes = client.call(requests.GetSceneList())

  for scene in scenes.getScenes():
    scene_name = scene["sceneName"]

    item = client.call(requests.GetSceneItemId(sceneName=scene_name, sourceName=source_name))

    if item.status:
      id = item.datain["sceneItemId"]

      client.call(requests.SetSceneItemEnabled(sceneName=scene_name, sceneItemId=id, sceneItemEnabled=visible))


def setAudioSourceMute(source, muted):
  global client

  client.call(requests.SetInputMute(inputName=source, inputMuted=muted))


def setDesktopMute(muted):
  global AUDIO_DESKTOP_NAME

  setAudioSourceMute(AUDIO_DESKTOP_NAME, muted)


def setMicrophoneMute(muted):
  global AUDIO_MICROPHONE_NAME

  setAudioSourceMute(AUDIO_MICROPHONE_NAME, muted)


def setWebcamHide(hidden):
  global VIDEO_WEBCAM_NAME

  setScenesItemVisible(VIDEO_WEBCAM_NAME, not hidden)


def setAwayMessage(message=None):
  global client, SCENE_AWAY_NAME, ITEM_AWAY_MESSAGE_NAME

  client.call(requests.SetInputSettings(inputName=ITEM_AWAY_MESSAGE_NAME, inputSettings={ "text": message if message is not None else "Já volto" }))

  time.sleep(0.1)

  message_item = client.call(requests.GetSceneItemId(sceneName=SCENE_AWAY_NAME, sourceName=ITEM_AWAY_MESSAGE_NAME))

  if not message_item.status:
    return

  message_id = message_item.datain["sceneItemId"]

  message_transform = client.call(requests.GetSceneItemTransform(sceneName=SCENE_AWAY_NAME, sceneItemId=message_id))

  if not message_transform.status:
    return

  old_transform = message_transform.datain["sceneItemTransform"]
  new_transform = {
    "positionX": 960 - old_transform["width"] * 0.5,
    "positionY": 540 - old_transform["height"] * 0.5
  }

  client.call(requests.SetSceneItemTransform(sceneName=SCENE_AWAY_NAME, sceneItemId=message_id, sceneItemTransform=new_transform))


def setAwayMessageVisible(visible):
  global SCENE_AWAY_NAME

  setScenesItemVisible(SCENE_AWAY_NAME, visible)


def setAway(enabled, message=None):
  global client, away, AUDIO_BGM_NAME, SOUND_AWAY_START, SOUND_AWAY_END

  away = enabled

  setDesktopMute(away)
  setMicrophoneMute(away)
  setWebcamHide(away)

  if away:
    setAwayMessage(message)

  setAwayMessageVisible(away)

  info = client.call(requests.GetInputVolume(inputName=AUDIO_BGM_NAME))

  if info.status:
    volume = info.datain["inputVolumeDb"] + 10 * (1 if away else -1)

    client.call(requests.SetInputVolume(inputName=AUDIO_BGM_NAME, inputVolumeDb=volume))

  if away:
    playSound(SOUND_AWAY_START)
  else:
    playSound(SOUND_AWAY_END)

  print("Away set to:", away, "-", message)


def handle_button(button, value):
  global client, encoder_input_name, away, AUDIO_BGM_NAME

  print("Button", button, "with value", value)

  if value == 1:
    if button < 5:
      input_name = encoder_input_name[button]

      if input_name is not None:
        client.call(requests.ToggleInputMute(inputName=input_name))
    elif button == 5:
      setAudioSourceMute(AUDIO_BGM_NAME, True)

      client.call(requests.SetCurrentProgramScene(sceneName="Minecraft"))
    elif button == 6:
      setAudioSourceMute(AUDIO_BGM_NAME, False)

      client.call(requests.SetCurrentProgramScene(sceneName="Left Screen"))
    elif button == 7:
      setAudioSourceMute(AUDIO_BGM_NAME, False)

      client.call(requests.SetCurrentProgramScene(sceneName="Coding"))
    elif button == 10:
      playSound("C:\\Users\\SultansOfCode\\Desktop\\zedamanga.wav")
    elif button == 20:
      setAway(True, "Já volto")
    elif button == 21:
      setAway(True, "Mijar")
    elif button == 22:
      setAway(True, "Cingaro")
    elif button == 23:
      reason = easygui.enterbox("Motivo do away:")

      if reason is not None:
        setAway(True, reason)
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
