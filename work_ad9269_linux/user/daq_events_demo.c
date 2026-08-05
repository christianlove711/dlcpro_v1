#include "zynq_daq.h"
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>
int main(void) {
  int fd = zynq_daq_open(); struct zynq_daq_frame frame;
  struct zynq_daq_status status;
  /* A nonzero threshold returns EOPNOTSUPP in this fixed-RTL release. */
  if (fd < 0 || zynq_daq_start(fd, 20000000, 0)) return 1;
  while (!zynq_daq_dequeue_frame(fd, &frame)) {
    const unsigned char *data = zynq_daq_map_slot(fd, frame.slot);
    if (data == MAP_FAILED) break;
    uint32_t magic;
    memcpy(&magic, data, sizeof(magic));
    printf("event sequence=%u slot=%u bytes=%u magic=%08x\n",
           frame.sequence, frame.slot, frame.length, magic);
    munmap((void *)data, frame.stride);
    zynq_daq_release_frame(fd, frame.slot);
    if (!zynq_daq_get_status(fd, &status))
      printf("event-path=%s suppressed=%u dropped=%u dma-errors=%u\n",
             status.event_path_enabled ? "armed" : "disabled",
             status.suppressed_events, status.dropped_events,
             status.dma_errors);
  }
  zynq_daq_stop(fd); close(fd); return 0;
}
