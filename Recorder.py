import sounddevice as sd
import soundfile as sf

import threading

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
        # self.start()
        print("Recorder initialized")
    
    def start(self):
        self.istream.start()
        print("* start recording")
        
    def stop(self):
        self.istream.stop()
        print("* stop recording")
        
    def get_record_audio(self, duration=1):
        if self.istream.stopped:
            self.istream.start()
        length = duration * self.samplerate
        frames = []
        for _ in range(0, int(length / self.chunk)):
            data, overflowed = self.istream.read(self.chunk)
            frames.append(data)
        
        return b''.join(frames)
    
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