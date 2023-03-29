import os
import time
import wave
from playsound import playsound
import pyaudio
import textwrap
import google.cloud.texttospeech as tts
import openai
from api_key import open_ai_api_key
from context import system_message
from pynput.keyboard import Key, Listener

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/mamen/PycharmProjects/AI Assistant Kira/google_credentials.json"
prompts = []
start_recording = False
stop_recording = False
playing_response = False
stop_response = False


def on_press(key):
    global start_recording
    global playing_response
    global stop_response
    if key == Key.shift_r:
        start_recording = True
    elif key == Key.ctrl_r and playing_response:
        print("Stop response")
        stop_response = True
        playing_response = False


def on_release(key):
    if key == Key.shift_r:
        global stop_recording
        stop_recording = True
        global start_recording
        start_recording = False


def wrap_text(text):
    wrapper = textwrap.TextWrapper(width=140)
    return wrapper.wrap(text=text)


def record_audio(p):
    global stop_recording
    pass
    chunk = 1024  # Record in chunks of 1024 samples
    sample_format = pyaudio.paInt16  # 16 bits per sample
    channels = 2
    fs = 44100  # Record at 44100 samples per second

    playsound("audio/start_recording_sound.mp3")

    stream = p.open(format=sample_format,
                    channels=channels,
                    rate=fs,
                    frames_per_buffer=chunk,
                    input=True)

    frames = []  # Initialize array to store frames

    first = True

    while start_recording and not stop_recording:  # for i in range(0, int(fs / chunk * seconds)):
        if first:
            first = False
        data = stream.read(chunk)
        frames.append(data)

    # Stop and close the stream
    stop_recording = False
    stream.stop_stream()
    p.close(stream)
    stream.close()

    playsound("audio/stop_recording_sound.mp3")
    # Save the recorded data as a WAV file
    filename = "audio/user_input.wav"

    wf = wave.open(filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(sample_format))
    wf.setframerate(fs)
    wf.writeframes(b''.join(frames))
    wf.close()
    return filename


def send_request():
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        max_tokens=1000,
        messages=prompts
    )

    response = dict(completion.choices[0].message)
    prompts.append(response)

    return response.get("content")


def get_next_prompt(p):
    audio_path = record_audio(p)
    audio_file = open(audio_path, "rb")

    transcript = openai.Audio.transcribe("whisper-1", audio_file)

    print("User:", transcript.text)
    return transcript.text


def output_response(text, p):
    global playing_response
    text_to_wav("de-DE-Wavenet-F", text)
    playing_response = True

    wf = wave.open('audio/ki_output.wav', 'rb')

    # define callback
    def callback(in_data, frame_count, time_info, status):
        data = wf.readframes(frame_count)
        return (data, pyaudio.paContinue)

    # open stream using callback
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True,
                    stream_callback=callback)

    # start the stream
    stream.start_stream()

    global stop_response
    while stream.is_active():
        if stop_response:
            stream.stop_stream()
            stop_response = False
        time.sleep(0.1)

    # stop stream
    stream.stop_stream()
    stream.close()
    wf.close()

    playing_response = False
    playsound("audio/response_done.mp3")


def text_to_wav(voice_name: str, text: str):
    language_code = "-".join(voice_name.split("-")[:2])
    text_input = tts.SynthesisInput(text=text)
    voice_params = tts.VoiceSelectionParams(
        language_code=language_code, name=voice_name
    )
    audio_config = tts.AudioConfig(audio_encoding=tts.AudioEncoding.LINEAR16)

    client = tts.TextToSpeechClient()
    response = client.synthesize_speech(
        input=text_input,
        voice=voice_params,
        audio_config=audio_config,
    )

    filename = f"audio/ki_output.wav"
    with open(filename, "wb") as out:
        out.write(response.audio_content)


def main():
    openai.api_key = open_ai_api_key
    prompts.append({"role": "system", "content": system_message})
    p = pyaudio.PyAudio()  # Create an interface to PortAudio
    with Listener(on_press=on_press, on_release=on_release) as listener:
        while True:
            if start_recording:
                try:
                    next_prompt = get_next_prompt(p)
                except openai.error.InvalidRequestError:
                    playsound("audio/fail.wav")
                    playsound("audio/response_done.mp3")
                    continue
                if next_prompt == "beenden" or next_prompt == "Beenden" or next_prompt == "Beenden." or next_prompt == "beenden.":
                    return
                if "AUFNAHME ABBRECHEN" in next_prompt.upper():
                    playsound("audio/abort.wav")
                    playsound("audio/response_done.mp3")
                    continue
                prompts.append({"role": "user", "content": next_prompt})
                output_response(send_request(), p)
            else:
                time.sleep(0.5)
        listener.join()
    p.terminate()


if __name__ == '__main__':
    main()
    playsound("audio/beenden.wav")
    print(prompts)
    timecode = time.strftime("%Y%m%d-%H%M%S")
    with open(f"history/chat-{timecode}.txt", 'w') as f:
        for line in prompts:
            role = line.get("role")
            content = line.get("content")
            f.write(f"{role}:\n{content}\n\n\n")
