#ifndef ZYNQ_DAQ_H
#define ZYNQ_DAQ_H

#include <linux/types.h>
#include <linux/ioctl.h>

#define ZYNQ_DAQ_FRAME_BYTES 8320U
#define ZYNQ_DAQ_SLOT_BYTES  12288U
#define ZYNQ_DAQ_RING_SLOTS  64U
#define ZYNQ_SCOPE_FRAME_BYTES 32832U
#define ZYNQ_SCOPE_SLOT_BYTES  36864U
#define ZYNQ_SCOPE_RING_SLOTS  16U
#define ZYNQ_DAQ_IOC_MAGIC 'Q'

enum zynq_daq_mode {
  ZYNQ_DAQ_MODE_SCOPE = 0,
  ZYNQ_DAQ_MODE_EVENT = 1,
};

enum zynq_scope_trigger {
  ZYNQ_SCOPE_TRIGGER_FREE = 0,
  ZYNQ_SCOPE_TRIGGER_RISING = 1,
  ZYNQ_SCOPE_TRIGGER_FALLING = 2,
};

struct zynq_daq_config {
  __u32 rate_hz;
  __u32 threshold; /* reserved; must remain zero */
};

struct zynq_scope_config {
  __u32 rate_hz;
  __u32 decimation_log2; /* 0..8 = 1..256 */
  __u32 trigger_mode;
  __u32 trigger_channel; /* 0=A, 1=B */
  __s32 trigger_level;   /* signed ADC code */
  __u32 fps;             /* 10 or 20 */
};

struct zynq_daq_frame {
  __u32 slot, length, sequence, flags;
  __u32 mode, stride, reserved[2];
  __u64 dma_addr;
};

struct zynq_daq_status {
  __u32 running, fifo_level, dma_errors, event_count, dropped_events;
  __u32 stream_id, measured_rate_hz, last_error, suppressed_events;
  __u32 event_path_enabled, mode, scope_frame_count, scope_dropped;
  __u32 scope_suppressed, scope_status, spi_id_grade, spi_error_detail;
  __u64 last_event_index;
};

#define ZYNQ_DAQ_IOC_START       _IOW(ZYNQ_DAQ_IOC_MAGIC, 0x01, struct zynq_daq_config)
#define ZYNQ_DAQ_IOC_STOP        _IO(ZYNQ_DAQ_IOC_MAGIC, 0x02)
#define ZYNQ_DAQ_IOC_SET_RATE    _IOW(ZYNQ_DAQ_IOC_MAGIC, 0x03, __u32)
#define ZYNQ_DAQ_IOC_SET_THRESH  _IOW(ZYNQ_DAQ_IOC_MAGIC, 0x04, __u32)
#define ZYNQ_DAQ_IOC_DEQUEUE     _IOR(ZYNQ_DAQ_IOC_MAGIC, 0x05, struct zynq_daq_frame)
#define ZYNQ_DAQ_IOC_RELEASE     _IOW(ZYNQ_DAQ_IOC_MAGIC, 0x06, __u32)
#define ZYNQ_DAQ_IOC_GET_STATUS  _IOR(ZYNQ_DAQ_IOC_MAGIC, 0x07, struct zynq_daq_status)
#define ZYNQ_DAQ_IOC_SCOPE_START _IOW(ZYNQ_DAQ_IOC_MAGIC, 0x08, struct zynq_scope_config)
#define ZYNQ_DAQ_IOC_GET_MODE    _IOR(ZYNQ_DAQ_IOC_MAGIC, 0x09, __u32)

int zynq_daq_open(void);
int zynq_daq_start(int fd, __u32 rate_hz, __u32 threshold);
int zynq_scope_start(int fd, const struct zynq_scope_config *config);
int zynq_daq_stop(int fd);
int zynq_daq_set_rate(int fd, __u32 rate_hz);
int zynq_daq_set_threshold(int fd, __u32 threshold);
int zynq_daq_dequeue_frame(int fd, struct zynq_daq_frame *frame);
int zynq_daq_release_frame(int fd, __u32 slot);
int zynq_daq_get_status(int fd, struct zynq_daq_status *status);
void *zynq_daq_map_slot(int fd, __u32 slot);
#endif
