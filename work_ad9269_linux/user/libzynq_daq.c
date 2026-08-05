#include "zynq_daq.h"
#include <fcntl.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <unistd.h>

int zynq_daq_open(void) { return open("/dev/zynq_daq", O_RDWR | O_CLOEXEC); }
int zynq_daq_start(int fd, __u32 rate_hz, __u32 threshold) { struct zynq_daq_config c={rate_hz,threshold}; return ioctl(fd,ZYNQ_DAQ_IOC_START,&c); }
int zynq_scope_start(int fd, const struct zynq_scope_config *config) { return ioctl(fd,ZYNQ_DAQ_IOC_SCOPE_START,config); }
int zynq_daq_stop(int fd) { return ioctl(fd,ZYNQ_DAQ_IOC_STOP); }
int zynq_daq_set_rate(int fd, __u32 v) { return ioctl(fd,ZYNQ_DAQ_IOC_SET_RATE,&v); }
int zynq_daq_set_threshold(int fd, __u32 v) { return ioctl(fd,ZYNQ_DAQ_IOC_SET_THRESH,&v); }
int zynq_daq_dequeue_frame(int fd, struct zynq_daq_frame *v) { return ioctl(fd,ZYNQ_DAQ_IOC_DEQUEUE,v); }
int zynq_daq_release_frame(int fd, __u32 v) { return ioctl(fd,ZYNQ_DAQ_IOC_RELEASE,&v); }
int zynq_daq_get_status(int fd, struct zynq_daq_status *v) { return ioctl(fd,ZYNQ_DAQ_IOC_GET_STATUS,v); }
void *zynq_daq_map_slot(int fd, __u32 slot) {
  __u32 mode = ZYNQ_DAQ_MODE_EVENT;
  size_t stride;
  if (ioctl(fd, ZYNQ_DAQ_IOC_GET_MODE, &mode))
    return MAP_FAILED;
  stride = mode == ZYNQ_DAQ_MODE_SCOPE ?
      ZYNQ_SCOPE_SLOT_BYTES : ZYNQ_DAQ_SLOT_BYTES;
  return mmap(0, stride, PROT_READ, MAP_SHARED, fd, (off_t)slot * stride);
}
