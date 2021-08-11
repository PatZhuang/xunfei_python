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
        """获取固定时长的输入音频

        Args:
            duration (int, optional): 音频输入时长，单位为毫秒. 不能小于 chunk. Defaults to 1000.

        Returns:
            bytes: raw 格式的输入音频
        """
        while self.istream.stopped:
            self.start()
            
        length = duration // 1000 * self.samplerate
        frames = []
        for _ in range(0, max(int(length / self.chunk), 1)):
            data, overflowed = self.istream.read(self.chunk)
            frames.append(data)
        
        return b''.join(frames)
    
    def get_record_audio_with_len(self, frame_len):
        """获取固定大小的音频片段，注意 16bit 的采样精度返回的数据长度为 2 倍

        Args:
            frame_len (int): 音频采样数

        Returns:
            bytes: raw 格式的输入音频
        """
        # 因为采样率是 16bit，所以返回的长度其实是 frame_len * 2
        return self.istream.read(frame_len)[0]
    
    def get_record_audio_with_vad(self, duration=10000, vad_bos=5000, vad_eos=2000, aggressiveness=3, filter_blank=True): 
        """获取音频，使用 vad 自动判断停止输入并截断

        Args:
            duration (int, optional): 最长输入音频时长，单位为毫秒. Defaults to 10000.
            vad_bos (int, optional): 允许的句首空白时长，单位为毫秒. Defaults to 5000.
            vad_eos (int, optional): 允许的句尾空白时长，单位为毫秒. Defaults to 2000.
            aggressiveness (int, optional): 过滤无声音频的强度，取值范围为整数 0～3. Defaults to 3.

        Returns:
            (bytes, bool): (raw 格式的输入音频, 是否有输入音频)
        """
        vad = webrtcvad.Vad(aggressiveness)
        bos_cnt = 0
        eos_cnt = 0
        frame_duration = 20
        frames = b''
        has_spoken = False
        
        for i in range(duration // frame_duration):
            time.sleep(0.02)
            frame = self.get_record_audio_with_len(frame_len=self.samplerate // 1000 * frame_duration)
            
            frames += frame
            if vad.is_speech(frame, self.samplerate):
                has_spoken = True
                eos_cnt = 0
            else:
                if not has_spoken:
                    bos_cnt += frame_duration
                else:
                    eos_cnt += frame_duration
            if bos_cnt >= vad_bos:
                # 如果是句首空白停止，返回空串
                frames = b''
                break
            elif eos_cnt >= vad_eos:
                # 如果是句尾空白停止，停止录音并返回
                if filter_blank:
                    # 过滤句首句尾空白
                    pre_blank_len = bos_cnt * self.samplerate // 1000
                    suf_blank_len = vad_eos * self.samplerate // 1000
                    if self.dtype == 'int16':
                        pre_blank_len *= 2
                        suf_blank_len *= 2
                    frames = frames[pre_blank_len:-suf_blank_len]
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
            # 只考虑采样为 16bit 或 8bit 的情况
            bytes = 2 if self.dtype == 'int16' else 1
            chunksize = min(len(buffer) - current_frame, frames * bytes)
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