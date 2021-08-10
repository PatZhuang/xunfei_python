import sounddevice as sd
import soundfile as sf

import threading
import webrtcvad
import time

class Recorder(object):
    
    def __init__(self, dtype='int16', channels=1, samplerate=16000, chunk=1024) -> None:
        super().__init__()
        
        self.dtype = dtype
        self.channels = channels
        self.samplerate = samplerate
        self.chunk = chunk
        
        self.play_event = threading.Event()
        
        self.istream = sd.RawInputStream(samplerate=self.samplerate, 
                                         blocksize=self.chunk,
                                         dtype=self.dtype,
                                         channels=self.channels,
                                         latency=0.1)
        print("Recorder initialized")
        self.start()
    
    def start(self):
        while self.istream.stopped:
            self.istream.start()
            time.sleep(0.1)
        print("* start recording")
        
    def stop(self):
        self.istream.stop()
        print("* stop recording")
        
    def get_record_audio(self, duration=1000):
        while self.istream.stopped:
            self.start()
            
        length = duration // 1000 * self.samplerate
        frames = []
        for _ in range(0, max(int(length / self.chunk), 1)):
            data, overflowed = self.istream.read(self.chunk)
            frames.append(data)
        
        return b''.join(frames)
    
    def get_record_audio_with_len(self, frame_len):
        # 因为采样率是 16bit，所以返回的长度其实是 frame_len * 2
        return self.istream.read(frame_len)[0]
    
    def get_record_audio_with_vad(self, duration=10000, vad_bos=5000, vad_eos=2000):
        vad = webrtcvad.Vad(3)
        frame_duration = 20
        frames = b''
        has_spoken = False
        
        for i in range(duration // frame_duration):
            time.sleep(0.02)
            frame = self.get_record_audio_with_len(frame_len=self.samplerate // 1000 * frame_duration)
            
            frames += frame
            if vad.is_speech(frame, self.samplerate):
                has_spoken = True
            else:
                if not has_spoken:
                    vad_bos -= frame_duration
                else:
                    vad_eos -= frame_duration
            if not vad_bos or not vad_eos:
                break
        return frames, has_spoken
    
    def play_file(self, filename):
        event = threading.Event()
        current_frame = 0
        data, fs = sf.read(filename, always_2d=True)

        def play_file_callback(outdata, frames, time, status):
            nonlocal current_frame
            if status:
                print("play file status: %d" % status)
            chunksize = min(len(data) - current_frame, frames)
            outdata[:chunksize] = data[current_frame:current_frame + chunksize]
            if chunksize < frames:
                outdata[chunksize:] = 0
                raise sd.CallbackStop()
            current_frame += chunksize
            
        ostream = sd.OutputStream(samplerate=fs, channels=data.shape[1],
                                    callback=play_file_callback, finished_callback=event.set)
        with ostream:
            event.wait()
        
    def play_buffer(self, buffer):
        event = threading.Event()
        
        current_frame = 0
        def play_buffer_callback(outdata, frames, time, status):
            nonlocal current_frame
            if status:
                print("play buffe status: %d" % status)
            # 这里 chunksize = frame * 2 是因为量化比特数是 2 字节
            chunksize = min(len(buffer) - current_frame, frames * 2)
            outdata[:chunksize] = buffer[current_frame:current_frame + chunksize]
            if chunksize < frames * 2:
                raise sd.CallbackStop()
            current_frame += chunksize
        
        ostream = sd.RawOutputStream(samplerate=self.samplerate, blocksize=self.chunk, 
                                     channels=self.channels, dtype=self.dtype,
                                    callback=play_buffer_callback, finished_callback=event.set)
        with ostream:
            event.wait()
        return 
        
        
    def __del__(self):
        self.istream.stop()
        self.istream.close()
        
        print("Recorder deleted")
        return

if __name__ == '__main__':
    r = Recorder()
    r.get_record_audio_with_vad(duration=5000)