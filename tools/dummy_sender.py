import random
import time
from pylsl import StreamInfo, StreamOutlet, IRREGULAR_RATE


float_info = StreamInfo(
    name='DummyFloat',
    type='EEG',
    channel_count=8,
    nominal_srate=100,
    channel_format='float32',
    source_id='float123'
)
float_outlet = StreamOutlet(float_info)


int_info = StreamInfo(
    name='DummyInt',
    type='IntData',
    channel_count=4,
    nominal_srate=10,
    channel_format='int32',
    source_id='int123'
)
int_outlet = StreamOutlet(int_info)


str_info = StreamInfo(
    name='DummyStr',
    type='Markers',
    channel_count=1,
    nominal_srate=IRREGULAR_RATE,
    channel_format='string',
    source_id='str123'
)
str_outlet = StreamOutlet(str_info)

print("Streaming DummyFloat, DummyInt, DummyStr… (Ctrl-C to stop)")

start = time.time()
while True:
    
    float_sample = [random.random() for _ in range(8)]
    float_outlet.push_sample(float_sample)

    
    if int((time.time() - start) * 10) != int((time.time() - start - 0.01) * 10):
        int_sample = [random.randint(0, 100) for _ in range(4)]
        int_outlet.push_sample(int_sample)

    
    if int((time.time() - start) * 5) != int((time.time() - start - 0.01) * 5):
        label = random.choice(['ONSET', 'OFFSET', 'PING', 'PONG'])
        str_outlet.push_sample([f"{label}_{int((time.time()-start)*1000)}"])

    time.sleep(0.005)
