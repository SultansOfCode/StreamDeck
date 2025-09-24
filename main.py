# pyserial
# obs-websocket-py
# easygui
# https://github.com/Elektordi/obs-websocket-py
# https://github.com/obsproject/obs-websocket/blob/master/docs/generated/protocol.md#requests

from obswebsocket import obsws, requests
import easygui
import serial
import signal
import sys
import time
import winsound


WIDTH = 1920
HEIGHT = 1080

HALF_WIDTH = WIDTH * 0.5
HALF_HEIGHT = HEIGHT * 0.5

SPACING = 10

AUDIO_DESKTOP_NAME = "Desktop"
AUDIO_BGM_NAME = "BGM"
AUDIO_MICROPHONE_NAME = "Microphone"
VIDEO_WEBCAM_NAME = "Webcam Scene"
SCENE_AWAY_NAME = "Away"
ITEM_AWAY_MESSAGE_NAME = "Away Message"
SOUND_AWAY_START = "audio\\brazino.wav"
SOUND_AWAY_END = "audio\\pornhub.wav"
LIVEPIX_QRCODE_ITEM_NAME = "LivePix QR Code"

SCENE_NAMES = [
  "Minecraft",
  "Coding",
  "Only Webcam"
]

ENCODER_INPUT_NAME = [
  AUDIO_DESKTOP_NAME,
  AUDIO_BGM_NAME,
  AUDIO_MICROPHONE_NAME,
  None,
  None
]

BGM_VOLUME = -17
BGM_VOLUME_AWAY = -7

ctrl_c = False

away = False

client = None
s = None


def playSound(filename):
  winsound.PlaySound(filename, winsound.SND_FILENAME)


def setScenesItemVisible(source_name, visible):
  scenes = client.call(requests.GetSceneList())

  for scene in scenes.getScenes():
    scene_name = scene["sceneName"]

    item = client.call(requests.GetSceneItemId(sceneName=scene_name, sourceName=source_name))

    if not item.status:
      continue

    id = item.datain["sceneItemId"]

    client.call(requests.SetSceneItemEnabled(sceneName=scene_name, sceneItemId=id, sceneItemEnabled=visible))


def setAudioSourceMute(source, muted):
  client.call(requests.SetInputMute(inputName=source, inputMuted=muted))


def setDesktopMute(muted):
  setAudioSourceMute(AUDIO_DESKTOP_NAME, muted)


def setMicrophoneMute(muted):
  setAudioSourceMute(AUDIO_MICROPHONE_NAME, muted)


def setWebcamHide(hidden):
  setScenesItemVisible(VIDEO_WEBCAM_NAME, not hidden)


def toggleWebcamVisibility():
  scenes = client.call(requests.GetSceneList())
  visible = None

  for scene in scenes.getScenes():
    scene_name = scene["sceneName"]

    item = client.call(requests.GetSceneItemId(sceneName=scene_name, sourceName=VIDEO_WEBCAM_NAME))

    if not item.status:
      continue

    id = item.datain["sceneItemId"]

    if visible is None:
      visibility = client.call(requests.GetSceneItemEnabled(sceneName=scene_name, sceneItemId=id))

      if not visibility.status:
        continue

      visible = visibility.datain["sceneItemEnabled"]

    client.call(requests.SetSceneItemEnabled(sceneName=scene_name, sceneItemId=id, sceneItemEnabled=not visible))


