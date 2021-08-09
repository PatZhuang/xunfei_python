# 状态值

# ret code
MSP_SUCCESS             = 0 # 通用成功标记

# IVW
MSP_IVW_MSG_WAKEUP      = 1 # 唤醒
MSP_IVW_MSG_ERROR       = 2 # 出错
MSP_IVW_MSG_ISR_RESULT  = 3 # 唤醒+识别
MSP_IVW_MSG_ISR_EPS     = 4 # 唤醒+识别结果中 vad 端点检测消息
MSP_IVW_MSG_VOLUME      = 5
MSP_IVW_MSG_ENROLL      = 6
MSP_IVW_MSG_RESET       = 7

# RSLT status
MSP_REC_STATUS_SUCCESS              = 0 # 识别成功，此时用户可以调用QISRGetResult来获取（部分）结果。
MSP_REC_STATUS_NO_MATCH             = 1 # 识别结束，没有识别结果。
MSP_REC_STATUS_INCOMPLETE			= 2 # 正在识别中。
MSP_REC_STATUS_NON_SPEECH_DETECTED  = 3 # discard status, no more in use
MSP_REC_STATUS_SPEECH_DETECTED      = 4 # recognizer has detected audio, this is delayed status
MSP_REC_STATUS_COMPLETE				= 5 # 识别结束。
MSP_REC_STATUS_MAX_CPU_TIME         = 6 # CPU time limit exceeded
MSP_REC_STATUS_MAX_SPEECH           = 7 # maximum speech length exceeded, partial results may be returned
MSP_REC_STATUS_STOPPED              = 8 # recognition was stopped
MSP_REC_STATUS_REJECTED             = 9 # recognizer rejected due to low confidence
MSP_REC_STATUS_NO_SPEECH_FOUND      = 10    # recognizer still found no audio, this is delayed status

# EP status
MSP_EP_LOOKING_FOR_SPEECH   = 0 	# 还没有检测到音频的前端点。
MSP_EP_IN_SPEECH            = 1 	# 已经检测到了音频前端点，正在进行正常的音频处理。
MSP_EP_AFTER_SPEECH         = 3 	# 检测到音频的后端点，后继的音频会被MSC忽略。
MSP_EP_TIMEOUT              = 4 	# 超时。
MSP_EP_ERROR                = 5 	# 出现错误。
MSP_EP_MAX_SPEECH           = 6 	# 音频过大。
MSP_EP_IDLE                 = 7     # internal state after stop and before start

# TTS status
MSP_TTS_FLAG_STILL_HAVE_DATA    = 1 	# 音频还没取完，还有后继的音频
MSP_TTS_FLAG_DATA_END           = 2 	# 音频已经取完
MSP_TTS_FLAG_CMD_CANCELED       = 4
 
# Audio Sample status
MSP_AUDIO_SAMPLE_INIT           = 0x00
MSP_AUDIO_SAMPLE_FIRST          = 0x01
MSP_AUDIO_SAMPLE_CONTINUE       = 0x02
MSP_AUDIO_SAMPLE_LAST           = 0x04