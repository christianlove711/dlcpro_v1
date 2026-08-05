#include "zynq_daq.h"
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

int main(void)
{
  struct zynq_scope_config cfg = {
    .rate_hz = 80000000,
    .decimation_log2 = 0,
    .trigger_mode = ZYNQ_SCOPE_TRIGGER_FREE,
    .trigger_channel = 0,
    .trigger_level = 0,
    .fps = 10,
  };
  struct zynq_daq_frame frame;
  int fd = zynq_daq_open();

  if (fd < 0 || zynq_scope_start(fd, &cfg))
    return 1;
  while (!zynq_daq_dequeue_frame(fd, &frame)) {
    const unsigned char *data = zynq_daq_map_slot(fd, frame.slot);
    uint32_t magic = 0;

    if (data == MAP_FAILED)
      break;
    memcpy(&magic, data, sizeof(magic));
    printf("scope seq=%u slot=%u bytes=%u stride=%u magic=%08x\n",
           frame.sequence, frame.slot, frame.length, frame.stride, magic);
    munmap((void *)data, frame.stride);
    if (zynq_daq_release_frame(fd, frame.slot))
      break;
  }
  zynq_daq_stop(fd);
  close(fd);
  return 0;
}