def changeWebcamPosition():
  scenes = client.call(requests.GetSceneList())
  old_webcam_transform = None
  new_webcam_transform = None
  webcam_x = 0
  webcam_y = 0
  webcam_width = 320
  webcam_height = 240
  old_livepix_transform = None
  new_livepix_transform = None
  livepix_x = 0
  livepix_y = 0
  livepix_width = 240
  livepix_height = 256

  for scene in scenes.getScenes():
    scene_name = scene["sceneName"]

    webcam_item = client.call(requests.GetSceneItemId(sceneName=scene_name, sourceName=VIDEO_WEBCAM_NAME))

    if not webcam_item.status:
      continue

    webcam_id = webcam_item.datain["sceneItemId"]

    if old_webcam_transform is None:
      webcam_transform = client.call(requests.GetSceneItemTransform(sceneName=scene_name, sceneItemId=webcam_id))

      if not webcam_transform.status:
        continue

      old_webcam_transform = webcam_transform.datain["sceneItemTransform"]

      webcam_x = old_webcam_transform["positionX"]
      webcam_y = old_webcam_transform["positionY"]
      webcam_width = old_webcam_transform["width"] - old_webcam_transform["cropRight"]
      webcam_height = old_webcam_transform["height"] - old_webcam_transform["cropBottom"]

      if webcam_y < HALF_HEIGHT:
        if webcam_x < HALF_WIDTH:
          webcam_x = WIDTH - SPACING - webcam_width
          webcam_y = SPACING
        else:
          webcam_x = SPACING
          webcam_y = HEIGHT - SPACING - webcam_height
      else:
        if webcam_x < HALF_WIDTH:
          webcam_x = WIDTH - SPACING - webcam_width
          webcam_y = HEIGHT - SPACING - webcam_height
        else:
          webcam_x = SPACING
          webcam_y = SPACING

      new_webcam_transform = {
        "positionX": webcam_x,
        "positionY": webcam_y
      }

    if new_webcam_transform is not None:
      client.call(requests.SetSceneItemTransform(sceneName=scene_name, sceneItemId=webcam_id, sceneItemTransform=new_webcam_transform))

    livepix_item = client.call(requests.GetSceneItemId(sceneName=scene_name, sourceName=LIVEPIX_QRCODE_ITEM_NAME))

    if not livepix_item.status:
      continue

    livepix_id = livepix_item.datain["sceneItemId"]

    if old_livepix_transform is None:
      livepix_transform = client.call(requests.GetSceneItemTransform(sceneName=scene_name, sceneItemId=livepix_id))

      if not livepix_transform.status:
        continue

      old_livepix_transform = livepix_transform.datain["sceneItemTransform"]

      livepix_width = old_livepix_transform["width"]
      livepix_height = old_livepix_transform["height"]

      if webcam_y < HALF_HEIGHT or webcam_x < HALF_WIDTH:
        livepix_x = WIDTH - SPACING - livepix_width
        livepix_y = HEIGHT - SPACING - livepix_height
      else:
        livepix_x = WIDTH - SPACING - livepix_width
        livepix_y = HEIGHT - SPACING - webcam_height - SPACING - livepix_height

      new_livepix_transform = {
        "positionX": livepix_x,
        "positionY": livepix_y
      }

    if new_livepix_transform is not None:
      client.call(requests.SetSceneItemTransform(sceneName=scene_name, sceneItemId=livepix_id, sceneItemTransform=new_livepix_transform))


def setScene(scene_name):
  client.call(requests.SetCurrentProgramScene(sceneName=scene_name))


def setAwayMessage(message=None):
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
    "positionX": HALF_WIDTH - old_transform["width"] * 0.5,
    "positionY": HALF_HEIGHT - old_transform["height"] * 0.5
  }

  client.call(requests.SetSceneItemTransform(sceneName=SCENE_AWAY_NAME, sceneItemId=message_id, sceneItemTransform=new_transform))


def setAwayMessageVisible(visible):
  setScenesItemVisible(SCENE_AWAY_NAME, visible)


def setAway(enabled, message=None):
  away = enabled

  setDesktopMute(away)
  setMicrophoneMute(away)
  setWebcamHide(away)

  if away:
    setAwayMessage(message)

  setAwayMessageVisible(away)

  client.call(requests.SetInputVolume(inputName=AUDIO_BGM_NAME, inputVolumeDb=(BGM_VOLUME_AWAY if away else BGM_VOLUME)))

  if away:
    playSound(SOUND_AWAY_START)
  else:
    playSound(SOUND_AWAY_END)

  print("Away set to:", away, "-", message)


def handle_button(button, value):
  print("Button", button, "with value", value)

  if value == 1:
    if button < 5:
      input_name = ENCODER_INPUT_NAME[button]

      if input_name is not None:
        client.call(requests.ToggleInputMute(inputName=input_name))
    elif button == 5:
      setAudioSourceMute(AUDIO_BGM_NAME, True)

      setScene(SCENE_NAMES[0])
    elif button == 6:
      setAudioSourceMute(AUDIO_BGM_NAME, False)

      setScene(SCENE_NAMES[1])
    elif button == 7:
      setAudioSourceMute(AUDIO_BGM_NAME, False)

      setScene(SCENE_NAMES[2])
    elif button == 8:
      toggleWebcamVisibility()
    elif button == 9:
      changeWebcamPosition()
    elif button == 10:
      playSound("audio\\zedamanga.wav")
    elif button == 11:
      playSound("audio\\tiraqueeuvoucagar.wav")
    elif button == 12:
      playSound("audio\\brazino.wav")
    elif button == 13:
      playSound("audio\\pornhub.wav")
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
  print("Encoder", encoder, "with value", value)

  if value == 0:
    return

  input_name = ENCODER_INPUT_NAME[encoder]

  if input_name is None:
    return

  info = client.call(requests.GetInputVolume(inputName=input_name))

  if info.status:
    volume = info.datain["inputVolumeDb"] + value

    client.call(requests.SetInputVolume(inputName=input_name, inputVolumeDb=volume))


def signal_handler(sig, frame):
  global ctrl_c

  print("CTRL + C")

  ctrl_c = True


def main():
  signal.signal(signal.SIGINT, signal_handler)

  print("Conectado!")

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

    if ctrl_c:
      break

if __name__ == "__main__":
  while True:
    try:
      client = obsws("localhost", 4455)
      client.connect()

      s = serial.Serial("COM5", timeout=0.1)

      main()
    except:
      print("MIJO")
      pass

    if ctrl_c:
      break
